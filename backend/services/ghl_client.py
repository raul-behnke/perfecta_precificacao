# backend/services/ghl_client.py

import os
import json
import time
import requests
from typing import Optional
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# 1) Carregar o .env para que REFRESH_CLIENT_ID, REFRESH_CLIENT_SECRET, etc.
#    sejam populadas em os.environ antes de usarmos os.getenv(...) abaixo.
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()   # <<== Carrega automaticamente as variáveis definidas em backend/.env

# ------------------------------------------------------------
# Carrega as configurações base da API GoHighLevel
# ------------------------------------------------------------
API_BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"  # Versão usada nas chamadas

# Arquivos JSON de tokens e “installed locations”
AGENCY_TOKEN_FILE    = os.path.join(os.path.dirname(__file__), "..", "gohighlevel_token.json")
LOCATIONS_DATA_FILE  = os.path.join(os.path.dirname(__file__), "..", "installed_locations_data.json")

# Variáveis obrigatórias vindas do .env (agora já carregado acima)
AGENCY_COMPANY_ID     = os.getenv("AGENCY_COMPANY_ID", "").strip()
APP_ID                = os.getenv("APP_ID", "").strip()
REFRESH_CLIENT_ID     = os.getenv("REFRESH_CLIENT_ID", "").strip()
REFRESH_CLIENT_SECRET = os.getenv("REFRESH_CLIENT_SECRET", "").strip()


def _load_json(path: str) -> Optional[dict]:
    """Tenta ler um JSON de disco; devolve None se arquivo não existir ou for inválido."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"!!! [GHL] JSON inválido em: {path}")
        return None


def _save_json(path: str, data: dict) -> None:
    """Salva um dicionário como JSON em disco."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ------------------------------------------------------------
# 1) REFRESH DO TOKEN DA AGÊNCIA
# ------------------------------------------------------------
def refresh_agency_token() -> bool:
    """
    Usa o refresh_token armazenado em gohighlevel_token.json para obter novo access_token.
    Se bem-sucedido, sobrescreve o arquivo gohighlevel_token.json e retorna True.
    """
    print(">>> [GHL] Iniciando refresh do token da agência...")

    # Carrega o JSON atual (já deve existir com refresh_token válido)
    token_data = _load_json(AGENCY_TOKEN_FILE)
    if not token_data:
        print(f"!!! [GHL] ERRO: Arquivo '{AGENCY_TOKEN_FILE}' não encontrado ou inválido.")
        return False

    refresh_token = token_data.get("refresh_token")
    user_type     = token_data.get("userType")      # normalmente “Company”
    company_id    = token_data.get("companyId")     # já deve ser igual a AGENCY_COMPANY_ID

    if not refresh_token or not user_type or not company_id:
        print("!!! [GHL] ERRO: faltando 'refresh_token', 'userType' ou 'companyId' no JSON existente.")
        return False

    url = f"{API_BASE_URL}/oauth/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": REFRESH_CLIENT_ID,
        "client_secret": REFRESH_CLIENT_SECRET,
        "refresh_token": refresh_token,
        "user_type": user_type
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    try:
        resp = requests.post(url, data=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        novo = resp.json()

        # Garante que companyId e userType não sejam removidos
        novo["companyId"] = novo.get("companyId", company_id)
        novo["userType"]  = novo.get("userType", user_type)
        timestamp = int(time.time())
        novo["refreshed_at_unix_timestamp"] = timestamp
        novo["refreshed_at_readable"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        _save_json(AGENCY_TOKEN_FILE, novo)
        print(">>> [GHL] Novo token da agência recebido com sucesso.")
        return True

    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL][HTTP ERROR] {http_err} → Status: {resp.status_code}, Resposta: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado no refresh_agency_token: {e}")
        return False


# ------------------------------------------------------------
# 2) GET INSTALLED LOCATIONS
# ------------------------------------------------------------
def get_installed_locations() -> bool:
    """
    Faz GET em /oauth/installedLocations?isInstalled=true&companyId=...&appId=...
    e salva a lista de locations em installed_locations_data.json.
    """
    print("\n>>> [GHL] Buscando installed locations...")

    token_json = _load_json(AGENCY_TOKEN_FILE)
    if not token_json:
        print(f"!!! [GHL] ERRO: Não há gohighlevel_token.json válido em: {AGENCY_TOKEN_FILE}")
        return False

    access_token = token_json.get("access_token")
    if not access_token:
        print("!!! [GHL] ERRO: 'access_token' não encontrado no gohighlevel_token.json.")
        return False

    if not AGENCY_COMPANY_ID or not APP_ID:
        print("!!! [GHL] ERRO: variáveis AGENCY_COMPANY_ID ou APP_ID não definidas no .env.")
        return False

    url = f"{API_BASE_URL}/oauth/installedLocations"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Accept": "application/json"
    }
    params = {
        "isInstalled": "true",
        "companyId": AGENCY_COMPANY_ID,
        "appId": APP_ID
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # A resposta pode ser { "locations": [...] } ou uma lista direta
        if isinstance(data, dict) and "locations" in data:
            lista = data["locations"]
        elif isinstance(data, list):
            lista = data
        else:
            print("!!! [GHL] AVISO: Resposta inesperada de installedLocations; salvando raw.")
            lista = data

        # Salva no disco
        to_save = {"locations": lista} if isinstance(data, dict) else lista
        _save_json(LOCATIONS_DATA_FILE, to_save)
        print(f">>> [GHL] Encontradas {len(lista)} installedLocations e salvas em '{LOCATIONS_DATA_FILE}'.")
        return True

    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [GHL][HTTP ERROR] {http_err} → Status: {resp.status_code}, Resposta: {resp.text}")
        return False
    except Exception as e:
        print(f"!!! [GHL] Erro inesperado em get_installed_locations: {e}")
        return False


# ------------------------------------------------------------
# 3) GET LOCATION TOKEN PARA CADA LOCATION
# ------------------------------------------------------------
def manage_location_tokens() -> bool:
    """
    Para cada entry em installed_locations_data.json (lista ou dicionário),
    faz POST em /oauth/locationToken e anexa em cada objeto JSON o
    campo "location_specific_token_data", depois salva de volta no mesmo arquivo.
    """
    print("\n>>> [GHL] Iniciando gerenciamento de tokens de LOCATION...")

    token_json = _load_json(AGENCY_TOKEN_FILE)
    if not token_json:
        print(f"!!! [GHL] ERRO: Não há gohighlevel_token.json válido em: {AGENCY_TOKEN_FILE}")
        return False

    access_token = token_json.get("access_token")
    if not access_token:
        print("!!! [GHL] ERRO: 'access_token' não encontrado no gohighlevel_token.json.")
        return False

    raw = _load_json(LOCATIONS_DATA_FILE)
    if raw is None:
        print(f"!!! [GHL] ERRO: '{LOCATIONS_DATA_FILE}' inexistente ou inválido.")
        return False

    if isinstance(raw, dict) and "locations" in raw:
        lista = raw["locations"]
    elif isinstance(raw, list):
        lista = raw
    else:
        print(f"!!! [GHL] ERRO: Conteúdo inesperado em '{LOCATIONS_DATA_FILE}'.")
        return False

    url = f"{API_BASE_URL}/oauth/locationToken"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    for loc in lista:
        location_id = loc.get("_id") or loc.get("id")
        if not location_id:
            loc["location_specific_token_data"] = {"error": "Missing location ID"}
            continue

        print(f"\n--- [GHL] Solicitando token para Location ID: {location_id} ---")
        payload = {
            "companyId": AGENCY_COMPANY_ID,
            "locationId": location_id
        }

        try:
            resp = requests.post(url, data=payload, headers=headers, timeout=20)
            resp.raise_for_status()
            loc["location_specific_token_data"] = resp.json()
            print(f"    <- [GHL] Token para Location {location_id} obtido com sucesso.")
        except requests.exceptions.HTTPError as http_err:
            detalhe = None
            try:
                detalhe = resp.json()
            except:
                detalhe = resp.text
            loc["location_specific_token_data"] = {
                "error": str(http_err),
                "status_code": resp.status_code,
                "details": detalhe
            }
            print(f"    !!! [GHL][HTTP ERROR] {http_err} → Status: {resp.status_code}, Resposta: {detalhe}")
        except Exception as e:
            loc["location_specific_token_data"] = {"error": str(e)}
            print(f"    !!! [GHL] Erro inesperado para Location {location_id}: {e}")

    # Salva tudo de volta
    _save_json(LOCATIONS_DATA_FILE, lista)
    print(f"\n>>> [GHL] Todos os tokens de location foram processados e salvos em '{LOCATIONS_DATA_FILE}'.")
    return True
