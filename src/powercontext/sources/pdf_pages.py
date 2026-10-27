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

"""Parse a complete PDF into page Sources and retrieve evidence pages from Memory."""

from __future__ import annotations

import hashlib
import io
import re
from collections import defaultdict
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from powercontext.builtin.artifacts.memory.models import MemoryCitation
from powercontext.builtin.runtime.models import SearchMemoryRequest
from powercontext.limits import MAX_SOURCE_ID_LENGTH
from powercontext.sources.definitions import AdapterSourceDefinition, SourceDefinition
from powercontext.sources.models import Source, SourceMaterialization
from powercontext.sources.projections import TEXT_EVIDENCE_PROJECTION_KEY, TextEvidence

PDF_PAGE_SOURCE_NAME = "pdf-page"
PDF_PAGE_SOURCE_VERSION = "1"
_TOKEN = re.compile(r"[a-z]+|\d+")
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9&/-]{2,}")
_STOP = frozenset(
    """
    a an the and or of to for in on at by from with without into over after before about as is are was were be been
    being that this these those it its their his her they them we our you your not no nor if then than so such what
    which who whom how when where why please provide give state calculate using used use only shown within between
    during per FY fy year years company report reported reporting define defined response question answer answers
    """.split()
)


class PDFDocumentInput(BaseModel):
    """One original PDF addressed by a caller-stable document id."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    content: bytes


class PDFPageInput(BaseModel):
    """Extracted text for one physical PDF page."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_sha256: str
    page_number: int
    text: str


class PDFPageSource(Source):
    """Captured page whose identity is the document, digest, and physical page."""

    source_id: str
    document_id: str
    document_sha256: str
    page_number: int
    text: str


def parse_pdf_document(value: PDFDocumentInput) -> tuple[PDFPageInput, ...]:
    """Return every physical page in order, or fail without a partial result."""

    _validate_document_id(value.document_id)
    if not isinstance(value.content, bytes | bytearray) or not value.content:
        raise ValueError("PDF document is empty or unreadable")  # noqa: TRY003
    content = bytes(value.content)
    digest = hashlib.sha256(content).hexdigest()
    try:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise ValueError("PDF document could not be decrypted")  # noqa: TRY003
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            extracted = page.extract_text(extraction_mode="plain") or ""
            text = "" if extracted.strip() == "" else extracted
            pages.append(
                PDFPageInput(
                    document_id=value.document_id,
                    document_sha256=digest,
                    page_number=number,
                    text=text,
                )
            )
    except ValueError:
        raise
    except (PdfReadError, OSError, TypeError, KeyError, AssertionError, RecursionError) as error:
        raise ValueError("PDF document could not be parsed") from error  # noqa: TRY003
    except Exception as error:
        raise ValueError("PDF document could not be parsed") from error  # noqa: TRY003
    if not pages:
        raise ValueError("PDF document does not contain a page")  # noqa: TRY003
    return tuple(pages)


def pdf_page_source_id(document_id: str, document_sha256: str, page_number: int) -> str:
    """Return the stable page identity for one document revision and physical page."""

    _validate_document_id(document_id)
    source_id = f"pdf:{quote(document_id, safe='')}:{document_sha256}:{page_number}"
    if len(source_id) <= MAX_SOURCE_ID_LENGTH:
        return source_id
    digest = hashlib.sha256(f"{document_id}\0{document_sha256}\0{page_number}".encode()).hexdigest()
    return f"pdf:{digest}"


class PDFPageSourceAdapter:
    """Resolve and read one captured PDF page."""

    input_class = PDFPageInput
    name = PDF_PAGE_SOURCE_NAME
    source_class = PDFPageSource

    async def resolve(self, value: PDFPageInput, /) -> PDFPageSource:
        _validate_page(value)
        source_id = pdf_page_source_id(value.document_id, value.document_sha256, value.page_number)
        return PDFPageSource(
            name=source_id,
            definition_version=PDF_PAGE_SOURCE_VERSION,
            materialization=SourceMaterialization.CAPTURED,
            source_id=source_id,
            document_id=value.document_id,
            document_sha256=value.document_sha256,
            page_number=value.page_number,
            text=value.text,
        )

    async def read(self, source: PDFPageSource, /) -> PDFPageInput:
        return PDFPageInput(
            document_id=source.document_id,
            document_sha256=source.document_sha256,
            page_number=source.page_number,
            text=source.text,
        )


class PDFPageTextEvidenceProjection:
    """Project one page as document id plus extracted page text."""

    name = TEXT_EVIDENCE_PROJECTION_KEY.name
    version = TEXT_EVIDENCE_PROJECTION_KEY.version
    source_class = PDFPageSource
    output_class: type[BaseModel] = TextEvidence

    def project(self, source: PDFPageSource, /) -> TextEvidence:
        return TextEvidence(
            source_type=PDF_PAGE_SOURCE_NAME,
            source_id=source.source_id,
            content=f"{source.document_id}\n{source.text}",
            metadata={
                "document_id": source.document_id,
                "document_sha256": source.document_sha256,
                "page_number": source.page_number,
            },
        )


PDF_PAGE_SOURCE_DEFINITION: SourceDefinition[PDFPageInput, PDFPageSource, PDFPageInput] = AdapterSourceDefinition(
    PDFPageSourceAdapter(),
    version=PDF_PAGE_SOURCE_VERSION,
    projections=(PDFPageTextEvidenceProjection(),),
)


async def search_pdf_pages(memory, question: str, limit: int = 10) -> tuple[MemoryCitation, ...]:
    """Return up to ``limit`` distinct page citations for one natural-language question."""

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("PDF page search limit must be a positive integer")  # noqa: TRY003
    ranked: dict[tuple[str, str], tuple[float, object]] = {}
    pool = max(limit, 40)
    for query in _queries(question):
        page = await memory.search(SearchMemoryRequest(query=query[:2000], mode="fts", limit=pool))
        for rank, hit in enumerate(page.hits):
            key = (hit.entry_id, hit.entry_version_id)
            score = _overlap(question, hit.text) + (1.0 / (rank + 8))
            current = ranked.get(key)
            if current is None or score > current[0]:
                ranked[key] = (score, hit)
    ordered = sorted(ranked.values(), key=lambda item: (-item[0], item[1].entry_id))
    citations: list[MemoryCitation] = []
    seen: set[str] = set()
    for _score, hit in ordered:
        if hit.entry_id in seen:
            continue
        seen.add(hit.entry_id)
        citations.append(
            MemoryCitation(
                memory_ref=hit.memory_ref,
                entry_id=hit.entry_id,
                entry_version_id=hit.entry_version_id,
            )
        )
        if len(citations) == limit:
            break
    return tuple(citations)


def _queries(question: str) -> tuple[str, ...]:
    queries = [question]
    numbers = _NUMBER.findall(question)
    words = [word for word in _WORD.findall(question) if word.casefold() not in _STOP and len(word) > 3]
    if numbers:
        queries.append(" ".join(numbers[:12]))
    unique_words: list[str] = []
    for word in words:
        if word.casefold() not in {item.casefold() for item in unique_words}:
            unique_words.append(word)
    for start in range(0, min(len(unique_words), 16), 4):
        group = unique_words[start : start + 4]
        if group:
            queries.append(" ".join(group))
    if numbers and unique_words:
        queries.append(" ".join([*unique_words[:6], *numbers[:6]]))
    deduped: list[str] = []
    for query in queries:
        normalized = " ".join(query.split())
        if normalized and normalized not in deduped:
            deduped.append(normalized)
    return tuple(deduped[:12])


def _overlap(question: str, text: str) -> float:
    query_counts: dict[str, int] = defaultdict(int)
    for token in _TOKEN.findall(question.casefold()):
        query_counts[token] += 3 if token.isdigit() or token not in _STOP else 0.25
    if not query_counts:
        return 0.0
    page_counts: dict[str, int] = defaultdict(int)
    for token in _TOKEN.findall(text.casefold()):
        page_counts[token] += 1
    score = 0.0
    for token, weight in query_counts.items():
        if page_counts[token]:
            score += weight * min(page_counts[token], 3)
    return score


def _validate_document_id(document_id: str) -> None:
    if not isinstance(document_id, str) or document_id.strip() == "":
        raise ValueError("document_id must not be empty or whitespace")  # noqa: TRY003


def _validate_page(value: PDFPageInput) -> None:
    _validate_document_id(value.document_id)
    if not isinstance(value.page_number, int) or isinstance(value.page_number, bool) or value.page_number < 1:
        raise ValueError("page_number must be a positive integer")  # noqa: TRY003
    if not re.fullmatch(r"[0-9a-f]{64}", value.document_sha256):
        raise ValueError("document_sha256 must be a lowercase SHA-256 digest")  # noqa: TRY003


__all__ = [
    "PDF_PAGE_SOURCE_DEFINITION",
    "PDFDocumentInput",
    "PDFPageInput",
    "PDFPageSource",
    "parse_pdf_document",
    "pdf_page_source_id",
    "search_pdf_pages",
]
