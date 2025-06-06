# backend/services/diagnose_pipelines.py (VERSÃO CORRIGIDA)

import json
import os
import requests
from typing import Dict

# --- CONFIGURAÇÃO ---
LOCATION_ID = "vH3FikNOO9r4YkbIIiub"

# --- Funções Auxiliares ---

def get_location_token() -> str:
    """Carrega o token de acesso específico para a location configurada."""
    locations_file = os.path.join(os.path.dirname(__file__), "..", "installed_locations_data.json")
    if not os.path.exists(locations_file):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {locations_file}. Execute 'update_all_tokens.py' primeiro.")

    with open(locations_file, "r", encoding="utf-8") as f:
        locations_data = json.load(f)

    target_location = next((loc for loc in locations_data if loc.get("_id") == LOCATION_ID or loc.get("id") == LOCATION_ID), None)

    if not target_location:
        raise ValueError(f"Location com ID '{LOCATION_ID}' não encontrada no arquivo de dados.")

    token_data = target_location.get("location_specific_token_data", {})
    access_token = token_data.get("access_token")

    if not access_token:
        raise RuntimeError(f"Token de acesso não encontrado para a Location {LOCATION_ID}.")

    return access_token

def fetch_pipelines_data(access_token: str, location_id: str) -> list: # <-- ALTERADO: recebe location_id
    """Busca os dados de todas as pipelines e seus stages via API."""
    base_url = "https://services.leadconnectorhq.com"
    url = f"{base_url}/opportunities/pipelines"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": "2021-07-28",
        "Accept": "application/json"
    }
    
    # Parâmetro de consulta exigido pela API
    params = {
        "locationId": location_id  # <-- ALTERADO: adiciona o parâmetro
    }
    
    print("Buscando dados das pipelines na API...")
    try:
        # Adiciona `params=params` à requisição
        resp = requests.get(url, headers=headers, params=params, timeout=30) # <-- ALTERADO
        resp.raise_for_status()
        data = resp.json()
        return data.get("pipelines", [])
    except requests.exceptions.RequestException as e:
        print(f"!!! ERRO ao chamar a API: {e}")
        # Tenta imprimir mais detalhes do erro, se disponíveis
        if e.response is not None:
            print(f"Detalhes: {e.response.text}")
        return []

def display_pipelines_info(pipelines: list):
    """Exibe as informações de pipelines e stages de forma organizada."""
    if not pipelines:
        print("\nNenhuma pipeline encontrada para esta location.")
        return

    print("\n✅ Pipelines e Stages encontrados:\n")
    for pipeline in pipelines:
        pipeline_name = pipeline.get('name', 'N/A')
        pipeline_id = pipeline.get('id', 'N/A')
        
        print("="*60)
        print(f"PIPELINE: {pipeline_name}")
        print(f"  ID: {pipeline_id}")
        print("="*60)
        
        stages = pipeline.get('stages', [])
        if not stages:
            print("  -> Esta pipeline não possui nenhuma etapa (stage).")
        else:
            print(f"  {'ETAPA (Stage)':<30} | {'STAGE ID'}")
            print(f"  {'-'*30} | {'-'*30}")
            for stage in stages:
                stage_name = stage.get('name', 'N/A')
                stage_id = stage.get('id', 'N/A')
                print(f"  {stage_name:<30} | {stage_id}")
        print("\n")

def main():
    """Função principal para orquestrar a busca e exibição."""
    try:
        token = get_location_token()
        # Passa o LOCATION_ID para a função de fetch
        pipelines = fetch_pipelines_data(token, LOCATION_ID) # <-- ALTERADO
        display_pipelines_info(pipelines)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"ERRO: {e}")

if __name__ == "__main__":
    main()