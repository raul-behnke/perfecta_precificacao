# backend/main.py

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env (se existir)
load_dotenv()

app = FastAPI(title="API de Precificação Solar")

# ——————— Configuração de CORS ———————
# Permite que o front-end (rodando em outro domínio/porta ou via file://) faça requisições.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Permite qualquer origem. Em produção, especifique apenas o domínio necessário.
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE etc.
    allow_headers=["*"],            # Content-Type, Authorization etc.
)
# ——————————————————————————————————————————

# Importa a lógica de cálculo que está no arquivo services/calculos.py
from services.calculos import calcular_valor_proposta


# ------------------------------------------------------------
#  Modelos Pydantic para validação dos dados de entrada/saída
# ------------------------------------------------------------

class PropostaInput(BaseModel):
    """
    Modelo de dados de entrada para a rota /calcular.
    Todos os campos marcados como "..." (Field(...)) são obrigatórios.
    Os que têm valores default podem ser omitidos no JSON de requisição.
    """
    consumo_medio_mensal: float = Field(..., example=400.0)
    potencia_modulos_w: float = Field(..., example=585.0)
    potencia_sistema_kw: float = Field(..., example=4.68)

    custo_unitario_modulo: float = Field(1000.0, example=1200.0)
    quantidade_inversor: int = Field(1, example=1)
    custo_unitario_inversor: float = Field(3000.0, example=3500.0)
    custo_estrutura: float = Field(500.0, example=600.0)
    custo_cabos: float = Field(200.0, example=250.0)

    ajuste_telhas: float = Field(100.0, example=150.0)
    ajuste_padrao_entrada: float = Field(100.0, example=120.0)

    percentual_indiretos: float = Field(0.05, example=0.05)
    percentual_margem: float = Field(0.20, example=0.20)
    aliquota_impostos: float = Field(0.15, example=0.15)

    valor_adicional: float = Field(0.0, example=100.0)
    forma_desconto: str = Field("Sem Desconto", example="Porcentagem")
    valor_desconto: float = Field(0.0, example=5.0)

    indice_irrad: float = Field(3.79, example=4.0)
    taxa_desempenho: float = Field(0.8, example=0.85)


class PropostaOutput(BaseModel):
    """
    Modelo de dados de saída (retorna apenas o valor final da proposta).
    """
    valor_proposta: float


# ----------------------------
#  Rotas da API (endpoints)
# ----------------------------

@app.get("/")
def home():
    """
    Rota raiz apenas para verificar que a API está rodando.
    """
    return {"mensagem": "API de Precificação Solar rodando. Use POST /calcular para obter o valor da proposta."}


@app.post("/calcular", response_model=PropostaOutput)
def calcular_proposta(input: PropostaInput):
    """
    Recebe todos os dados de entrada no formato PropostaInput,
    chama a função calcular_valor_proposta e retorna o valor calculado.
    """
    try:
        # Converte o Pydantic model em dicionário e passa para a função de cálculo
        valor = calcular_valor_proposta(input.dict())
        return {"valor_proposta": valor}
    except Exception as e:
        # Em caso de erro durante o cálculo, retorna 400 com a mensagem de detalhe
        raise HTTPException(status_code=400, detail=str(e))


# Caso queira rodar este arquivo diretamente com 'python main.py'
if __name__ == "__main__":
    import uvicorn

    # Lê a porta do arquivo .env ou usa 8000 como padrão
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
