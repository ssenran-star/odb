# Copyright (c) 2026 OceanBase.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Capture one offline CSV row as a stable, citable Source."""

from __future__ import annotations

import csv
import io
import json
from urllib.parse import quote

from pydantic import BaseModel

from powercontext.limits import MAX_SOURCE_ID_LENGTH
from powercontext.sources.definitions import AdapterSourceDefinition, SourceDefinition
from powercontext.sources.models import Source, SourceMaterialization
from powercontext.sources.projections import TEXT_EVIDENCE_PROJECTION_KEY, TextEvidence

CSV_ROW_SOURCE_NAME = "csv-row"
CSV_ROW_SOURCE_VERSION = "1"


class CSVDocumentInput(BaseModel):
    """One complete offline CSV document addressed by a caller-stable id."""

    document_id: str
    primary_key: str
    content: bytes


class CSVRowInput(BaseModel):
    """One validated data row, with header order and raw field text preserved."""

    document_id: str
    primary_key: str
    primary_key_value: str
    columns: tuple[str, ...]
    values: tuple[str, ...]


class CSVRowSource(Source):
    """Captured row evidence whose identity is the document id and primary key."""

    source_id: str
    document_id: str
    primary_key: str
    primary_key_value: str
    columns: tuple[str, ...]
    values: tuple[str, ...]


def parse_csv_document(value: CSVDocumentInput) -> tuple[CSVRowInput, ...]:
    """Parse one UTF-8 CSV document into validated rows, or fail with no partial result."""

    _validate_document_id(value.document_id)
    _validate_primary_key_name(value.primary_key)
    records = _read_csv_records(value.content)
    columns = _validate_header(records)
    primary_key_index = _primary_key_index(columns, value.primary_key)
    rows: list[CSVRowInput] = []
    seen_keys: set[str] = set()
    for record in records[1:]:
        if not record:
            continue
        if len(record) != len(columns):
            raise ValueError("CSV row field count must match the header")  # noqa: TRY003
        row = CSVRowInput(
            document_id=value.document_id,
            primary_key=value.primary_key,
            primary_key_value=record[primary_key_index],
            columns=columns,
            values=tuple(record),
        )
        _validate_row_input(row)
        if row.primary_key_value in seen_keys:
            raise ValueError("primary key value must be unique within the document")  # noqa: TRY003
        seen_keys.add(row.primary_key_value)
        rows.append(row)
    return tuple(rows)


def csv_row_source_id(document_id: str, primary_key_value: str) -> str:
    """Return the percent-encoded row identity ``csv:{document_id}:{primary_key_value}``."""

    _validate_document_id(document_id)
    _validate_primary_key_value(primary_key_value)
    source_id = f"csv:{quote(document_id, safe='')}:{quote(primary_key_value, safe='')}"
    if len(source_id) > MAX_SOURCE_ID_LENGTH:
        raise ValueError(f"source_id must not exceed {MAX_SOURCE_ID_LENGTH} characters")  # noqa: TRY003
    return source_id


class CSVRowSourceAdapter:
    """Resolve and read one captured CSV row."""

    input_class = CSVRowInput
    name = CSV_ROW_SOURCE_NAME
    source_class = CSVRowSource

    async def resolve(self, value: CSVRowInput, /) -> CSVRowSource:
        _validate_row_input(value)
        source_id = csv_row_source_id(value.document_id, value.primary_key_value)
        return CSVRowSource(
            name=source_id,
            definition_version=CSV_ROW_SOURCE_VERSION,
            materialization=SourceMaterialization.CAPTURED,
            source_id=source_id,
            document_id=value.document_id,
            primary_key=value.primary_key,
            primary_key_value=value.primary_key_value,
            columns=value.columns,
            values=value.values,
        )

    async def read(self, source: CSVRowSource, /) -> CSVRowInput:
        return CSVRowInput(
            document_id=source.document_id,
            primary_key=source.primary_key,
            primary_key_value=source.primary_key_value,
            columns=tuple(source.columns),
            values=tuple(source.values),
        )


class CSVRowTextEvidenceProjection:
    """Project one captured row as ordered JSON text evidence."""

    name = TEXT_EVIDENCE_PROJECTION_KEY.name
    version = TEXT_EVIDENCE_PROJECTION_KEY.version
    source_class = CSVRowSource
    output_class: type[BaseModel] = TextEvidence

    def project(self, source: CSVRowSource, /) -> TextEvidence:
        row = dict(zip(source.columns, source.values, strict=True))
        return TextEvidence(
            source_type=CSV_ROW_SOURCE_NAME,
            source_id=source.source_id,
            content=json.dumps(row, ensure_ascii=False, separators=(",", ":")),
            metadata={
                "document_id": source.document_id,
                "primary_key": source.primary_key,
                "primary_key_value": source.primary_key_value,
                "columns": list(source.columns),
                "row": row,
            },
        )


CSV_ROW_SOURCE_DEFINITION: SourceDefinition[CSVRowInput, CSVRowSource, CSVRowInput] = AdapterSourceDefinition(
    CSVRowSourceAdapter(),
    version=CSV_ROW_SOURCE_VERSION,
    projections=(CSVRowTextEvidenceProjection(),),
)


def _validate_document_id(document_id: str) -> None:
    if not isinstance(document_id, str) or document_id == "" or document_id != document_id.strip():
        raise ValueError(  # noqa: TRY003
            "document_id must be non-empty and must not contain leading or trailing whitespace"
        )


def _validate_primary_key_name(primary_key: str) -> None:
    if not isinstance(primary_key, str) or primary_key == "":
        raise ValueError("primary_key must be non-empty")  # noqa: TRY003


def _validate_primary_key_value(primary_key_value: str) -> None:
    if not isinstance(primary_key_value, str) or primary_key_value.strip() == "":
        raise ValueError("primary_key_value must not be blank")  # noqa: TRY003


def _validate_header(records: list[list[str]]) -> tuple[str, ...]:
    if not records or not records[0]:
        raise ValueError("CSV document must include a non-empty header")  # noqa: TRY003
    columns = tuple(records[0])
    if any(not isinstance(column, str) or column.strip() == "" for column in columns):
        raise ValueError("CSV header fields must be non-empty and not whitespace")  # noqa: TRY003
    if len(set(columns)) != len(columns):
        raise ValueError("CSV header fields must be unique")  # noqa: TRY003
    return columns


def _primary_key_index(columns: tuple[str, ...], primary_key: str) -> int:
    try:
        return columns.index(primary_key)
    except ValueError:
        raise ValueError("primary_key must exactly match a header column") from None  # noqa: TRY003


def _validate_row_input(value: CSVRowInput) -> None:
    _validate_document_id(value.document_id)
    _validate_primary_key_name(value.primary_key)
    _validate_primary_key_value(value.primary_key_value)
    columns = tuple(value.columns)
    values = tuple(value.values)
    if not columns or any(column.strip() == "" for column in columns) or len(set(columns)) != len(columns):
        raise ValueError("CSV columns must be non-empty, non-blank, and unique")  # noqa: TRY003
    if len(values) != len(columns):
        raise ValueError("CSV row field count must match the header")  # noqa: TRY003
    try:
        primary_key_index = columns.index(value.primary_key)
    except ValueError:
        raise ValueError("primary_key must exactly match a header column") from None  # noqa: TRY003
    if values[primary_key_index] != value.primary_key_value:
        raise ValueError("primary_key_value must equal the primary key field")  # noqa: TRY003
    csv_row_source_id(value.document_id, value.primary_key_value)


def _read_csv_records(content: bytes) -> list[list[str]]:
    try:
        with io.TextIOWrapper(io.BytesIO(content), encoding="utf-8-sig", newline="") as text:
            return list(
                csv.reader(
                    text,
                    delimiter=",",
                    quotechar='"',
                    doublequote=True,
                    escapechar=None,
                    strict=True,
                    skipinitialspace=False,
                )
            )
    except UnicodeDecodeError as error:
        raise ValueError("CSV document must be valid UTF-8") from error  # noqa: TRY003
    except csv.Error as error:
        raise ValueError("CSV document is malformed") from error  # noqa: TRY003


__all__ = [
    "CSV_ROW_SOURCE_DEFINITION",
    "CSVDocumentInput",
    "CSVRowInput",
    "CSVRowSource",
    "csv_row_source_id",
    "parse_csv_document",
]
