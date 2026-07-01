"""Repository and dataset discovery utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass(frozen=True)
class DiscoveredFile:
    """Represents a discovered file in repository inventory."""

    path: str
    kind: str
    size_bytes: int


@dataclass
class RepositoryInventory:
    """Structured inventory of important repository files."""

    datasets: List[DiscoveredFile] = field(default_factory=list)
    job_descriptions: List[DiscoveredFile] = field(default_factory=list)
    metadata: List[DiscoveredFile] = field(default_factory=list)
    documentation: List[DiscoveredFile] = field(default_factory=list)
    configs: List[DiscoveredFile] = field(default_factory=list)
    auxiliary: List[DiscoveredFile] = field(default_factory=list)

    def as_dict(self) -> Dict[str, List[Dict[str, object]]]:
        """Serialize inventory to primitive dictionary."""

        def serialize(items: List[DiscoveredFile]) -> List[Dict[str, object]]:
            return [
                {"path": item.path, "kind": item.kind, "size_bytes": item.size_bytes}
                for item in items
            ]

        return {
            "datasets": serialize(self.datasets),
            "job_descriptions": serialize(self.job_descriptions),
            "metadata": serialize(self.metadata),
            "documentation": serialize(self.documentation),
            "configs": serialize(self.configs),
            "auxiliary": serialize(self.auxiliary),
        }


class RepositoryDiscovery:
    """Discovers files and groups them by backend-relevant categories."""

    DATASET_EXTENSIONS = {".jsonl", ".json", ".csv", ".yaml", ".yml", ".docx"}
    CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".toml", ".ini", ".env"}
    DOC_EXTENSIONS = {".md", ".docx", ".txt"}

    def discover(self, repository_root: Path) -> RepositoryInventory:
        """Discover and classify files under repository root."""

        inventory = RepositoryInventory()
        for file_path in repository_root.rglob("*"):
            if not file_path.is_file():
                continue
            if ".venv" in file_path.parts or "__pycache__" in file_path.parts:
                continue

            rel = file_path.relative_to(repository_root).as_posix()
            suffix = file_path.suffix.lower()
            size = file_path.stat().st_size

            discovered = DiscoveredFile(path=rel, kind=self._classify(rel, suffix), size_bytes=size)

            if discovered.kind == "dataset":
                inventory.datasets.append(discovered)
            elif discovered.kind == "job_description":
                inventory.job_descriptions.append(discovered)
            elif discovered.kind == "metadata":
                inventory.metadata.append(discovered)
            elif discovered.kind == "config":
                inventory.configs.append(discovered)
            elif discovered.kind == "documentation":
                inventory.documentation.append(discovered)
            else:
                inventory.auxiliary.append(discovered)

        return inventory

    def _classify(self, rel_path: str, suffix: str) -> str:
        name = Path(rel_path).name.lower()
        if "candidate" in name and suffix in self.DATASET_EXTENSIONS:
            return "dataset"
        if "submission" in name and suffix in self.DATASET_EXTENSIONS:
            return "metadata"
        if "job_description" in name and suffix == ".docx":
            return "job_description"
        if name.startswith("readme") and suffix in self.DOC_EXTENSIONS:
            return "documentation"
        if rel_path.startswith("configs/") or suffix in self.CONFIG_EXTENSIONS:
            return "config"
        if suffix in self.DOC_EXTENSIONS:
            return "documentation"
        return "auxiliary"
