"""
Gerador de dados fictícios bancários brasileiros.

Produz três tabelas com anomalias intencionais para exercitar
todas as camadas da pipeline (validação, profiler e SLM).

Cenários disponíveis:
  - baseline    : dados válidos, primeira carga
  - non_breaking: adiciona coluna nova anulável (schema evolution permitido)
  - breaking    : altera tipo de coluna-chave (deve ir para quarentena)
"""

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import yaml

random.seed(42)
np.random.seed(42)

# Faker é opcional — fallback para stdlib se não estiver instalado
try:
    from faker import Faker
    fake = Faker("pt_BR")
    _NOMES = None
    _CPFS  = None
except ImportError:
    fake = None
    _NOMES = [
        "Ana Silva","Carlos Souza","Maria Oliveira","João Santos","Pedro Alves",
        "Beatriz Lima","Lucas Pereira","Fernanda Costa","Rafael Martins","Juliana Rocha",
        "Gustavo Ferreira","Camila Ribeiro","André Carvalho","Larissa Mendes","Thiago Barbosa",
        "Priscila Nascimento","Rodrigo Gomes","Vanessa Araújo","Bruno Cardoso","Tatiane Dias",
    ]
    _CNPJS = [f"{random.randint(10,99)}.{random.randint(100,999)}.{random.randint(100,999)}/0001-{random.randint(10,99)}" for _ in range(500)]


def _cpf() -> str:
    if fake:
        return fake.cpf().replace(".", "").replace("-", "")
    d = [random.randint(0, 9) for _ in range(11)]
    return "".join(map(str, d))


def _nome() -> str:
    if fake:
        return fake.name()
    return random.choice(_NOMES) + f" {random.randint(100,999)}"


def _cnpj() -> str:
    if fake:
        return fake.cnpj().replace(".", "").replace("/", "").replace("-", "")
    return f"{random.randint(10000000,99999999):08d}{random.randint(1000,9999):04d}"

ScenarioType = Literal["baseline", "non_breaking", "breaking"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    return (start + timedelta(days=random.randint(0, delta.days))).strftime("%Y-%m-%d")


def _inject_nulls(series: pd.Series, pct: float) -> pd.Series:
    mask = np.random.random(len(series)) < pct
    return series.where(~mask, other=None)


# ─────────────────────────────────────────────────────────────────────────────
# tb_clientes
# ─────────────────────────────────────────────────────────────────────────────
def _gerar_clientes(n: int = 500, scenario: ScenarioType = "baseline") -> pd.DataFrame:
    segmentos = ["VAREJO", "PRIME", "PRIVATE", "PJ_PEQUENO", "PJ_MEDIO"]
    rows = []
    for _ in range(n):
        rows.append(
            {
                "cd_cliente"      : str(uuid.uuid4())[:12].upper(),
                "nr_cpf_cnpj"     : _cpf(),
                "nm_cliente"      : _nome(),
                "dt_nascimento"   : _random_date(datetime(1950, 1, 1), datetime(2000, 12, 31)),
                "cd_segmento"     : random.choice(segmentos),
                "cd_agencia"      : str(random.randint(1000, 9999)),
                "vl_renda_mensal" : round(random.uniform(1500, 80000), 2),
                "fl_ativo"        : random.choice([True, False]),
                "dt_cadastro"     : _random_date(datetime(2015, 1, 1), datetime(2024, 6, 1)),
            }
        )
    df = pd.DataFrame(rows)

    # Anomalias: 18 % de nulos em renda (dado incompleto vindo do legado SAS)
    df["vl_renda_mensal"] = _inject_nulls(df["vl_renda_mensal"], 0.18)
    # 3 % de agências com formato inválido (simulando erro de exportação SAS)
    bad_idx = df.sample(frac=0.03).index
    df.loc[bad_idx, "cd_agencia"] = "AGENC-???"

    if scenario == "non_breaking":
        # Nova coluna anulável — deve gerar WARNING mas avançar
        df["cd_gestor_relacionamento"] = _inject_nulls(
            pd.Series([str(uuid.uuid4())[:8].upper() for _ in range(n)]), 0.60
        )
    elif scenario == "breaking":
        # Coluna obrigatória 'cd_agencia' foi removida da exportação SAS → BREAKING
        df = df.drop(columns=["cd_agencia"])

    return df


def _contrato_clientes(scenario: ScenarioType) -> dict:
    base = {
        "table"       : "tb_clientes",
        "description" : "Cadastro mestre de clientes pessoa física e jurídica.",
        "owner"       : "squad-dados-cadastrais",
        "version"     : "1.0.0",
        "tolerance"   : {"max_null_pct": 25, "allow_duplicates": False},
        "schema": [
            {"name": "cd_cliente",       "type": "string",  "nullable": False, "primary_key": True},
            {"name": "nr_cpf_cnpj",      "type": "string",  "nullable": False},
            {"name": "nm_cliente",       "type": "string",  "nullable": False},
            {"name": "dt_nascimento",    "type": "date",    "nullable": True},
            {"name": "cd_segmento",      "type": "string",  "nullable": False},
            {"name": "cd_agencia",       "type": "string",  "nullable": False},
            {"name": "vl_renda_mensal",  "type": "float",   "nullable": True},
            {"name": "fl_ativo",         "type": "boolean", "nullable": False},
            {"name": "dt_cadastro",      "type": "date",    "nullable": False},
        ],
    }
    # Em non_breaking: dados têm coluna nova, mas contrato ainda não foi atualizado
    # → validator detecta coluna extra no arquivo → NON_BREAKING warning
    # Em breaking: coluna cd_agencia foi removida dos dados → contrato exige ela → BREAKING
    return base


# ─────────────────────────────────────────────────────────────────────────────
# tb_transacoes
# ─────────────────────────────────────────────────────────────────────────────
def _gerar_transacoes(clientes_df: pd.DataFrame, n: int = 2000) -> pd.DataFrame:
    tipos = ["COMPRA", "SAQUE", "TED", "PIX", "PAGAMENTO_BOLETO", "ESTORNO"]
    rows = []
    for _ in range(n):
        vl = round(random.uniform(1.50, 25000.00), 2)
        rows.append(
            {
                "id_transacao"      : str(uuid.uuid4()),
                "cd_cliente"        : clientes_df["cd_cliente"].dropna().sample(1).iloc[0],
                "dt_transacao"      : _random_date(datetime(2023, 1, 1), datetime(2024, 12, 31)),
                "vl_transacao"      : vl,
                "tp_transacao"      : random.choice(tipos),
                "cd_estabelecimento": _cnpj(),
                "fl_suspeita"       : random.random() < 0.04,   # 4 % marcado como suspeito
                "cd_canal"          : random.choice(["APP", "INTERNET", "AGENCIA", "ATM", "POS"]),
            }
        )
    df = pd.DataFrame(rows)
    # 6 % sem estabelecimento (compras online sem identificação)
    df["cd_estabelecimento"] = _inject_nulls(df["cd_estabelecimento"], 0.06)
    # Duplicatas intencionais: 1.5 %
    dupes = df.sample(frac=0.015)
    df = pd.concat([df, dupes], ignore_index=True)
    return df


def _contrato_transacoes() -> dict:
    return {
        "table"       : "tb_transacoes",
        "description" : "Movimentações financeiras de todos os canais de atendimento.",
        "owner"       : "squad-transacoes",
        "version"     : "2.3.1",
        "tolerance"   : {"max_null_pct": 10, "allow_duplicates": False},
        "schema": [
            {"name": "id_transacao",       "type": "string",  "nullable": False, "primary_key": True},
            {"name": "cd_cliente",         "type": "string",  "nullable": False},
            {"name": "dt_transacao",       "type": "date",    "nullable": False},
            {"name": "vl_transacao",       "type": "float",   "nullable": False},
            {"name": "tp_transacao",       "type": "string",  "nullable": False},
            {"name": "cd_estabelecimento", "type": "string",  "nullable": True},
            {"name": "fl_suspeita",        "type": "boolean", "nullable": False},
            {"name": "cd_canal",           "type": "string",  "nullable": False},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# tb_contratos_credito
# ─────────────────────────────────────────────────────────────────────────────
def _gerar_contratos_credito(clientes_df: pd.DataFrame, n: int = 300) -> pd.DataFrame:
    produtos = ["CARTAO_CREDITO", "CHEQUE_ESPECIAL", "CREDITO_PESSOAL", "FINANCIAMENTO_VEICULO", "CONSIGNADO"]
    status   = ["ATIVO", "ENCERRADO", "EM_ATRASO", "RENEGOCIADO"]
    rows = []
    for _ in range(n):
        limite    = round(random.uniform(500, 100000), 2)
        utilizado = round(random.uniform(0, limite * 1.15), 2)   # até 15 % acima do limite (anomalia)
        rows.append(
            {
                "id_contrato"    : str(uuid.uuid4())[:16].upper(),
                "cd_cliente"     : clientes_df["cd_cliente"].dropna().sample(1).iloc[0],
                "dt_contrato"    : _random_date(datetime(2018, 1, 1), datetime(2024, 6, 1)),
                "vl_limite"      : limite,
                "vl_utilizado"   : utilizado,
                "tp_produto"     : random.choice(produtos),
                "cd_status"      : random.choice(status),
                "dt_vencimento"  : _random_date(datetime(2024, 1, 1), datetime(2030, 12, 31)),
                "nr_parcelas"    : random.randint(1, 60),
                "tx_juros_am"    : round(random.uniform(0.8, 8.5), 4),
            }
        )
    return pd.DataFrame(rows)


def _contrato_contratos_credito() -> dict:
    return {
        "table"       : "tb_contratos_credito",
        "description" : "Contratos de produtos de crédito ativos e encerrados.",
        "owner"       : "squad-credito",
        "version"     : "3.0.0",
        "tolerance"   : {"max_null_pct": 5, "allow_duplicates": False},
        "schema": [
            {"name": "id_contrato",   "type": "string",  "nullable": False, "primary_key": True},
            {"name": "cd_cliente",    "type": "string",  "nullable": False},
            {"name": "dt_contrato",   "type": "date",    "nullable": False},
            {"name": "vl_limite",     "type": "float",   "nullable": False},
            {"name": "vl_utilizado",  "type": "float",   "nullable": False},
            {"name": "tp_produto",    "type": "string",  "nullable": False},
            {"name": "cd_status",     "type": "string",  "nullable": False},
            {"name": "dt_vencimento", "type": "date",    "nullable": False},
            {"name": "nr_parcelas",   "type": "integer", "nullable": False},
            {"name": "tx_juros_am",   "type": "float",   "nullable": False},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point público
# ─────────────────────────────────────────────────────────────────────────────
def generate_all(
    storage,
    scenario: ScenarioType = "baseline",
) -> list[dict]:
    """
    Gera dados fictícios e persiste via Storage (bronze + contracts).

    Bronze layer  : CSVs com os dados gerados (landing zone)
    Contracts     : manifestos YAML com os contratos de dados

    Retorna lista de dicts com metadados de cada tabela produzida.
    """
    print(f"\n[GENERATE] Gerando dados ficticios - cenario: [{scenario.upper()}]")

    clientes_df   = _gerar_clientes(500, scenario)
    transacoes_df = _gerar_transacoes(clientes_df)
    contratos_df  = _gerar_contratos_credito(clientes_df)

    datasets = [
        ("tb_clientes",          clientes_df,   _contrato_clientes(scenario)),
        ("tb_transacoes",        transacoes_df, _contrato_transacoes()),
        ("tb_contratos_credito", contratos_df,  _contrato_contratos_credito()),
    ]

    produced = []
    for table_name, df, contract in datasets:
        suffix            = f"_{scenario}" if scenario != "baseline" else ""
        csv_filename      = f"{table_name}{suffix}.csv"
        contract_filename = f"{table_name}{suffix}.yaml"

        storage.write("bronze", csv_filename, df)
        storage.write_text("contracts", contract_filename,
                           yaml.dump(contract, allow_unicode=True, sort_keys=False))

        print(f"   [OK] {table_name}: {len(df)} linhas -> bronze/{csv_filename}")
        produced.append({
            "table"            : table_name,
            "filename"         : csv_filename,
            "contract_filename": contract_filename,
            "scenario"         : scenario,
        })

    return produced
