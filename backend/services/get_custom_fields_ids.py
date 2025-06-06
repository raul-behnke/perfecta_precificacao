# backend/services/get_custom_fields_ids.py (VERSÃO CORRIGIDA)

import json
import os
import requests

# --- CONFIGURAÇÃO ---
LOCATION_ID = "vH3FikNOO9r4YkbIIiub"
LOCATIONS_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "installed_locations_data.json")

# ---------------------------------------------------------------------------
# LISTA DE CHAVES CORRIGIDA com base na saída do script de diagnóstico
# ---------------------------------------------------------------------------
CUSTOM_FIELD_KEYS = [
    # Removido "source", "city", "name", "assigned_to" pois parecem ser campos padrão, não customizados.
    # Se forem customizados, adicione a chave correta aqui.
    "contact.cpf_ou_cnpj",
    "contact.endereco_de_instalacao",
    "contact.fatura_de_energia",
    "contact.concessionaria_de_energia_local",
    "contact.consumo_medio_mensal",
    "contact.taxa_de_simultaneidade_",
    "contact.ndice_de_irradiao",
    "contact.taxa_de_desempenho_",
    "contact.potncia_dos_mdulos_w",
    "contact.potncia_do_sistema_kw",
    "contact.quantidade_de_mdulos",
    "contact.custo_unitrio_do_mdulo_r",
    "contact.quantidade_de_inversor",
    "contact.custo_unitrio_do_inversor_r",
    "contact.custo_de_estrutura_r",
    "contact.custo_de_cabos_e_componentes_r",
    "contact.custo_base_instalao_por_kw_r",
    "contact.percentual_de_custos_indiretos_",
    "contact.percentual_de_margem_de_lucro_",
    "contact.alquota_de_impostos_sobre_venda_",
    "contact.valor_adicional_r",
    "contact.forma_de_desconto",
    "contact.valor_do_desconto_se_aplicvel",
#    "contact.valor_da_proposta", # Parecia haver duas "Valor da Proposta"
    "contact.valor_da_proposta_r",
    "contact.observaes_da_proposta"
]
# ---------------------------------------------------------------------------

def load_location_token(file_path: str, location_id: str) -> str:
    """Carrega o 'access_token' específico para uma location do arquivo JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados de locations não encontrado: {file_path}. Execute o script 'update_all_tokens.py' primeiro.")
    with open(file_path, "r", encoding="utf-8") as f:
        locations_data = json.load(f)
    target_location = next((loc for loc in locations_data if loc.get("_id") == location_id or loc.get("id") == location_id), None)
    if not target_location:
        raise ValueError(f"Location com ID '{location_id}' não encontrada em {file_path}.")
    token_data = target_location.get("location_specific_token_data")
    if not token_data or "access_token" not in token_data:
        raise RuntimeError(f"Não foi possível encontrar 'access_token' para a Location {location_id}.")
    return token_data["access_token"]

def fetch_all_custom_fields(location_id: str, access_token: str) -> list:
    """Chama a API GET para listar todos os Custom Fields da Location."""
    base_url = "https://services.leadconnectorhq.com"
    endpoint = f"/locations/{location_id}/customFields"
    url = base_url + endpoint
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("customFields", [])
    except requests.exceptions.HTTPError as http_err:
        print(f"!!! [HTTP ERROR] {http_err} -> Status: {resp.status_code}, Resposta: {resp.text}")
        raise
    except Exception as e:
        print(f"!!! Erro inesperado ao buscar custom fields: {e}")
        raise

def map_keys_to_ids(all_fields: list, keys_to_find: list) -> dict:
    """Mapeia as 'keys' fornecidas para seus respectivos 'IDs'."""
    # A API retorna a chave com o prefixo 'contact.', então vamos usar 'fieldKey' diretamente
    id_map = {field.get("fieldKey"): field.get("id") for field in all_fields if field.get("fieldKey")}
    result_mapping = {}
    for key in keys_to_find:
        result_mapping[key] = id_map.get(key)
        if result_mapping[key] is None:
            print(f"  [AVISO] A key '{key}' não foi encontrada nos Custom Fields da sua conta.")
    return result_mapping

def main():
    """Função principal para orquestrar o processo."""
    print(">>> Iniciando busca por IDs de Custom Fields (com chaves corrigidas)...")
    try:
        access_token = load_location_token(LOCATIONS_DATA_FILE, LOCATION_ID)
        print(f"[INFO] Token de acesso para a Location '{LOCATION_ID}' carregado com sucesso.")
        print("[INFO] Buscando todos os Custom Fields via API...")
        all_fields = fetch_all_custom_fields(LOCATION_ID, access_token)
        print(f"[INFO] {len(all_fields)} campos encontrados no total.")
        print("[INFO] Mapeando as keys especificadas para seus IDs...")
        final_mapping = map_keys_to_ids(all_fields, CUSTOM_FIELD_KEYS)
        print("\n✅ [RESULTADO] Mapeamento de 'key' para 'fieldId':\n")
        print(json.dumps(final_mapping, indent=2, ensure_ascii=False))
        output_dir = os.path.dirname(__file__)
        output_file = os.path.join(output_dir, "custom_fields_ids.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_mapping, f, indent=4, ensure_ascii=False)
        print(f"\n✅ Arquivo de mapeamento foi salvo em: {output_file}")
    except (FileNotFoundError, ValueError, RuntimeError, requests.exceptions.RequestException) as e:
        print(f"\n❌ ERRO: Ocorreu um problema. {e}")
        print("   Por favor, verifique suas configurações e se o token é válido.")
        exit(1)

if __name__ == "__main__":
    main()