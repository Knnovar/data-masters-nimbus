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
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

from src.generators.writers import (
    BaseWriter,
    CSVWriter,
    JSONWriter,
    FixedWidthWriter,
    WriterFactory,
    SUPPORTED_FORMATS,
)

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
        "table"          : "tb_clientes",
        "description"    : "Cadastro mestre de clientes pessoa fisica e juridica.",
        "owner"          : "squad-dados-cadastrais",
        "version"        : "1.0.0",
        "manifest_status": "DRAFT",
        "source": {
            "system"          : "CORE_BANCARIO_TOTVS",
            "format"          : "csv",
            "encoding"        : "utf-8",
            "os"              : "unix",
            "update_frequency": "daily",
            "contact"         : "squad-dados-cadastrais@banco.com.br",
        },
        "regulatory": {
            "tags"               : ["LGPD", "BACEN_4658"],
            "data_classification": "confidential",
            "retention_years"    : 10,
        },
        "steward": {
            "name" : "Data Steward Cadastral",
            "email": "steward-cadastral@banco.com.br",
        },
        "business_context": (
            "Tabela mestre de clientes utilizada por todos os produtos de credito e relacionamento. "
            "A segmentacao (cd_segmento) determina o produto ofertado e o gestor responsavel. "
            "Atualizada diariamente pelo batch noturno do CORE_BANCARIO_TOTVS."
        ),
        "tolerance"   : {"max_null_pct": 25, "allow_duplicates": False},
        "dependencies": ["tb_agencias", "tb_segmentos"],
        "sample_queries": [
            {"description": "Distribuicao por segmento",
             "sql": "SELECT cd_segmento, COUNT(*) as qtd FROM tb_clientes WHERE fl_ativo = true GROUP BY cd_segmento"},
            {"description": "Clientes ativos com renda acima de 10k",
             "sql": "SELECT cd_cliente, nm_cliente, vl_renda_mensal FROM tb_clientes WHERE fl_ativo = true AND vl_renda_mensal > 10000"},
        ],
        "schema": [
            {"name": "cd_cliente",      "type": "string",  "nullable": False, "primary_key": True,
             "description": "Codigo unico do cliente no sistema legado. Gerado sequencialmente pelo CORE_BANCARIO."},
            {"name": "nr_cpf_cnpj",     "type": "string",  "nullable": False,
             "description": "CPF (11 digitos) ou CNPJ (14 digitos) sem mascara.",
             "regulatory_flags": ["LGPD_SENSITIVE"]},
            {"name": "nm_cliente",      "type": "string",  "nullable": False,
             "description": "Nome completo do cliente conforme cadastro na Receita Federal.",
             "regulatory_flags": ["LGPD_SENSITIVE"]},
            {"name": "dt_nascimento",   "type": "date",    "nullable": True,
             "description": "Data de nascimento. Nula para clientes PJ.",
             "regulatory_flags": ["LGPD_SENSITIVE"]},
            {"name": "cd_segmento",     "type": "string",  "nullable": False,
             "description": "Segmento de relacionamento. Dominio: VAREJO, PRIME, PRIVATE, PJ_PEQUENO, PJ_MEDIO.",
             "business_rules": ["PRIME: vl_renda_mensal >= 10000", "PRIVATE: vl_renda_mensal >= 30000"]},
            {"name": "cd_agencia",      "type": "string",  "nullable": False,
             "description": "Codigo numerico de 4 digitos da agencia de relacionamento principal."},
            {"name": "vl_renda_mensal", "type": "float",   "nullable": True,
             "description": "Renda mensal declarada em BRL. Nula para clientes PJ.",
             "business_rules": ["Sempre nulo para cd_segmento IN (PJ_PEQUENO, PJ_MEDIO)"],
             "regulatory_flags": ["SCR_CANDIDATE"]},
            {"name": "fl_ativo",        "type": "boolean", "nullable": False,
             "description": "Indica se o cliente possui relacionamento ativo com o banco."},
            {"name": "dt_cadastro",     "type": "date",    "nullable": False,
             "description": "Data de abertura do cadastro no sistema."},
        ],
    }
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
        "table"          : "tb_transacoes",
        "description"    : "Movimentacoes financeiras de todos os canais de atendimento.",
        "owner"          : "squad-transacoes",
        "version"        : "2.3.1",
        "manifest_status": "DRAFT",
        "source": {
            "system"          : "SWITCH_TRANSACIONAL",
            "format"          : "csv",
            "encoding"        : "utf-8",
            "os"              : "unix",
            "update_frequency": "event_driven",
            "contact"         : "squad-transacoes@banco.com.br",
        },
        "regulatory": {
            "tags"               : ["BACEN_4658", "PCI_DSS"],
            "data_classification": "confidential",
            "retention_years"    : 7,
        },
        "steward": {
            "name" : "Data Steward Transacional",
            "email": "steward-transacoes@banco.com.br",
        },
        "business_context": (
            "Registro de todas as movimentacoes financeiras por canal. "
            "fl_suspeita sinaliza transacoes em analise pelo motor antifraude. "
            "cd_estabelecimento pode ser nulo para compras online nao identificadas."
        ),
        "tolerance"      : {"max_null_pct": 10, "allow_duplicates": False},
        "dependencies"   : ["tb_clientes"],
        "sample_queries" : [
            {"description": "Volume transacionado por canal no mes",
             "sql": "SELECT cd_canal, COUNT(*) as qtd, SUM(vl_transacao) as total FROM tb_transacoes GROUP BY cd_canal"},
            {"description": "Transacoes suspeitas recentes",
             "sql": "SELECT * FROM tb_transacoes WHERE fl_suspeita = true ORDER BY dt_transacao DESC LIMIT 100"},
        ],
        "schema": [
            {"name": "id_transacao",       "type": "string",  "nullable": False, "primary_key": True,
             "description": "UUID da transacao. Gerado pelo switch transacional no momento da operacao."},
            {"name": "cd_cliente",         "type": "string",  "nullable": False,
             "description": "Referencia ao cliente em tb_clientes."},
            {"name": "dt_transacao",       "type": "date",    "nullable": False,
             "description": "Data da transacao no fuso horario America/Sao_Paulo."},
            {"name": "vl_transacao",       "type": "float",   "nullable": False,
             "description": "Valor em BRL. Positivo para debitos, negativo para estornos."},
            {"name": "tp_transacao",       "type": "string",  "nullable": False,
             "description": "Tipo da operacao. Dominio: COMPRA, SAQUE, TED, PIX, PAGAMENTO_BOLETO, ESTORNO."},
            {"name": "cd_estabelecimento", "type": "string",  "nullable": True,
             "description": "CNPJ do estabelecimento. Nulo para compras online nao identificadas (~6%)."},
            {"name": "fl_suspeita",        "type": "boolean", "nullable": False,
             "description": "Flag do motor antifraude. True indica transacao em analise (~4% do volume)."},
            {"name": "cd_canal",           "type": "string",  "nullable": False,
             "description": "Canal de origem. Dominio: APP, INTERNET, AGENCIA, ATM, POS."},
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
        "table"          : "tb_contratos_credito",
        "description"    : "Contratos de produtos de credito ativos e encerrados.",
        "owner"          : "squad-credito",
        "version"        : "3.0.0",
        "manifest_status": "DRAFT",
        "source": {
            "system"          : "SISTEMA_CREDITO_SAS",
            "format"          : "sas7bdat",
            "encoding"        : "latin-1",
            "os"              : "unix",
            "update_frequency": "daily",
            "contact"         : "squad-credito@banco.com.br",
        },
        "regulatory": {
            "tags"               : ["SCR", "BACEN_4658", "LGPD"],
            "data_classification": "restricted",
            "retention_years"    : 10,
        },
        "steward": {
            "name" : "Data Steward Credito",
            "email": "steward-credito@banco.com.br",
        },
        "business_context": (
            "Contratos de credito de todos os produtos ofertados pelo banco. "
            "Alimenta o SCR mensalmente. vl_utilizado pode exceder vl_limite em ate 15% "
            "para produtos com tolerancia de limite (cheque especial). "
            "cd_status EM_ATRASO dispara cobranca automatica apos D+1."
        ),
        "tolerance"      : {"max_null_pct": 5, "allow_duplicates": False},
        "dependencies"   : ["tb_clientes"],
        "sample_queries" : [
            {"description": "Contratos em atraso por produto",
             "sql": "SELECT tp_produto, COUNT(*) as qtd FROM tb_contratos_credito WHERE cd_status = 'EM_ATRASO' GROUP BY tp_produto"},
            {"description": "Utilizacao media do limite por segmento",
             "sql": "SELECT tp_produto, AVG(vl_utilizado/NULLIF(vl_limite,0)) as pct_utilizacao FROM tb_contratos_credito WHERE cd_status = 'ATIVO' GROUP BY tp_produto"},
        ],
        "schema": [
            {"name": "id_contrato",   "type": "string",  "nullable": False, "primary_key": True,
             "description": "Identificador unico do contrato gerado pelo sistema de credito.",
             "sas_label"  : "ID CONTRATO CREDITO"},
            {"name": "cd_cliente",    "type": "string",  "nullable": False,
             "description": "Referencia ao cliente em tb_clientes.",
             "sas_label"  : "CODIGO CLIENTE"},
            {"name": "dt_contrato",   "type": "date",    "nullable": False,
             "description": "Data de abertura do contrato.",
             "sas_label"  : "DATA ABERTURA CONTRATO"},
            {"name": "vl_limite",     "type": "float",   "nullable": False,
             "description": "Limite de credito aprovado em BRL.",
             "sas_label"  : "VALOR LIMITE APROVADO",
             "regulatory_flags": ["SCR_CANDIDATE"]},
            {"name": "vl_utilizado",  "type": "float",   "nullable": False,
             "description": "Saldo utilizado atual em BRL. Pode exceder vl_limite em produtos com tolerancia.",
             "sas_label"  : "VALOR UTILIZADO ATUAL",
             "business_rules": ["Pode ser ate 15% acima de vl_limite para CHEQUE_ESPECIAL"],
             "regulatory_flags": ["SCR_CANDIDATE"]},
            {"name": "tp_produto",    "type": "string",  "nullable": False,
             "description": "Tipo do produto de credito. Dominio: CARTAO_CREDITO, CHEQUE_ESPECIAL, CREDITO_PESSOAL, FINANCIAMENTO_VEICULO, CONSIGNADO."},
            {"name": "cd_status",     "type": "string",  "nullable": False,
             "description": "Status do contrato. Dominio: ATIVO, ENCERRADO, EM_ATRASO, RENEGOCIADO.",
             "business_rules": ["EM_ATRASO dispara cobranca automatica apos D+1"]},
            {"name": "dt_vencimento", "type": "date",    "nullable": False,
             "description": "Data de vencimento da ultima parcela ou do contrato."},
            {"name": "nr_parcelas",   "type": "integer", "nullable": False,
             "description": "Numero total de parcelas do contrato. 1 para credito rotativo."},
            {"name": "tx_juros_am",   "type": "float",   "nullable": False,
             "description": "Taxa de juros ao mes em percentual. Ex: 2.5 = 2,5% a.m.",
             "sas_label"  : "TAXA JUROS MENSAL"},
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Entry point público
# ─────────────────────────────────────────────────────────────────────────────
# ─── Leiaute posicional padrão para FixedWidthWriter ─────────────────────────
_FIXED_LAYOUT_CLIENTES: List[Tuple[str, int, str]] = [
    ("cd_cliente",      12, "string"),
    ("nr_cpf_cnpj",     14, "string"),
    ("nm_cliente",      40, "string"),
    ("dt_nascimento",   10, "date"),
    ("cd_segmento",     12, "string"),
    ("cd_agencia",       6, "string"),
    ("vl_renda_mensal", 12, "float"),
    ("fl_ativo",         1, "string"),
    ("dt_cadastro",     10, "date"),
]

_FIXED_LAYOUT_TRANSACOES: List[Tuple[str, int, str]] = [
    ("id_transacao",       36, "string"),
    ("cd_cliente",         12, "string"),
    ("dt_transacao",       10, "date"),
    ("vl_transacao",       12, "float"),
    ("tp_transacao",       20, "string"),
    ("cd_estabelecimento", 18, "string"),
    ("fl_suspeita",         1, "string"),
    ("cd_canal",            8, "string"),
]

_FIXED_LAYOUT_CONTRATOS: List[Tuple[str, int, str]] = [
    ("id_contrato",    36, "string"),
    ("cd_cliente",     12, "string"),
    ("dt_contrato",    10, "date"),
    ("vl_limite",      12, "float"),
    ("vl_utilizado",   12, "float"),
    ("tp_produto",     24, "string"),
    ("cd_status",      12, "string"),
    ("dt_vencimento",  10, "date"),
    ("nr_parcelas",     5, "integer"),
    ("tx_juros_am",     8, "float"),
]

# Aninhamento JSON para testar json_normalize da pipeline
_JSON_NEST_CLIENTES: Dict[str, List[str]] = {
    "dados_pessoais": ["nm_cliente", "dt_nascimento", "nr_cpf_cnpj"],
    "dados_bancarios": ["cd_segmento", "cd_agencia", "vl_renda_mensal"],
}

_JSON_NEST_CONTRATOS: Dict[str, List[str]] = {
    "valores": ["vl_limite", "vl_utilizado", "tx_juros_am"],
    "info_contrato": ["tp_produto", "cd_status", "dt_vencimento", "nr_parcelas"],
}


def _build_writer(fmt: str, table_name: str, scenario: ScenarioType = "baseline") -> BaseWriter:
    """
    Constrói o writer adequado para a tabela e formato solicitados.

    Args:
        fmt: Formato de saida ('csv', 'json', 'fixed').
        table_name: Nome da tabela para selecionar leiaute/nesting correto.
        scenario: Cenario de dados (afeta layouts para 'breaking').

    Returns:
        Instância de BaseWriter configurada.

    Raises:
        ValueError: Formato invalido ou tabela sem leiaute definido.
    """
    if fmt == "csv":
        return WriterFactory.get("csv")

    if fmt == "json":
        # Pipeline usa JSON flat — colunas correspondem ao contrato sem transformacao.
        # O aninhamento (_JSON_NEST_CLIENTES / _JSON_NEST_CONTRATOS) existe apenas
        # para testes do extractor_json.py, nao para o fluxo de validacao.
        return WriterFactory.get("json", nest_columns=None, root_key="data")

    if fmt == "fixed":
        layout_map: Dict[str, List[Tuple[str, int, str]]] = {
            "tb_clientes"          : _FIXED_LAYOUT_CLIENTES,
            "tb_transacoes"        : _FIXED_LAYOUT_TRANSACOES,
            "tb_contratos_credito" : _FIXED_LAYOUT_CONTRATOS,
        }
        if table_name not in layout_map:
            raise ValueError(f"Sem leiaute posicional definido para: {table_name}")
        layout = layout_map[table_name]
        # Em cenário 'breaking', cd_agencia foi removida — ajusta layout
        if scenario == "breaking" and table_name == "tb_clientes":
            layout = [col for col in layout if col[0] != "cd_agencia"]
        return WriterFactory.get("fixed", layout=layout)

    raise ValueError(
        f"Formato nao suportado: '{fmt}'. Opcoes validas: {', '.join(SUPPORTED_FORMATS)}"
    )


def generate_all(
    storage,
    scenario: ScenarioType = "baseline",
    fmt: str = "csv",
) -> List[dict]:
    """
    Gera dados fictícios bancários e persiste via Storage na landing zone.

    Separa a responsabilidade de geração de dados (domínio) da escrita
    (formato), delegando para o writer selecionado por WriterFactory.

    Args:
        storage: Instância de StorageBase (LocalStorage ou MinIOStorage).
        scenario: Cenario de dados. Um de: 'baseline', 'non_breaking', 'breaking'.
        fmt: Formato de saída. Um de: 'csv', 'json', 'fixed'.

    Returns:
        Lista de dicts com metadados das tabelas produzidas:
        [{"table": ..., "filename": ..., "contract_filename": ..., "scenario": ...}]

    Raises:
        ValueError: Formato nao suportado ou parametros invalidos.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Formato nao suportado: '{fmt}'. Opcoes validas: {', '.join(SUPPORTED_FORMATS)}"
        )

    print(f"\n[GENERATE] Gerando dados ficticios - cenario: [{scenario.upper()}] - formato: [{fmt.upper()}]")

    clientes_df   = _gerar_clientes(500, scenario)
    transacoes_df = _gerar_transacoes(clientes_df)
    contratos_df  = _gerar_contratos_credito(clientes_df)

    datasets: List[Tuple[str, pd.DataFrame, dict]] = [
        ("tb_clientes",          clientes_df,   _contrato_clientes(scenario)),
        ("tb_transacoes",        transacoes_df, _contrato_transacoes()),
        ("tb_contratos_credito", contratos_df,  _contrato_contratos_credito()),
    ]

    produced: List[dict] = []

    for table_name, df, contract in datasets:
        suffix            = f"_{scenario}" if scenario != "baseline" else ""
        contract_filename = f"{table_name}{suffix}.yaml"

        # Seleciona writer — delega serialização para o Strategy correto
        writer                = _build_writer(fmt, table_name, scenario)
        base_name             = f"{table_name}{suffix}"
        filename, file_content = writer.serialize(df, base_name)

        # Persiste via storage (agnostico de backend)
        storage.write_text("bronze", filename, file_content)

        # Para fixed-width, grava sidecar com colspecs para leitura posterior
        if fmt == "fixed" and hasattr(writer, "layout_sidecar"):
            sidecar_name, sidecar_content = writer.layout_sidecar(base_name)
            storage.write_text("bronze", sidecar_name, sidecar_content)
        storage.write_text("contracts", contract_filename,
                           yaml.dump(contract, allow_unicode=True, sort_keys=False))

        print(f"   [OK] {table_name}: {len(df)} linhas -> bronze/{filename}")
        produced.append({
            "table"            : table_name,
            "filename"         : filename,
            "contract_filename": contract_filename,
            "scenario"         : scenario,
            "format"           : fmt,
        })

    return produced
