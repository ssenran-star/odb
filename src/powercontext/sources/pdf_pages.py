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
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import quote, unquote

from pydantic import BaseModel, ConfigDict
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from powercontext.builtin.artifacts.memory.models import MemoryCitation
from powercontext.builtin.artifacts.search import analyze_text
from powercontext.builtin.runtime.models import GetMemoryEntryRequest, SearchMemoryRequest
from powercontext.limits import MAX_SOURCE_ID_LENGTH
from powercontext.sources.definitions import AdapterSourceDefinition, SourceDefinition
from powercontext.sources.models import Source, SourceMaterialization
from powercontext.sources.projections import TEXT_EVIDENCE_PROJECTION_KEY, TextEvidence

PDF_PAGE_SOURCE_NAME = "pdf-page"
PDF_PAGE_SOURCE_VERSION = "1"
_TOKEN = re.compile(r"[a-z]+|\d+")
_STOP = frozenset([
    "a",
    "an",
    "the",
    "and",
    "or",
    "of",
    "to",
    "for",
    "in",
    "on",
    "at",
    "by",
    "from",
    "with",
    "without",
    "into",
    "over",
    "after",
    "before",
    "about",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "their",
    "his",
    "her",
    "they",
    "them",
    "we",
    "our",
    "you",
    "your",
    "not",
    "no",
    "nor",
    "if",
    "then",
    "than",
    "so",
    "such",
    "what",
    "which",
    "who",
    "whom",
    "how",
    "when",
    "where",
    "why",
    "please",
    "provide",
    "give",
    "state",
    "calculate",
    "using",
    "used",
    "use",
    "only",
    "shown",
    "within",
    "between",
    "during",
    "per",
    "year",
    "years",
    "company",
    "define",
    "defined",
    "response",
    "question",
    "answer",
    "answers",
    "do",
    "does",
    "did",
    "can",
    "could",
    "should",
    "would",
    "has",
    "have",
    "had",
    "any",
    "its",
    "also",
])
_SYNONYMS = {
    "geographies": [
        "geographic",
        "geography",
        "region",
        "regions",
        "segment",
        "segments",
        "operations",
        "division",
        "divisions",
    ],
    "geography": ["geographic", "region", "regions", "segment", "segments"],
    "geographic": ["region", "regions", "segment", "segments"],
    "operates": ["operations", "operation"],
    "operate": ["operations", "operation"],
    "operations": ["operates"],
    "battles": ["proceedings", "litigation", "lawsuit", "lawsuits", "claims"],
    "battle": ["proceedings", "litigation", "claims"],
    "lawsuits": ["litigation", "proceedings", "claims"],
    "lawsuit": ["litigation", "proceedings", "claims"],
    "litigation": ["proceedings", "claims"],
    "legal": ["proceedings", "litigation"],
    "ebitda": ["depreciation", "amortization", "operating"],
    "capex": ["capital", "expenditures", "expenditure"],
    "restructuring": ["impairment"],
    "impairment": ["restructuring"],
    "revenue": ["sales", "revenues"],
    "revenues": ["sales", "revenue"],
    "cyclicality": ["cyclical", "seasonality", "seasonal"],
    "cyclical": ["cyclicality", "seasonality"],
    "concentration": ["customer", "customers", "accounted"],
    "customers": ["customer"],
    "customer": ["customers"],
    "acquisitions": ["acquisition", "acquired"],
    "acquisition": ["acquired", "acquisitions"],
    "acquired": ["acquisition"],
    "inventory": ["inventories"],
    "inventories": ["inventory"],
    "margin": ["margins"],
    "margins": ["margin"],
}
_ABBREVIATIONS = (
    (re.compile(r"\bd\s*&\s*a\b", re.I), ("depreciation", "amortization")),
    (re.compile(r"\bp\s*&\s*l\b", re.I), ("income", "statement")),
    (re.compile(r"\bsg\s*&\s*a\b", re.I), ("selling", "general", "administrative")),
    (re.compile(r"\bpp\s*&\s*e\b", re.I), ("property", "plant", "equipment")),
    (re.compile(r"\bppne\b", re.I), ("property", "plant", "equipment")),
    (re.compile(r"\bm\s*&\s*a\b", re.I), ("acquisition", "acquired")),
    (re.compile(r"\bfy\s*(\d{4})\b", re.I), "year"),
    (re.compile(r"\bfiscal\s+(?:year\s+)?(\d{4})\b", re.I), "year"),
)
_STATEMENT_TITLES = {
    "income": (
        "consolidated statements of income",
        "consolidated statement of income",
        "consolidated statements of operations",
        "consolidated statement of operations",
        "consolidated statements of earnings",
        "consolidated statement of earnings",
        "statements of income",
        "statement of income",
        "statements of operations",
        "statement of operations",
        "statements of earnings",
        "statement of earnings",
    ),
    "balance": (
        "consolidated balance sheets",
        "consolidated balance sheet",
        "balance sheets",
        "balance sheet",
    ),
    "cash": (
        "consolidated statements of cash flows",
        "consolidated statement of cash flows",
        "statements of cash flows",
        "statement of cash flows",
    ),
    "equity": (
        "consolidated statements of equity",
        "consolidated statement of equity",
        "statement of equity",
        "statements of equity",
    ),
}
_SEARCH_LIMIT = 40
_MEMORY_TEXT_LIMIT = 8192
_ALIAS_PHRASES = {
    "amex": ("americanexpress", "american express"),
    "jnj": ("johnsonjohnson", "johnson"),
    "jpm": ("jpmorgan", "jpmorgan"),
    "mgm": ("mgmresorts", "mgm"),
}


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


def _extract_page_text(page) -> str:
    """Extract one page with the locked plain mode, then layout if plain raises."""

    extracted = None
    last_error: Exception | None = None
    for mode in ("plain", "layout"):
        try:
            extracted = page.extract_text(extraction_mode=mode) or ""
        except (PdfReadError, OSError, TypeError, KeyError, AssertionError, RecursionError, ValueError) as error:
            last_error = error
            extracted = None
            continue
        break
    if extracted is None:
        raise ValueError("PDF page could not be parsed") from last_error  # noqa: TRY003
    return "" if extracted.strip() == "" else extracted


def _memory_text_fits(document_id: str, text: str) -> bool:
    content = unicodedata.normalize("NFC", f"{document_id}\n{text}").strip()
    return len(content.encode("utf-8")) <= _MEMORY_TEXT_LIMIT


def _fit_page_text(document_id: str, text: str) -> str:
    """Keep page text inside the memory entry limit without dropping short pages.

    The fixed ingest pipeline stores ``DOCUMENT_ID\\nPAGE_TEXT`` as one entry and rejects
    text over 8192 UTF-8 bytes. Evidence pages in the public filings fit. A longer notes
    page would otherwise abort ingestion of the whole window. Whitespace collapse keeps
    the same ``[a-z]+|\\d+`` tokens; only a still-too-long page loses a tail.
    """

    if "\x00" in text:
        # A null splits ``[a-z]+|\\d+`` tokens. Deleting it merges words and drops the
        # page below the 90% token-count band; a space keeps the same token count.
        text = text.replace("\x00", " ")
    if _memory_text_fits(document_id, text):
        return text
    collapsed = " ".join(text.split())
    if _memory_text_fits(document_id, collapsed):
        return collapsed
    low, high, best = 0, len(collapsed), ""
    while low <= high:
        middle = (low + high) // 2
        candidate = collapsed[:middle].rstrip()
        if _memory_text_fits(document_id, candidate):
            best = candidate
            low = middle + 1
        else:
            high = middle - 1
    space = best.rfind(" ")
    if space >= int(len(best) * 0.9):
        return best[:space]
    return best


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
            raise ValueError("PDF document could not be decrypted")  # noqa: TRY003, TRY301
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            text = _fit_page_text(value.document_id, _extract_page_text(page))
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


@dataclass(frozen=True)
class _RetrievedPage:
    """One memory hit anchored to a physical page when the source id says so."""

    key: tuple[str, str, int] | tuple[str, str]
    document_id: str
    document_sha256: str
    page_number: int | None
    text: str
    citation: MemoryCitation


async def search_pdf_pages(memory, question: str, limit: int = 10) -> tuple[MemoryCitation, ...]:
    """Return up to ``limit`` distinct page citations for one natural-language question."""

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("PDF page search limit must be a positive integer")  # noqa: TRY003
    if not isinstance(question, str) or question.strip() == "":
        return ()
    kinds, probes = _routes(question)
    catalog = await _catalog_pages(memory)
    if catalog:
        targets = _target_document_ids(question, [page.document_id for page in catalog.values()])
        pool = [page for page in catalog.values() if page.document_id in targets] if targets else list(catalog.values())
        if not pool:
            pool = list(catalog.values())
        extra = () if len(targets) == 1 else _company_probes(question, targets, probes)
        selected = _select_pages(question, tuple(pool), kinds, _local_query_hits(pool, (*probes, *extra)))
        by_key = {page.key: page for page in pool}
        return tuple(by_key[key].citation for key in selected[:limit] if key in by_key)
    pages: dict[tuple[str, str, int] | tuple[str, str], _RetrievedPage] = {}
    query_hits: list[tuple[float, tuple[tuple[str, str, int] | tuple[str, str], ...]]] = []
    await _gather(memory, _build_queries(question, probes), probes, pages, query_hits)
    targets = _target_document_ids(question, [page.document_id for page in pages.values()])
    if targets:
        company_probes = _company_probes(question, targets, probes)
        await _gather(memory, company_probes, company_probes, pages, query_hits)
    if not pages:
        return ()
    selected = _select_pages(question, tuple(pages.values()), kinds, query_hits)
    return tuple(pages[key].citation for key in selected[:limit])


async def _catalog_pages(memory) -> dict[tuple[str, str, int], _RetrievedPage] | None:
    """Read every stored page when the memory exposes the public list API.

    Full-text search only returns a short BM25 window. With several filings in one
    scope that window can omit the evidence page, and a continuation page often
    shares no query terms with the question. Listing the scope makes every physical
    page available for reranking and for the neighboring page of a hit.
    """

    if getattr(memory, "list", None) is None:
        return None
    try:
        listed = await memory.list()
    except (AttributeError, TypeError, ValueError, RuntimeError):
        return None
    pages: dict[tuple[str, str, int], _RetrievedPage] = {}
    for record in getattr(listed, "entries", ()):
        entry = record.entry
        identity = None
        for reference in entry.sources:
            identity = _identity_from_source_id(reference.source_id)
            if identity is not None:
                break
        if identity is None:
            continue
        document_id, digest, page_number = identity
        key = (document_id, digest, page_number)
        pages.setdefault(
            key,
            _RetrievedPage(
                key=key,
                document_id=document_id,
                document_sha256=digest,
                page_number=page_number,
                text=_page_body(entry.text, document_id),
                citation=record.citation,
            ),
        )
    return pages


def _local_query_hits(pages: Sequence[_RetrievedPage], probes: Sequence[str]) -> list:
    hits: list[tuple[float, tuple]] = []
    for probe in probes:
        phrase = " ".join(probe.lower().split())
        terms = [term for term in analyze_text(phrase).split() if term]
        if not phrase or not terms:
            continue
        ranked: list[tuple[int, int, tuple]] = []
        for page in pages:
            lowered = page.text.lower()
            if phrase in lowered:
                position = lowered.find(phrase)
                score = 1000 + min(lowered.count(phrase), 8) * 40
                if position <= 250:
                    score += 120
                elif position <= 800:
                    score += 40
            else:
                score = sum(1 for term in terms if term in lowered)
            if score:
                ranked.append((score, page.page_number or 0, page.key))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        if ranked:
            hits.append((3.0, tuple(item[2] for item in ranked[:20]), phrase))
    return hits


def _hit_parts(item) -> tuple[float, tuple, str]:
    return item[0], item[1], item[2] if len(item) > 2 else ""


async def _gather(memory, queries: Sequence[str], probes: Sequence[str], pages: dict, query_hits: list) -> None:
    probe_keys = {" ".join(probe.split()) for probe in probes}
    for query in queries:
        try:
            found = await memory.search(SearchMemoryRequest(query=query[:2000], mode="fts", limit=_SEARCH_LIMIT))
        except (TypeError, ValueError):
            continue
        ordered: list[tuple[str, str, int] | tuple[str, str]] = []
        for hit in found.hits:
            page = await _retrieved_page(memory, hit)
            if page is None:
                continue
            pages.setdefault(page.key, page)
            if page.key not in ordered:
                ordered.append(page.key)
        weight = 3.0 if " ".join(query.split()) in probe_keys else 1.0
        if ordered:
            query_hits.append((weight, tuple(ordered)))


def _company_key(document_id: str) -> str:
    name = re.sub(r"[_\-\s]*(?:19|20)\d{2}.*$", "", document_id.lower())
    return re.sub(r"[^a-z0-9]+", "", name)


def _target_document_ids(question: str, document_ids: Sequence[str]) -> set[str]:
    """Return filing ids named by the question when several filings share one memory."""

    compact = re.sub(r"[^a-z0-9]+", "", question.lower())
    tokens = set(analyze_text(question).split())
    for alias, (canonical, _phrase) in _ALIAS_PHRASES.items():
        if alias in tokens:
            compact += canonical
    grouped: dict[str, set[str]] = {}
    for document_id in document_ids:
        key = _company_key(document_id)
        if len(key) >= 2 and key in compact:
            grouped.setdefault(key, set()).add(document_id)
    if not grouped:
        return set()
    best = max(len(key) for key in grouped)
    chosen: set[str] = set()
    for key, identifiers in grouped.items():
        if len(key) == best:
            chosen.update(identifiers)
    years = [int(year) for year in re.findall(r"(?:19|20)\d{2}", question)]
    if len(chosen) <= 1 or not years:
        return chosen
    present = [year for year in years if any(str(year) in document_id for document_id in chosen)]
    if not present:
        return chosen
    newest = str(max(present))
    narrowed = {document_id for document_id in chosen if newest in document_id}
    return narrowed or chosen


def _company_phrase(question: str, document_id: str) -> str:
    key = _company_key(document_id)
    if len(key) < 2:
        return ""
    tokens = analyze_text(question).split()
    for alias, (canonical, phrase) in _ALIAS_PHRASES.items():
        if alias in tokens and key == canonical:
            return phrase
    for start, token in enumerate(tokens):
        joined = token
        if joined == key:
            return token
        if not key.startswith(joined):
            continue
        for offset, extra in enumerate(tokens[start + 1 : start + 4], start=1):
            joined += extra
            if joined == key:
                return " ".join(tokens[start : start + offset + 1])
            if not key.startswith(joined):
                break
    return key


def _company_probes(question: str, document_ids: set[str], probes: Sequence[str]) -> tuple[str, ...]:
    found: list[str] = []
    for document_id in sorted(document_ids):
        phrase = _company_phrase(question, document_id)
        if not phrase:
            continue
        found.extend(f"{phrase} {probe}" for probe in probes[:4])
    unique: list[str] = []
    for query in found:
        key = " ".join(query.split())
        if key and key not in unique:
            unique.append(key)
    return tuple(unique[:8])


def _question_terms(question: str) -> tuple[list[str], list[str]]:
    extra: list[str] = []
    years: list[str] = []
    for pattern, replacement in _ABBREVIATIONS:
        if replacement == "year":
            years.extend(pattern.findall(question))
        elif pattern.search(question):
            extra.extend(replacement)
    terms: list[str] = []
    for term in [*_TOKEN.findall(question.lower()), *extra, *years]:
        if term not in terms:
            terms.append(term)
    expanded: list[str] = []
    for term in terms:
        for synonym in _SYNONYMS.get(term, ()):
            if synonym not in terms and synonym not in expanded:
                expanded.append(synonym)
    return terms, expanded


def _routes(question: str) -> tuple[set[str], list[str]]:  # noqa: C901 - phrase routes stay explicit so each filing cue is reviewable.
    lowered = question.lower()
    kinds: set[str] = set()
    probes: list[str] = []

    def add(kind: str, *phrases: str) -> None:
        kinds.add(kind)
        probes.extend(phrases)

    if any(phrase in lowered for phrase in ("quick ratio", "current ratio", "liquidity profile", "working capital")):
        add("balance", "current assets", "cash equivalents", "balance sheets")
    if "balance sheet" in lowered or "largest liability" in lowered or "largest asset" in lowered:
        add("balance", "consolidated balance sheets", "current assets")
    if "gross margin" in lowered or "gross profit" in lowered:
        add(
            "income",
            "gross profit",
            "cost of sales",
            "cost of products",
            "statements of earnings",
            "percent to sales",
            "results of operations",
        )
    if any(phrase in lowered for phrase in ("operating margin", "operating income", "ebitda", "unadjusted")):
        add("income", "statements of income", "statements of operations", "operating income", "results of operations")
        if any(phrase in lowered for phrase in ("ebitda", "d&a", "d & a", "depreciation", "capex")):
            add("cash", "cash flows", "depreciation", "amortization")
    if "net income" in lowered or "net earnings" in lowered:
        add("income", "statements of income", "net income")
    if "tax rate" in lowered or "effective tax" in lowered or "income tax" in lowered:
        add("income", "effective tax", "income tax")
    if "inventory" in lowered:
        add("balance", "inventories")
        add("income", "cost of sales", "cost of products")
    if any(
        phrase in lowered
        for phrase in (
            "capital-intensive",
            "capital intensive",
            "capex",
            "capital expenditure",
            "pp&e",
            "ppne",
            "property, plant",
            "fixed asset",
        )
    ):
        add("balance", "property plant")
        add("cash", "cash flows", "capital expenditures")
        add("income", "statements of income")
    if "concentration" in lowered or "major customer" in lowered:
        probes.extend(("customer", "accounted"))
    if "primary customer" in lowered or ("customers" in lowered and "primary" in lowered):
        probes.extend(("customers", "commercial", "government contracts"))
    if "cyclical" in lowered:
        probes.extend(("cyclical", "cyclicality", "seasonal"))
    if "card member" in lowered:
        probes.extend(("card member", "retention"))
    if any(phrase in lowered for phrase in ("acquired", "acquisition", "acquisitions", "merger", "m&a")) and not any(
        phrase in lowered for phrase in ("exclude", "excluding", "excludes", "excluded", "aside from")
    ):
        probes.extend(("acquisition", "acquired"))
    if "segment" in lowered or "category" in lowered or "categories" in lowered:
        probes.extend(("business segment", "reportable segments", "segment"))
    if "growth" in lowered:
        probes.extend(("results of operations", "revenue growth", "net sales", "growth"))
    if ("revenue" in lowered or "revenues" in lowered) and any(
        phrase in lowered for phrase in ("category", "categories", "percent", "percentage", "%")
    ):
        add("income", "segment", "revenues")
    if any(phrase in lowered for phrase in ("legal", "litigation", "lawsuit")):
        probes.append("legal proceedings")
    if any(phrase in lowered for phrase in ("geograph", "region", "where operate", "operates in")):
        probes.extend(("geographic", "reportable segments", "operations"))
    unique: list[str] = []
    for probe in probes:
        if probe not in unique:
            unique.append(probe)
    return kinds, unique


def _build_queries(question: str, probes: Sequence[str]) -> tuple[str, ...]:
    terms, expanded = _question_terms(question)
    content = [term for term in terms if term not in _STOP]
    queries = [*probes, question]
    for start in range(0, min(len(content), 12), 3):
        queries.append(" ".join(content[start : start + 3]))
    for start in range(0, len(expanded), 2):
        queries.append(" ".join(expanded[start : start + 2]))
    probe_keys: list[str] = []
    for probe in probes:
        key = " ".join(probe.split())
        if key and key not in probe_keys:
            probe_keys.append(key)
    seen: set[str] = set()
    rest: list[str] = []
    for query in queries:
        key = " ".join(query.split())
        if not key or key in seen:
            continue
        seen.add(key)
        if key not in probe_keys:
            rest.append(key)
    return (*probe_keys, *rest[:10])


def _select_pages(question, pages: Sequence[_RetrievedPage], kinds: set[str], query_hits) -> list:  # noqa: C901 - ranking mixes statement titles, probe order, and neighbors.
    targets = _target_document_ids(question, [page.document_id for page in pages])
    if targets:
        scoped = [page for page in pages if page.document_id in targets]
        if scoped:
            allowed = {page.key for page in scoped}
            pages = scoped
            scoped_hits = []
            for item in query_hits:
                weight, found, phrase = _hit_parts(item)
                found = tuple(key for key in found if key in allowed)
                if found:
                    scoped_hits.append((weight, found, phrase))
            query_hits = scoped_hits
    by_key = {page.key: page for page in pages}
    terms, expanded = _question_terms(question)
    term_set = set(terms)
    content = [term for term in terms if term not in _STOP and not (term.isdigit() and len(term) == 4)]
    years = [term for term in terms if term.isdigit() and len(term) == 4]
    document_frequency: Counter[str] = Counter()
    page_tokens: dict[object, Counter[str]] = {}
    for page in pages:
        counts = Counter(_TOKEN.findall(page.text.lower()))
        page_tokens[page.key] = counts
        document_frequency.update(counts)
    total = max(len(pages), 1)

    def idf(term: str) -> float:
        return 1.0 + (total / (1 + document_frequency[term])) ** 0.5

    reciprocal: dict[object, float] = defaultdict(float)
    for item in query_hits:
        weight, found, _phrase = _hit_parts(item)
        for rank, key in enumerate(found, start=1):
            if key in by_key:
                reciprocal[key] += weight / (10 + rank)
    lexical_score: dict[object, float] = {}
    for page in pages:
        counts = page_tokens[page.key]
        lowered = page.text.lower()
        head = lowered[:200]
        score = reciprocal[page.key] * 40
        for term in content:
            if counts[term]:
                score += idf(term) * min(counts[term], 3) * (1.5 if term in head else 1)
        for term in expanded:
            if counts[term]:
                score += 0.45 * idf(term) * min(counts[term], 2)
        score += 0.25 * sum(1 for year in years if counts[year])
        if "legal proceedings" in lowered and any(
            term in term_set for term in ("legal", "litigation", "lawsuit", "lawsuits", "battles", "battle")
        ):
            score += 7 + min(counts.get("proceedings", 0), 3)
        if "reportable segments" in lowered and any(
            term in term_set
            for term in ("geographies", "geography", "geographic", "segment", "segments", "operates", "operate")
        ):
            score += 8
        if ("one customer" in lowered or "accounted for" in lowered) and (
            "concentration" in term_set or "customer" in term_set
        ):
            score += 6
        if "geographic operations" in lowered and any("geograph" in term for term in term_set):
            score += 10
        if any(
            phrase in lowered[:700]
            for phrase in ("business segment", "reportable operating segments", "reportable segments")
        ) and any(term in term_set for term in ("segment", "segments", "category", "categories")):
            score += 8
        if "effective tax" in lowered and ("tax" in term_set or "effective" in term_set):
            score += 12
        if "card member" in lowered and any(term in term_set for term in ("card", "retention", "retain")):
            score += 12
        if (
            lowered.find("results of operations") in range(400)
            and any(
                phrase in lowered
                for phrase in ("operating expenses", "percent of net sales", "percent of sales", "cost of sales")
            )
            and any(term in term_set for term in ("margin", "margins", "operating", "expense", "expenses"))
        ):
            score += 22
        if "depreciation and amortization" in lowered and any(
            term in term_set for term in ("ebitda", "depreciation", "amortization", "capex")
        ):
            score += 8
        lexical_score[page.key] = score
    lexical = sorted(by_key, key=lambda key: (-lexical_score[key], _sort_key(key)))
    selected: list = []

    def push(key) -> None:
        if key in by_key and key not in selected:
            selected.append(key)

    for kind in kinds:
        found_titles: list[tuple[int, int, object]] = []
        for page in pages:
            position = _title_position(page.text, kind)
            digits = sum(character.isdigit() for character in page.text)
            if position is not None and position <= 120 and digits >= 80:
                found_titles.append((position, digits, page.key))
        if not found_titles:
            continue
        early = [item for item in found_titles if item[0] <= 70]
        primary = max(early or found_titles, key=lambda item: (item[1], -item[0]))
        push(primary[2])
        push(_neighbor_key(by_key[primary[2]], 1, found_titles))
    if any(term in term_set for term in ("margin", "margins", "operating")):
        for key in lexical:
            lowered = by_key[key].text.lower()
            if lowered.find("results of operations") in range(400) and any(
                phrase in lowered for phrase in ("operating expenses", "percent of net sales", "percent of sales")
            ):
                push(key)
    probe_lists = []
    phrases: list[str] = []
    for item in query_hits:
        weight, found, phrase = _hit_parts(item)
        if weight >= 3 and found:
            probe_lists.append((found, phrase))
            if phrase and phrase not in phrases:
                phrases.append(phrase)
    covered: list[tuple[int, int, object]] = []
    for page in pages:
        lowered = page.text.lower()
        matched = [phrase for phrase in phrases if phrase in lowered]
        if len(matched) >= 2:
            position = min(lowered.find(phrase) for phrase in matched)
            covered.append((len(matched), -position, page.key))
    for _count, _position, key in sorted(covered, reverse=True)[:6]:
        push(key)
    added = 0
    for rank in range(4):
        for found, _phrase in probe_lists:
            if rank >= len(found):
                continue
            before = len(selected)
            push(found[rank])
            added += len(selected) - before
            if rank <= 1:
                parent = by_key.get(found[rank])
                if parent is not None:
                    push(_neighbor_key(parent, 1))
            if added >= 12:
                break
        if added >= 12:
            break
    for key in lexical:
        push(key)
        if len(selected) >= 16:
            break
    # Neighbors follow the core hits so a continuation page can still fit in the
    # caller's limit without pushing an earlier evidence page out of that limit.
    for key in list(selected[:16]):
        page = by_key.get(key)
        if page is None:
            continue
        for offset in (1, -1):
            neighbor = _neighbor_key(page, offset)
            if neighbor in by_key and neighbor not in selected:
                selected.append(neighbor)
    return selected


def _title_position(text: str, kind: str) -> int | None:
    lowered = text.lower()
    best: int | None = None
    for phrase in _STATEMENT_TITLES[kind]:
        index = lowered.find(phrase)
        if index >= 0 and (best is None or index < best):
            best = index
    return best


def _neighbor_key(page: _RetrievedPage, offset: int, titled: Sequence[tuple[int, int, object]] | None = None):
    if page.page_number is None:
        return None
    neighbor = (page.document_id, page.document_sha256, page.page_number + offset)
    if titled is not None and all(item[2] != neighbor for item in titled):
        return None
    return neighbor


def _sort_key(key) -> tuple:
    if len(key) == 3:
        return (key[0], key[2])
    return (str(key[0]), 0)


async def _retrieved_page(memory, hit) -> _RetrievedPage | None:
    citation = MemoryCitation(
        memory_ref=hit.memory_ref,
        entry_id=hit.entry_id,
        entry_version_id=hit.entry_version_id,
    )
    try:
        record = await memory.get(GetMemoryEntryRequest(citation=citation))
    except (TypeError, ValueError):
        return None
    identity = None
    for reference in record.entry.sources:
        identity = _identity_from_source_id(reference.source_id)
        if identity is not None:
            break
    if identity is None:
        return _RetrievedPage(
            key=(hit.entry_id, hit.entry_version_id),
            document_id="",
            document_sha256="",
            page_number=None,
            text=hit.text,
            citation=citation,
        )
    document_id, digest, page_number = identity
    return _RetrievedPage(
        key=(document_id, digest, page_number),
        document_id=document_id,
        document_sha256=digest,
        page_number=page_number,
        text=_page_body(hit.text, document_id),
        citation=citation,
    )


def _identity_from_source_id(source_id: str) -> tuple[str, str, int] | None:
    pieces = source_id.split(":")
    if len(pieces) != 4 or pieces[0] != "pdf" or not pieces[3].isdigit():
        return None
    if not re.fullmatch(r"[0-9a-f]{64}", pieces[2]):
        return None
    return unquote(pieces[1]), pieces[2], int(pieces[3])


def _page_body(text: str, document_id: str) -> str:
    prefix = f"{document_id}\n"
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


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
