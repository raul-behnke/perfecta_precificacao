# backend/main.py

import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (incluindo o WEBHOOK_URL)
load_dotenv()

# Lê a variável do webhook do .env
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
if not WEBHOOK_URL:
    raise RuntimeError("A variável de ambiente WEBHOOK_URL não está definida.")

app = FastAPI(title="API de Precificação Solar")

# ——————— Configuração de CORS ———————
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Permite qualquer origem durante o dev; em produção, restrinja ao seu domínio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ——————————————————————————————————————————

# Importa a lógica de cálculo
from services.calculos import calcular_valor_proposta

# (Opcional: Se você for manter a lógica /webhook interna, importe ghl_clients aqui)

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
    """
    Retorna a URL do webhook configurada no .env.
    O front-end usa este endpoint para saber para onde enviar os dados.
    """
    return {"webhook_url": WEBHOOK_URL}


@app.post("/calcular", response_model=PropostaOutput)
def calcular_proposta(input: PropostaInput):
    try:
        valor = calcular_valor_proposta(input.dict())
        return {"valor_proposta": valor}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# (Se você tiver rota /webhook interna, mantenha aqui. Mas neste momento,
#  como iremos enviar direto ao LeadConnectorHQ, não precisamos dela.)

# Caso queira rodar este arquivo diretamente com 'python main.py'
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
