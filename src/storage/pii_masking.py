"""
src/storage/pii_masking.py — Mascaramento de PII no arquivo de rejeitos.

A quarentena guarda a linha **original**, do jeito que chegou, porque e isso que
permite ao Steward entender por que ela foi rejeitada. O efeito colateral e que
o arquivo de rejeitos concentra dado sensivel em claro — CPF, nome e e-mail — em
uma camada que costuma ter controle de acesso mais frouxo que a Silver.

A saida aqui nao e apagar o valor: um rejeito sem valor nenhum e inutil para
triagem. E substitui-lo por um token **deterministico** derivado do valor:

    "Maria Silva"  ->  MASK:7f3a9c2b41d8

O mesmo valor gera sempre o mesmo token, entao continua sendo possivel dizer
"esta pessoa aparece em 12 linhas rejeitadas" ou cruzar com outra carga, sem que
o valor original seja legivel. E hash sem chave, entao nao e anonimizacao no
sentido juridico: vale contra leitura casual e contra vazamento do arquivo, nao
contra um atacante que ja conhece o universo de valores possiveis e faz forca
bruta. Quem precisa do valor real vai ao Bronze, que tem controle proprio.

Quais colunas sao mascaradas vem do Manifest (`regulatory_flags:
[LGPD_SENSITIVE]`), nunca de heuristica sobre o nome da coluna: o contrato e a
autoridade, e coluna sensivel nao declarada continua sendo um problema de
contrato, nao de codigo.
"""

import hashlib

import pandas as pd

MASK_PREFIX = "MASK:"
_TOKEN_LEN = 12

# Colunas de rastreio geradas pelo caster estrito (src/storage/strict_cast.py).
_REJECT_COLUMNS = "_reject_columns"
_REJECT_VALUES = "_reject_values"


def mask_value(value) -> str:
    """Token deterministico do valor; vazio continua vazio."""
    if value is None:
        return ""
    texto = str(value)
    if not texto.strip() or texto.strip() in ("nan", "None"):
        return ""
    digest = hashlib.sha256(texto.encode("utf-8")).hexdigest()[:_TOKEN_LEN]
    return MASK_PREFIX + digest


def sensitive_columns(contract) -> list:
    """Colunas marcadas LGPD_SENSITIVE no Manifest, ou lista vazia."""
    if contract is None:
        return []
    getter = getattr(contract, "lgpd_sensitive_columns", None)
    if callable(getter):
        return list(getter())
    return []


def _mask_trace(row, sensiveis_lower: set) -> str:
    """Mascara, dentro de `_reject_values`, so as posicoes de coluna sensivel.

    As duas colunas de rastreio andam juntas: `_reject_columns` traz os nomes
    separados por virgula e `_reject_values` os valores na mesma ordem,
    separados por barra vertical. Preservar a posicao importa — o Steward le as
    duas lado a lado.
    """
    nomes = [c.strip() for c in str(row.get(_REJECT_COLUMNS, "")).split(",") if c.strip()]
    valores = str(row.get(_REJECT_VALUES, "")).split("|")
    if not nomes or len(nomes) != len(valores):
        return row.get(_REJECT_VALUES, "")
    return "|".join(
        mask_value(valor) if nome.lower() in sensiveis_lower else valor
        for nome, valor in zip(nomes, valores)
    )


def mask_rejected(df: pd.DataFrame, contract) -> pd.DataFrame:
    """Devolve o DataFrame de rejeitos com as colunas sensiveis mascaradas.

    Nao altera o DataFrame recebido e nao remove nenhuma coluna: a estrutura do
    arquivo de rejeitos continua igual, so o conteudo sensivel fica ilegivel.
    """
    sensiveis = sensitive_columns(contract)
    if df is None or df.empty or not sensiveis:
        return df

    sensiveis_lower = {c.lower() for c in sensiveis}
    out = df.copy()
    atingidas = []
    for coluna in out.columns:
        if coluna.lower() in sensiveis_lower:
            out[coluna] = out[coluna].map(mask_value)
            atingidas.append(coluna)

    if _REJECT_VALUES in out.columns and _REJECT_COLUMNS in out.columns:
        out[_REJECT_VALUES] = out.apply(lambda r: _mask_trace(r, sensiveis_lower), axis=1)

    if atingidas:
        print("     [PII] quarentena mascarada em {} coluna(s): {}".format(
            len(atingidas), ", ".join(atingidas)))
    return out
