# backend/services/diagnose_fields.py

import json
import os
import requests

# --- CONFIGURAÇÃO ---
# Verifique se estes valores estão corretos
LOCATION_ID = "vH3FikNOO9r4YkbIIiub" # Substitua se for diferente
LOCATIONS_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "installed_locations_data.json")

def load_location_token(file_path: str, location_id: str) -> str:
    """Carrega o 'access_token' específico para uma location."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {file_path}. Execute 'update_all_tokens.py' primeiro.")

    with open(file_path, "r", encoding="utf-8") as f:
        locations_data = json.load(f)

    target_location = next((loc for loc in locations_data if loc.get("_id") == location_id or loc.get("id") == location_id), None)

    if not target_location:
        raise ValueError(f"Location com ID '{location_id}' não encontrada em {file_path}.")

    token_data = target_location.get("location_specific_token_data")
    if not token_data or "access_token" not in token_data:
        raise RuntimeError(f"Token não encontrado para a Location {location_id}.")

    return token_data["access_token"]

def diagnose_custom_fields(location_id: str, access_token: str):
    """Busca e exibe todos os campos personalizados da location."""
    base_url = "https://services.leadconnectorhq.com"
    url = f"{base_url}/locations/{location_id}/customFields"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    
    print(f"Buscando campos para a Location ID: {location_id}...")
    
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        custom_fields = data.get("customFields", [])
        
        if not custom_fields:
            print("\n❌ Nenhum campo personalizado foi encontrado nesta Location.")
            return

        print("\n✅ Campos Personalizados Encontrados:\n")
        print("-" * 60)
        print(f"{'NOME DO CAMPO':<40} | {'CHAVE (key)':<40}")
        print("-" * 60)
        
        for field in custom_fields:
            # O nome do campo pode estar em 'name' ou 'label'
            field_name = field.get('name', 'N/A')
            # A chave do campo geralmente está em 'fieldKey'
            field_key = field.get('fieldKey', 'N/A')
            print(f"{field_name:<40} | {field_key:<40}")
        
        print("-" * 60)
        print("\nCopie as chaves da coluna 'CHAVE (key)' e cole na lista 'CUSTOM_FIELD_KEYS' do script 'get_custom_fields_ids.py'.")

    except Exception as e:
        print(f"\n❌ Ocorreu um erro: {e}")

if __name__ == "__main__":
    try:
        token = load_location_token(LOCATIONS_DATA_FILE, LOCATION_ID)
        diagnose_custom_fields(LOCATION_ID, token)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERRO DE CONFIGURAÇÃO: {e}")