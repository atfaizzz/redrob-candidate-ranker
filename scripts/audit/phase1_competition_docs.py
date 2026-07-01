"""Phase 1: Extract full text from all competition DOCX files."""
import sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

CHALLENGE_DIR = Path("India_runs_data_and_ai_challenge")
DOCS = [
    "README.docx",
    "submission_spec.docx",
    "redrob_signals_doc.docx",
]

HONEYPOT_TERMS = [
    "honeypot", "trap", "synthetic", "sanity check", "hidden evaluation",
    "leakage", "fake candidate", "decoy", "adversarial", "sentinel",
    "watermark", "evaluation-only", "reserved", "dummy"
]

NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_docx_text(docx_path: Path) -> str:
    with ZipFile(docx_path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()
    paragraphs = []
    for para in root.iter(f"{NS}p"):
        runs = [r.text or "" for r in para.iter(f"{NS}t")]
        text = "".join(runs).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


results = {}
for doc in DOCS:
    path = CHALLENGE_DIR / doc
    if not path.exists():
        print(f"[SKIP] {doc} not found")
        continue
    text = extract_docx_text(path)
    results[doc] = text
    print(f"\n{'='*60}")
    print(f"FILE: {doc}  ({len(text)} chars, {len(text.splitlines())} lines)")
    print(f"{'='*60}")
    hits = []
    for term in HONEYPOT_TERMS:
        for i, line in enumerate(text.splitlines(), 1):
            if term.lower() in line.lower():
                hits.append((term, i, line.strip()))
    if hits:
        print(f"  HONEYPOT-RELATED TERMS FOUND ({len(hits)} hits):")
        for term, lineno, line in hits:
            print(f"    [{term}] line {lineno}: {line[:120]}")
    else:
        print("  No honeypot/trap-related terms found in this document.")

print("\n\nFULL TEXT DUMP (for manual review):")
for doc, text in results.items():
    print(f"\n{'='*60}")
    print(f"=== {doc} ===")
    print(f"{'='*60}")
    print(text[:8000])
    if len(text) > 8000:
        print(f"... [{len(text)-8000} more chars truncated]")
