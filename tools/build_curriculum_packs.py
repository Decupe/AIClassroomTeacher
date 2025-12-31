import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

OUT_DIR = Path("curriculum_packs")
CACHE_DIR = Path(".cache/curriculum_sources")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENT = "AIClassroomTeacher/0.1 (educational prototype; contact: local)"
TIMEOUT = 30


@dataclass
class Source:
    pack_id: str                 # e.g. "KS3_Maths"
    year_band: str               # e.g. "KS3 (Year 7-9)"
    subject: str                 # e.g. "Maths"
    url: str
    source_type: str             # "html" or "pdf"
    publisher: str               # e.g. "GOV.UK / Department for Education"
    licence: str                 # e.g. "Open Government Licence v3.0"


# ---- Configure your curriculum sources here ----
SOURCES: List[Source] = [
    # KS3 (Year 7–9) maths / english / science PDFs (official)
    Source(
        pack_id="KS3_Maths",
        year_band="KS3 (Year 7-9)",
        subject="Maths",
        url="https://assets.publishing.service.gov.uk/media/5a7c1408e5274a1f5cc75a68/SECONDARY_national_curriculum_-_Mathematics.pdf",
        source_type="pdf",
        publisher="GOV.UK / Department for Education",
        licence="Open Government Licence v3.0",
    ),
    Source(
        pack_id="KS3_English",
        year_band="KS3 (Year 7-9)",
        subject="English",
        url="https://assets.publishing.service.gov.uk/media/5a7b8761ed915d4147620f6b/SECONDARY_national_curriculum_-_English2.pdf",
        source_type="pdf",
        publisher="GOV.UK / Department for Education",
        licence="Open Government Licence v3.0",
    ),
    Source(
        pack_id="KS3_Science",
        year_band="KS3 (Year 7-9)",
        subject="Science",
        url="https://assets.publishing.service.gov.uk/media/5a7d563de5274a2af0ae2ffa/SECONDARY_national_curriculum_-_Science_220714.pdf",
        source_type="pdf",
        publisher="GOV.UK / Department for Education",
        licence="Open Government Licence v3.0",
    ),
]


def _safe_filename(url: str) -> str:
    p = urlparse(url)
    name = Path(p.path).name or "download"
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", name)


def fetch_to_cache(url: str) -> Path:
    cache_path = CACHE_DIR / _safe_filename(url)
    if cache_path.exists():
        return cache_path

    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    cache_path.write_bytes(r.content)
    time.sleep(0.5)  # be polite
    return cache_path


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            parts.append(t)
    return "\n".join(parts)


def extract_text_from_html(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    # remove nav/footers/scripts
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    main = soup.find("main") or soup.body or soup
    text = main.get_text("\n", strip=True)
    return text


def normalize_text(text: str) -> str:
    # clean weird spaces and repeated newlines
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> List[str]:
    """
    Simple chunker: splits on blank lines; merges paragraphs until max_chars.
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    buf = ""
    for p in paras:
        if not buf:
            buf = p
            continue
        if len(buf) + 2 + len(p) <= max_chars:
            buf = buf + "\n\n" + p
        else:
            chunks.append(buf)
            # start new with overlap tail from previous
            tail = buf[-overlap:] if overlap and len(buf) > overlap else ""
            buf = (tail + "\n\n" + p).strip()
    if buf:
        chunks.append(buf)
    return chunks


def build_pack(source: Source) -> Dict[str, Any]:
    cached = fetch_to_cache(source.url)

    if source.source_type == "pdf":
        raw = extract_text_from_pdf(cached)
    elif source.source_type == "html":
        raw = extract_text_from_html(cached)
    else:
        raise ValueError(f"Unknown source_type: {source.source_type}")

    text = normalize_text(raw)
    chunks = chunk_text(text)

    return {
        "pack_id": source.pack_id,
        "year_band": source.year_band,
        "subject": source.subject,
        "source": {
            "url": source.url,
            "publisher": source.publisher,
            "licence": source.licence,
            "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        },
        "chunks": [
            {
                "chunk_id": f"{source.pack_id}_{i:04d}",
                "text": c,
            }
            for i, c in enumerate(chunks, start=1)
        ],
    }


def main():
    for s in SOURCES:
        pack = build_pack(s)
        out_path = OUT_DIR / f"{s.pack_id}.json"
        out_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✅ Wrote {out_path} ({len(pack['chunks'])} chunks)")


if __name__ == "__main__":
    main()
