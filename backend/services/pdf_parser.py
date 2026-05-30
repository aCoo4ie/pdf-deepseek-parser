from __future__ import annotations

import base64
import re
from io import BytesIO
from typing import TypedDict

import fitz  # PyMuPDF


class PageData(TypedDict):
    page: int
    text: str
    paragraphs: list[str]


class ParseResult(TypedDict):
    total_pages: int
    pages: list[PageData]
    full_text: str
    paragraphs: list[str]
    first_page_image: str  # base64-encoded PNG of the first page


_HEADER_FOOTER_RE = re.compile(
    r"^\s*\d+\s*$"              # page numbers
    r"|^\s*https?://\S+\s*$"   # bare URLs
)

_MIN_PARAGRAPH_LEN = 30


def _clean_line(line: str) -> str:
    return line.strip()


def _split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs by blank-line boundaries, filtering noise."""
    raw_blocks = re.split(r"\n{2,}", text)
    paragraphs: list[str] = []
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        if _HEADER_FOOTER_RE.match(block):
            continue
        cleaned = " ".join(_clean_line(l) for l in block.splitlines() if _clean_line(l))
        if len(cleaned) < _MIN_PARAGRAPH_LEN:
            if paragraphs:
                paragraphs[-1] += " " + cleaned
            else:
                paragraphs.append(cleaned)
        else:
            paragraphs.append(cleaned)
    return paragraphs


def parse_pdf(file_bytes: bytes) -> ParseResult:
    """Extract text from a PDF and return structured page + paragraph data."""
    doc = fitz.open(stream=BytesIO(file_bytes), filetype="pdf")
    pages: list[PageData] = []
    all_paragraphs: list[str] = []
    full_parts: list[str] = []

    first_page_image = ""
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        paragraphs = _split_paragraphs(text)
        pages.append(
            PageData(page=page_num + 1, text=text, paragraphs=paragraphs)
        )
        all_paragraphs.extend(paragraphs)
        full_parts.append(text)

        if page_num == 0:
            mat = fitz.Matrix(1.5, 1.5)
            pix = page.get_pixmap(matrix=mat)
            first_page_image = base64.b64encode(pix.tobytes("png")).decode()

    doc.close()

    return ParseResult(
        total_pages=len(pages),
        pages=pages,
        full_text="\n\n".join(full_parts),
        paragraphs=all_paragraphs,
        first_page_image=first_page_image,
    )
