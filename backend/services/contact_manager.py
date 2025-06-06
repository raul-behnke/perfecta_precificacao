# backend/services/contact_manager.py

import requests
import json
from typing import Dict, Any

# Carregue o mapeamento de IDs que geramos anteriormente
try:
    with open("backend/services/custom_fields_ids.json", "r", encoding="utf-8") as f:
        CUSTOM_FIELD_IDS = json.load(f)
except FileNotFoundError:
    print("!!! ALERTA: Arquivo 'custom_fields_ids.json' não encontrado. As funções de custom field não funcionarão.")
    CUSTOM_FIELD_IDS = {}

# --- CONSTANTES ---
# Substitua estes valores pelos IDs corretos da sua conta GHL
PIPELINE_ID = "8pMqwP5PVLR5LoM87lx8"
PIPELINE_STAGE_ID = "6a4d8f9a-1aff-4bc3-8a3e-76714b7722a7"

API_BASE_URL = "https://services.leadconnectorhq.com"
API_VERSION = "2021-07-28"

def get_location_token(location_id: str) -> str:
    """
    Carrega o token de acesso específico para uma location.
    Esta função é uma cópia simplificada da que usamos nos outros scripts.
    """
    try:
        with open("backend/installed_locations_data.json", "r", encoding="utf-8") as f:
            locations_data = json.load(f)
        
        target_location = next((loc for loc in locations_data if loc.get("_id") == location_id or loc.get("id") == location_id), None)
        
        if not target_location:
            raise ValueError(f"Location com ID '{location_id}' não encontrada.")
            
        token_data = target_location.get("location_specific_token_data", {})
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise RuntimeError(f"Token de acesso não encontrado para a Location {location_id}.")
            
        return access_token
    except FileNotFoundError:
        raise FileNotFoundError("Arquivo 'installed_locations_data.json' não encontrado. Execute 'update_all_tokens.py'.")

def build_contact_payload(data: Dict[str, Any], location_id: str) -> Dict[str, Any]:
    """Constrói o payload para a API de contatos a partir dos dados do webhook."""
    cliente_data = data.get("cliente", {})
    
    payload = {
        "locationId": location_id,
        "name": cliente_data.get("nome"),
        "email": cliente_data.get("email"), # Supondo que você adicionará email ao formulário
        "phone": cliente_data.get("telefone"),
        "address1": cliente_data.get("endereco"),
        "city": cliente_data.get("cidade"),
        "source": cliente_data.get("origem"),
        "customFields": []
    }

    # Mapeia os dados do formulário para os IDs dos custom fields
    # Adicione/Remova campos conforme sua necessidade
    mapping = {
        "contact.cpf_ou_cnpj": cliente_data.get("cpf"),
        "contact.consumo_medio_mensal": data.get("consumo", {}).get("consumo_medio_mensal"),
        "contact.potncia_dos_mdulos_w": data.get("equipamentos", {}).get("potencia_modulos_w"),
        "contact.potncia_do_sistema_kw": data.get("equipamentos", {}).get("potencia_sistema_kw"),
        "contact.quantidade_de_mdulos": data.get("equipamentos", {}).get("quantidade_modulos"),
        "contact.valor_da_proposta_r": data.get("valor_proposta"),
        "contact.observaes_da_proposta": data.get("observacoes_gerais")
        # ... adicione outros campos aqui
    }

    for key, value in mapping.items():
        field_id = CUSTOM_FIELD_IDS.get(key)
        if field_id and value is not None:
            payload["customFields"].append({"id": field_id, "field_value": value})
            
    # Filtra chaves com valor None para não enviar dados vazios
    return {k: v for k, v in payload.items() if v is not None}

def upsert_contact(location_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cria ou atualiza um contato no GoHighLevel."""
    access_token = get_location_token(location_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{API_BASE_URL}/contacts/upsert"
    
    print(f"-> Enviando dados de contato para GHL: {payload}")
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status() # Lança exceção para erros HTTP
    
    contact_data = resp.json().get("contact", {})
    print(f"<- Contato processado com sucesso! ID: {contact_data.get('id')}")
    return contact_data

def create_opportunity(location_id: str, contact_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Cria uma oportunidade para um contato."""
    access_token = get_location_token(location_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Version": API_VERSION,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    url = f"{API_BASE_URL}/opportunities/"

    negocio_data = data.get("negocio", {})
    
    payload = {
        "pipelineId": PIPELINE_ID,
        "stageId": PIPELINE_STAGE_ID,
        "name": negocio_data.get("titulo", f"Proposta para {data.get('cliente', {}).get('nome')}"),
        "contactId": contact_id,
        "status": "open",
        "monetaryValue": data.get("valor_proposta")
    }
    
    print(f"-> Criando oportunidade: {payload}")
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    
    opportunity_data = resp.json()
    print(f"<- Oportunidade criada com sucesso! ID: {opportunity_data.get('id')}")
    return opportunity_data

def process_proposal_webhook(location_id: str, data: Dict[str, Any]):
    """
    Orquestra o processo completo: upsert do contato e criação da oportunidade.
    """
    try:
        # Passo 1: Construir o payload e fazer o upsert do contato
        contact_payload = build_contact_payload(data, location_id)
        contact = upsert_contact(location_id, contact_payload)
        
        contact_id = contact.get("id")
        if not contact_id:
            raise ValueError("Não foi possível obter o ID do contato após o upsert.")
            
        # Passo 2: Criar a oportunidade associada ao contato
        create_opportunity(location_id, contact_id, data)
        
        print("\n✅ Processo de Webhook concluído com sucesso!")
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ ERRO HTTP: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"\n❌ ERRO Inesperado: {e}")