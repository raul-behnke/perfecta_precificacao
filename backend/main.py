# backend/main.py

import os
import sys
import json
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Constrói o caminho explícito para o arquivo .env e o carrega
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Adiciona o diretório 'backend' ao sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Lê a variável do webhook do .env
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
if not WEBHOOK_URL:
    raise RuntimeError("A variável de ambiente WEBHOOK_URL não está definida.")

app = FastAPI(title="API de Precificação Solar")

# --- Configuração de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------

# Importa a lógica de cálculo e de gerenciamento de contatos
from services.calculos import calcular_valor_proposta
from services.contact_manager import process_proposal_webhook

# ------------------------------------------------------------
#  Modelos Pydantic para validação dos dados de entrada/saída
# ------------------------------------------------------------

class PropostaInput(BaseModel):
    consumo_medio_mensal: float = Field(..., example=400.0)
    potencia_modulos_w: float = Field(..., example=585.0)
    potencia_sistema_kw: float = Field(..., example=4.68)
    custo_unitario_modulo: float = Field(1000.0, example=1200.0)
    quantidade_inversor: int = Field(1, example=1)
    custo_unitario_inversor: float = Field(3000.0, example=3500.0)
    custo_estrutura: float = Field(500.0, example=600.0)
    custo_cabos: float = Field(200.0, example=250.0)
    ajuste_telhas: float = Field(0.0, example=100.0)
    ajuste_padrao_entrada: float = Field(0.0, example=120.0)
    percentual_indiretos: float = Field(0.05, example=0.05)
    percentual_margem: float = Field(0.20, example=0.20)
    aliquota_impostos: float = Field(0.15, example=0.15)
    valor_adicional: float = Field(0.0, example=100.0)
    forma_desconto: str = Field("Sem Desconto", example="Porcentagem")
    valor_desconto: float = Field(0.0, example=5.0)
    indice_irrad: float = Field(3.79, example=4.0)
    taxa_desempenho: float = Field(0.8, example=0.85)

class PropostaOutput(BaseModel):
    valor_proposta: float

# ----------------------------
#  Rotas da API (endpoints)
# ----------------------------

@app.get("/")
def home():
    return {"mensagem": "API de Precificação Solar rodando. Use POST /calcular ou GET /config para obter webhook."}

@app.get("/config")
def get_config():
    return {"webhook_url": WEBHOOK_URL}

@app.post("/calcular", response_model=PropostaOutput)
def calcular_proposta(input_data: PropostaInput):
    try:
        valor = calcular_valor_proposta(input_data.dict())
        return {"valor_proposta": valor}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINT DE WEBHOOK CORRIGIDO ---
@app.post("/webhook/new-proposal/{location_id}")
async def handle_new_proposal(location_id: str, request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint que recebe os dados (do GHL ou de um teste) e inicia o processo
    de criação/atualização de contato e oportunidade.
    Ele lê o corpo da requisição de forma bruta para evitar erros de validação.
    """
    print(f"--- Webhook recebido para a location: {location_id} ---")
    try:
        payload = await request.json()
        print("--- Payload JSON recebido com sucesso. Iniciando processamento em background. ---")
        
        # Chama a lógica principal em segundo plano
        background_tasks.add_task(process_proposal_webhook, location_id, payload)
        
        return {"status": "success", "detail": "Payload recebido e processamento iniciado."}
        
    except json.JSONDecodeError:
        body_text = await request.body()
        print("!!! ERRO: Não foi possível decodificar o corpo da requisição como JSON.")
        print(f"--- Corpo recebido (texto bruto): ---\n{body_text.decode()}")
        raise HTTPException(status_code=400, detail="O corpo da requisição não é um JSON válido.")

# --- Bloco para execução direta ---
if __name__ == "__main__":
    import uvicorn
    # Usa a porta 8001 como padrão, que sabemos que funciona na sua máquina
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)