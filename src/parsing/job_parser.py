"""Job description parser for DOCX and plain-text sources."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import List

from src.contracts.domain import JobDescription


class JobDescriptionParser:
    """Parses a job description into canonical structured representation."""

    def parse(self, job_source: Path) -> JobDescription:
        if not job_source.exists():
            raise FileNotFoundError(f"Job document not found: {job_source}")

        if job_source.suffix.lower() == ".docx":
            raw_text = self._extract_docx_text(job_source)
        else:
            raw_text = job_source.read_text(encoding="utf-8")

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        role_title = self._extract_role_title(lines)
        seniority = self._extract_seniority_range(raw_text)
        location_constraints = self._extract_locations(raw_text)
        must_have = self._extract_section(lines, "Things you absolutely need", "Things we'd like")
        preferred = self._extract_section(lines, "Things we'd like", "Things we explicitly do NOT want")
        disqualifiers = self._extract_section(lines, "Things we explicitly do NOT want", "On location, comp, and logistics")

        return JobDescription(
            role_title=role_title,
            raw_text=raw_text,
            location_constraints=location_constraints,
            must_have_requirements=must_have,
            preferred_requirements=preferred,
            disqualifiers=disqualifiers,
            seniority_range_years=seniority,
        )

    def _extract_docx_text(self, path: Path) -> str:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")

        text = re.sub(r"</w:p>", "\n", xml)
        text = re.sub(r"<[^>]+>", " ", text)
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def _extract_role_title(self, lines: List[str]) -> str:
        for line in lines:
            if "Job Description:" in line:
                return line.split("Job Description:", 1)[1].strip()
        return lines[0] if lines else "Unknown Role"

    def _extract_seniority_range(self, text: str) -> tuple[float, float] | None:
        match = re.search(r"(\d+)\s*[\-–]\s*(\d+)\s*years", text)
        if not match:
            return None
        return float(match.group(1)), float(match.group(2))

    def _extract_locations(self, text: str) -> List[str]:
        match = re.search(r"Location:\s*([^\n]+)", text)
        if not match:
            return []
        raw = match.group(1)
        parts = [chunk.strip() for chunk in re.split(r"[|,/]", raw) if chunk.strip()]
        return parts

    def _extract_section(self, lines: List[str], start_marker: str, end_marker: str) -> List[str]:
        results: List[str] = []
        inside = False
        for line in lines:
            if start_marker in line:
                inside = True
                continue
            if inside and end_marker in line:
                break
            if inside and len(line) > 2:
                results.append(line)
        return results
