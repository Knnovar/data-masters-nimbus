"""
src/generators/writers.py — Writers de formato para a landing zone.

Implementa o padrão Strategy: cada writer recebe um DataFrame em memória
e o persiste no formato correspondente via Storage.

Hierarquia:
    BaseWriter (ABC)
    ├── CSVWriter
    ├── JSONWriter
    └── FixedWidthWriter

Uso:
    writer = WriterFactory.get("json")
    filename, content = writer.serialize(df, "tb_clientes")
    storage.write_text("bronze", filename, content)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Tipos e constantes
# ─────────────────────────────────────────────────────────────────────────────

SUPPORTED_FORMATS = ("csv", "json", "fixed")


# ─────────────────────────────────────────────────────────────────────────────
# Interface base
# ─────────────────────────────────────────────────────────────────────────────

class BaseWriter(ABC):
    """
    Interface comum para todos os writers de formato.

    Responsabilidades:
      - Receber um DataFrame puro (sem efeitos colaterais)
      - Serializar para o formato alvo
      - Retornar (filename, content_str) prontos para storage.write_text()

    Não deve:
      - Gravar arquivos diretamente em disco
      - Conhecer o Storage ou qualquer camada de persistência
    """

    @abstractmethod
    def serialize(self, df: pd.DataFrame, table_name: str) -> Tuple[str, str]:
        """
        Converte um DataFrame para string no formato alvo.

        Args:
            df: DataFrame com os dados a serializar.
            table_name: Nome da tabela (sem extensão).

        Returns:
            Tupla (filename, content) onde filename inclui a extensão correta
            e content é a string pronta para gravação.
        """

    @abstractmethod
    def extension(self) -> str:
        """Extensão do arquivo gerado (ex: '.csv')."""


# ─────────────────────────────────────────────────────────────────────────────
# Implementações
# ─────────────────────────────────────────────────────────────────────────────

class CSVWriter(BaseWriter):
    """
    Serializa DataFrame para CSV.

    Args:
        delimiter: Separador de colunas (padrão: ',').
        encoding: Encoding do arquivo gerado (padrão: 'utf-8').
    """

    def __init__(self, delimiter: str = ",", encoding: str = "utf-8") -> None:
        self._delimiter = delimiter
        self._encoding  = encoding

    def extension(self) -> str:
        return ".csv"

    def serialize(self, df: pd.DataFrame, table_name: str) -> Tuple[str, str]:
        """
        Converte DataFrame para CSV UTF-8.

        Args:
            df: DataFrame com os dados.
            table_name: Nome da tabela para compor o filename.

        Returns:
            Tupla (filename.csv, conteudo_csv).
        """
        # lineterminator=LF garante compatibilidade com DuckDB no Windows
        content  = df.to_csv(index=False, sep=self._delimiter, lineterminator='\n')
        filename = f"{table_name}{self.extension()}"
        return filename, content


class JSONWriter(BaseWriter):
    """
    Serializa DataFrame para JSON com suporte a aninhamento (nesting).

    O writer pode emular estruturas aninhadas para testar a robustez do
    normalizador json_normalize da pipeline. O campo nest_columns recebe
    um dicionário mapeando coluna_pai -> [filhas], ex:
        {"endereco": ["logradouro", "cidade", "uf"]}

    Args:
        nest_columns: Mapa de agrupamentos para aninhamento. None = flat.
        root_key: Chave raiz do JSON (ex: "data"). None = lista pura.
        indent: Indentação do JSON gerado.
    """

    def __init__(
        self,
        nest_columns: Optional[Dict[str, List[str]]] = None,
        root_key: Optional[str] = "data",
        indent: int = 2,
    ) -> None:
        self._nest_columns = nest_columns or {}
        self._root_key     = root_key
        self._indent       = indent

    def extension(self) -> str:
        return ".json"

    def serialize(self, df: pd.DataFrame, table_name: str) -> Tuple[str, str]:
        """
        Converte DataFrame para JSON, com aninhamento opcional.

        Colunas agrupadas em nest_columns são removidas do nível raiz e
        inseridas como objetos aninhados, testando a profundidade máxima
        do extractor_json.

        Args:
            df: DataFrame com os dados.
            table_name: Nome da tabela.

        Returns:
            Tupla (filename.json, conteudo_json).

        Raises:
            ValueError: Se uma coluna declarada em nest_columns não existir no df.
        """
        # Valida que as colunas de aninhamento existem
        for parent, children in self._nest_columns.items():
            missing = [c for c in children if c not in df.columns]
            if missing:
                raise ValueError(
                    f"Colunas declaradas em nest_columns nao existem no DataFrame: {missing}"
                )

        records = df.to_dict(orient="records")

        if self._nest_columns:
            records = [self._apply_nesting(r) for r in records]

        payload  = {self._root_key: records} if self._root_key else records
        content  = json.dumps(payload, ensure_ascii=False, indent=self._indent, default=str)
        filename = f"{table_name}{self.extension()}"
        return filename, content

    def _apply_nesting(self, record: dict) -> dict:
        """
        Reestrutura um dicionário flat em objeto aninhado conforme nest_columns.

        Args:
            record: Linha do DataFrame como dicionário.

        Returns:
            Dicionário com os campos agrupados em objetos aninhados.
        """
        nested = dict(record)
        for parent, children in self._nest_columns.items():
            nested[parent] = {child: nested.pop(child) for child in children if child in nested}
        return nested


class FixedWidthWriter(BaseWriter):
    """
    Serializa DataFrame para arquivo posicional (fixed-width).

    Requer um leiaute explícito definindo (coluna, largura, tipo) de cada campo.
    Campos numéricos são alinhados à direita; strings à esquerda.
    Todos os campos são truncados ou padronizados com espaços para respeitar
    exatamente a largura declarada — garantindo contagem de bytes precisa.

    Args:
        layout: Lista de tuplas (nome_coluna, largura, tipo).
                tipo aceita: 'string' | 'integer' | 'float' | 'date'.
        encoding: Encoding do arquivo gerado.
        fill_char: Caractere de preenchimento (padrão: espaço).
    """

    LayoutSpec = List[Tuple[str, int, str]]

    def __init__(
        self,
        layout: LayoutSpec,
        encoding: str = "utf-8",
        fill_char: str = " ",
    ) -> None:
        if not layout:
            raise ValueError("layout nao pode ser vazio.")
        self._layout    = layout
        self._encoding  = encoding
        self._fill_char = fill_char

    def extension(self) -> str:
        return ".txt"

    def serialize(self, df: pd.DataFrame, table_name: str) -> Tuple[str, str]:
        """
        Converte DataFrame para string posicional de largura fixa.

        Cada linha tem exatamente sum(larguras) bytes + newline.
        Campos ausentes no df são preenchidos com fill_char.

        Args:
            df: DataFrame com os dados.
            table_name: Nome da tabela.

        Returns:
            Tupla (filename.txt, conteudo_posicional).

        Raises:
            ValueError: Se alguma coluna do layout não existir no DataFrame.
        """
        missing = [col for col, _, _ in self._layout if col not in df.columns]
        if missing:
            raise ValueError(
                f"Colunas do layout ausentes no DataFrame: {missing}"
            )

        lines: List[str] = []
        for _, row in df.iterrows():
            parts: List[str] = []
            for col, width, dtype in self._layout:
                raw = row[col]
                parts.append(self._format_field(raw, width, dtype))
            lines.append("".join(parts))

        content  = "\n".join(lines) + "\n"
        filename = f"{table_name}{self.extension()}"
        return filename, content

    def layout_sidecar(self, table_name: str) -> tuple[str, str]:
        """
        Gera um arquivo sidecar JSON com os colspecs do leiaute.
        Usado por LocalStorage.read() para parsear arquivos posicionais
        sem precisar conhecer o leiaute externamente.

        Returns:
            Tupla (sidecar_filename, json_content).
        """
        names    = [col for col, _, _ in self._layout]
        start    = 0
        colspecs = []
        for _, width, _ in self._layout:
            colspecs.append([start, start + width])
            start += width
        payload  = {"names": names, "colspecs": colspecs}
        filename = f"{table_name}{self.extension()}.layout"
        return filename, json.dumps(payload)

    def _format_field(self, value: object, width: int, dtype: str) -> str:
        """
        Formata um valor para a largura exata do campo.

        Strings são alinhadas à esquerda (ljust).
        Numéricos são alinhados à direita (rjust).
        Trunca se o valor exceder a largura.

        Args:
            value: Valor do campo (qualquer tipo).
            width: Largura em caracteres do campo.
            dtype: Tipo do campo ('string', 'integer', 'float', 'date').

        Returns:
            String com exatamente `width` caracteres.
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return self._fill_char * width

        text = str(value)

        if dtype in ("integer", "float"):
            return text[:width].rjust(width, self._fill_char)
        else:
            return text[:width].ljust(width, self._fill_char)


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

class WriterFactory:
    """
    Cria instâncias de writer por formato.

    Uso:
        writer = WriterFactory.get("json")
        writer = WriterFactory.get("fixed", layout=[("id", 12, "string"), ...])

    Raises:
        ValueError: Formato não suportado.
    """

    @staticmethod
    def get(fmt: str, **kwargs) -> BaseWriter:
        """
        Retorna o writer correspondente ao formato solicitado.

        Args:
            fmt: Formato desejado. Um de: 'csv', 'json', 'fixed'.
            **kwargs: Parâmetros repassados ao writer específico.
                      Ex: nest_columns para JSONWriter,
                          layout para FixedWidthWriter.

        Returns:
            Instância de BaseWriter pronta para uso.

        Raises:
            ValueError: Se fmt não for um dos formatos suportados.
        """
        fmt = fmt.lower().strip()
        if fmt == "csv":
            return CSVWriter(**kwargs)
        if fmt == "json":
            return JSONWriter(**kwargs)
        if fmt in ("fixed", "fixed_width"):
            return FixedWidthWriter(**kwargs)
        raise ValueError(
            f"Formato nao suportado: '{fmt}'. "
            f"Opcoes validas: {', '.join(SUPPORTED_FORMATS)}"
        )
