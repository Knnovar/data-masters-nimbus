"""
src/governance/grant_emitter.py — DDL de controle de acesso derivado do Manifest.

O Manifest ja declara quem e o dono (`owner`), qual a classificacao da tabela
(`regulatory.data_classification`) e quais colunas sao sensiveis
(`regulatory_flags: [LGPD_SENSITIVE]`). Esse mesmo artefato, portanto, ja
contem tudo que uma politica de acesso precisa saber — o que faltava era
traduzi-lo para a linguagem do catalogo.

Este modulo faz **apenas a traducao**. Ele gera texto: `GRANT`, funcao de
mascara e `ALTER COLUMN ... SET MASK` em SQL do Unity Catalog. Nao abre conexao,
nao autentica, nao executa e nao depende de service principal — o artefato sai
para revisao de quem tem alcada para conceder acesso.

A separacao e deliberada e e a parte defensavel do desenho: o pipeline **deriva**
a permissao do contrato, mas nao **concede** permissao. Concessao automatica a
partir de um arquivo que o proprio pipeline escreve seria escalonamento de
privilegio disfarcado de automacao.

Uso:
    python -m src.governance.grant_emitter --file data/contracts/tb_clientes.yaml
    python tasks.py emit-grants --file data/contracts/tb_clientes.yaml
"""

import argparse
import sys
from pathlib import Path

MASK_FUNCTION = "mask_pii"

# Classificacoes em que conceder SELECT amplo nao e decisao do contrato.
_RESTRICTED = {"restricted", "secret", "confidential_restricted"}

# Tipo do Manifest -> tipo SQL. O Unity Catalog exige que a funcao de mascara
# devolva o mesmo tipo da coluna, entao ha uma funcao por tipo mascarado.
_SQL_TYPES = {
    "string": "STRING", "integer": "BIGINT", "long": "BIGINT", "float": "DOUBLE",
    "double": "DOUBLE", "decimal": "DECIMAL(38,6)", "boolean": "BOOLEAN",
    "date": "DATE", "timestamp": "TIMESTAMP",
}


def _sql_type(tipo: str) -> str:
    base = str(tipo or "string").split("(")[0].strip().lower()
    return _SQL_TYPES.get(base, "STRING")


def _mask_expression(sql_type: str) -> str:
    """Valor devolvido a quem nao pode ver o original, no tipo da coluna."""
    return "'***'" if sql_type == "STRING" else "NULL"


def _mask_name(sql_type: str) -> str:
    sufixo = sql_type.split("(")[0].lower()
    return "{}_{}".format(MASK_FUNCTION, sufixo)


def _ident(valor: str) -> str:
    """Nome de objeto do catalogo, sem aspas e sem espaco."""
    return str(valor or "").strip().replace("`", "")


def load_contract(path):
    """Carrega o Manifest YAML como DataContract."""
    import yaml
    from src.validation.contracts import DataContract

    with open(path, encoding="utf-8") as f:
        return DataContract.from_dict(yaml.safe_load(f))


def _classification(contract) -> str:
    reg = getattr(contract, "regulatory", None)
    return (getattr(reg, "data_classification", None) or "internal").lower()


def build_ddl(contract, catalog: str, schema: str, reader_group: str,
              pii_group: str, source: str = "") -> str:
    """Monta o DDL de acesso da tabela a partir do contrato.

    Args:
        contract: DataContract ja carregado.
        catalog:  catalogo do Unity Catalog (ex.: `nimbus`).
        schema:   schema de destino (ex.: `silver`).
        reader_group: grupo que recebe leitura da tabela.
        pii_group: grupo que enxerga o valor real da coluna sensivel; os demais
            recebem o valor mascarado pela funcao.
        source: caminho do Manifest de origem, so para o cabecalho.

    Returns:
        O script SQL como texto. Nunca executa nada.
    """
    catalog, schema = _ident(catalog), _ident(schema)
    tabela = _ident(getattr(contract, "table", "")) or "tabela"
    fqn = "{}.{}.{}".format(catalog, schema, tabela)
    sensiveis_nomes = {c.lower() for c in contract.lgpd_sensitive_columns()}
    sensiveis = [(_ident(c.name), _sql_type(c.type)) for c in contract.schema
                 if c.name.lower() in sensiveis_nomes]
    classificacao = _classification(contract)
    status = getattr(contract, "manifest_status", "DRAFT")

    linhas = [
        "-- Gerado por Nimbus (src/governance/grant_emitter.py) a partir do Manifest.",
        "-- Manifest : {}".format(source or "(nao informado)"),
        "-- Tabela   : {} | versao {} | status {}".format(
            fqn, getattr(contract, "version", "?"), status),
        "-- Owner    : {}".format(getattr(contract, "owner", "") or "(nao declarado)"),
        "-- Classificacao: {}".format(classificacao),
        "--",
        "-- ESTE ARQUIVO NAO E EXECUTADO PELO PIPELINE. Revise e aplique com quem",
        "-- tem alcada de concessao de acesso no workspace.",
        "",
    ]

    if status != "VALIDATED":
        linhas += [
            "-- [ATENCAO] Manifest em {}: a classificacao abaixo ainda nao passou pelo".format(status),
            "-- Data Steward. Nao aplique este script antes da promocao para VALIDATED.",
            "",
        ]

    linhas += [
        "GRANT USE CATALOG ON CATALOG `{}` TO `{}`;".format(catalog, reader_group),
        "GRANT USE SCHEMA ON SCHEMA `{}`.`{}` TO `{}`;".format(catalog, schema, reader_group),
    ]

    if classificacao in _RESTRICTED:
        linhas += [
            "",
            "-- Classificacao '{}': SELECT amplo nao e derivavel do contrato.".format(classificacao),
            "-- O grupo abaixo exige aprovacao nominal do owner; a linha vem comentada",
            "-- de proposito, para que a concessao seja um ato consciente de quem revisa.",
            "-- GRANT SELECT ON TABLE `{}`.`{}`.`{}` TO `{}`;".format(
                catalog, schema, tabela, reader_group),
        ]
    else:
        linhas.append("GRANT SELECT ON TABLE `{}`.`{}`.`{}` TO `{}`;".format(
            catalog, schema, tabela, reader_group))

    if not sensiveis:
        linhas += ["", "-- Nenhuma coluna marcada LGPD_SENSITIVE no Manifest: sem mascara a aplicar."]
        return "\n".join(linhas) + "\n"

    linhas += [
        "",
        "-- Mascara de coluna: quem nao esta em `{}` le o valor mascarado.".format(pii_group),
        "-- Ha uma funcao por tipo porque o Unity Catalog exige que a mascara devolva",
        "-- o mesmo tipo da coluna. As {} coluna(s) abaixo vem do Manifest".format(len(sensiveis)),
        "-- (regulatory_flags: [LGPD_SENSITIVE]), nao de heuristica de nome.",
    ]
    for sql_type in sorted({t for _, t in sensiveis}):
        linhas += [
            "CREATE OR REPLACE FUNCTION `{}`.`{}`.`{}`(val {})".format(
                catalog, schema, _mask_name(sql_type), sql_type),
            "  RETURN CASE WHEN is_account_group_member('{}') THEN val ELSE {} END;".format(
                pii_group, _mask_expression(sql_type)),
        ]
    linhas.append("")
    for coluna, sql_type in sensiveis:
        linhas.append(
            "ALTER TABLE `{}`.`{}`.`{}` ALTER COLUMN `{}` SET MASK `{}`.`{}`.`{}`;".format(
                catalog, schema, tabela, coluna, catalog, schema, _mask_name(sql_type)))

    return "\n".join(linhas) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera (sem executar) o DDL de acesso derivado de um Manifest")
    parser.add_argument("--file", required=True, help="Manifest YAML de origem")
    parser.add_argument("--catalog", default=None, help="Catalogo (padrao: DATABRICKS_CATALOG)")
    parser.add_argument("--schema", default=None, help="Schema (padrao: DATABRICKS_SILVER_SCHEMA)")
    parser.add_argument("--reader-group", default="nimbus_readers",
                        help="Grupo que recebe SELECT (padrao: nimbus_readers)")
    parser.add_argument("--pii-group", default="nimbus_pii_readers",
                        help="Grupo que enxerga PII sem mascara (padrao: nimbus_pii_readers)")
    parser.add_argument("--output", default=None,
                        help="Grava o DDL no caminho informado em vez de imprimir")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    import config

    caminho = Path(args.file)
    if not caminho.is_file():
        print("[GRANTS] Manifest nao encontrado: {}".format(caminho))
        return 1

    contract = load_contract(caminho)
    ddl = build_ddl(
        contract,
        catalog      = args.catalog or getattr(config, "DATABRICKS_CATALOG", "nimbus"),
        schema       = args.schema or getattr(config, "DATABRICKS_SILVER_SCHEMA", "silver"),
        reader_group = args.reader_group,
        pii_group    = args.pii_group,
        source       = str(caminho),
    )

    if args.output:
        destino = Path(args.output)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(ddl, encoding="utf-8")
        print("[GRANTS] DDL gravado em {} (nao executado)".format(destino))
    else:
        print(ddl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
