# backend/services/calculos.py

from math import ceil
from typing import Dict

def calcular_quantidade_modulos(consumo_mensal: float,
                               potencia_modulo_w: float,
                               indice_irrad: float,
                               taxa_desempenho: float) -> int:
    """
    Calcula a quantidade de módulos (arredondando para cima).
    Fórmula simplificada de exemplo:
      geração_diária = consumo_mensal / 30
      geração_por_modulo = (potencia_modulo_w / 1000) * indice_irrad * taxa_desempenho
      quantidade = ceil(geração_diária / geração_por_modulo)
    """
    geracao_diaria = consumo_mensal / 30.0
    geracao_modulo = (potencia_modulo_w / 1000.0) * indice_irrad * taxa_desempenho
    return ceil(geracao_diaria / geracao_modulo)

def calcular_valor_proposta(inputs: Dict) -> float:
    """
    Orquestra a precificação completa:
    1. Pega inputs (consumo, potência, custos, percentuais etc.)
    2. Calcula quantidade de módulos
    3. Calcula custos de equipamentos, mão de obra, indiretos, margem, impostos, descontos…
    (por ora, usamos valores fixos como placeholders)
    """
    # --- 1) Calcular quantidade de módulos ---
    quantidade_modulos = calcular_quantidade_modulos(
        consumo_mensal=inputs["consumo_medio_mensal"],
        potencia_modulo_w=inputs["potencia_modulos_w"],
        indice_irrad=inputs.get("indice_irrad", 3.79),
        taxa_desempenho=inputs.get("taxa_desempenho", 0.8),
    )

    # --- 2) Custos de Equipamentos (placeholder simples) ---
    custo_unitario_modulo = inputs.get("custo_unitario_modulo", 1000.0)
    custo_total_modulos = quantidade_modulos * custo_unitario_modulo

    quantidade_inversor = inputs.get("quantidade_inversor", 1)
    custo_unitario_inversor = inputs.get("custo_unitario_inversor", 3000.0)
    custo_total_inversor = quantidade_inversor * custo_unitario_inversor

    custo_estrutura = inputs.get("custo_estrutura", 500.0)
    custo_cabos = inputs.get("custo_cabos", 200.0)

    ce = custo_total_modulos + custo_total_inversor + custo_estrutura + custo_cabos

    # --- 3) Custo de Mão de Obra (placeholder) ---
    potencia_sistema_kw = inputs["potencia_sistema_kw"]
    custo_base_por_kw = inputs.get("custo_base_por_kw", 400.0)
    ajuste_telhas = inputs.get("ajuste_telhas", 100.0)
    ajuste_padrao = inputs.get("ajuste_padrao_entrada", 100.0)
    cmo = (potencia_sistema_kw * custo_base_por_kw) + ajuste_telhas + ajuste_padrao

    # --- 4) Custos Indiretos ---
    percentual_indiretos = inputs.get("percentual_indiretos", 0.05)
    ci = (ce + cmo) * percentual_indiretos

    # --- 5) Custo Total do Projeto ---
    ctp = ce + cmo + ci

    # --- 6) Aplicar margem e impostos ---
    percentual_margem = inputs.get("percentual_margem", 0.20)
    valor_margem = ctp * percentual_margem
    preco_antes_impostos = ctp + valor_margem

    aliquota_impostos = inputs.get("aliquota_impostos", 0.15)
    valor_impostos = preco_antes_impostos * aliquota_impostos
    preco_com_impostos = preco_antes_impostos + valor_impostos

    # --- 7) Adicionar valor adicional e aplicar desconto ---
    valor_adicional = inputs.get("valor_adicional", 0.0)
    preco_antes_desconto = preco_com_impostos + valor_adicional

    forma_desconto = inputs.get("forma_desconto", "Sem Desconto")
    valor_desconto = inputs.get("valor_desconto", 0.0)
    if forma_desconto.lower() in ("porcentagem", "%"):
        preco_final = preco_antes_desconto * (1 - valor_desconto / 100.0)
    elif forma_desconto.lower() == "valor":
        preco_final = preco_antes_desconto - valor_desconto
    else:
        preco_final = preco_antes_desconto

    return round(preco_final, 2)
