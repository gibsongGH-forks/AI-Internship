"""Small helpers for Week 5 Agentic Memory demos (no vendor lock-in)."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
EDGE = re.compile(
    r"\[\[([^\]]+)\]\]\s+(works_at|reports_to)\s+\[\[([^\]]+)\]\]",
    re.IGNORECASE,
)


def load_notes(notes_dir: str | Path) -> dict[str, str]:
    root = Path(notes_dir)
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(root.glob("*.md"))}


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def bag_vector(text: str, vocab: list[str]) -> list[float]:
    counts = Counter(tokenize(text))
    return [float(counts.get(t, 0)) for t in vocab]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class VectorIndex:
    docs: dict[str, str]
    vocab: list[str]
    vectors: dict[str, list[float]]

    @classmethod
    def build(cls, docs: dict[str, str]) -> "VectorIndex":
        vocab = sorted({t for text in docs.values() for t in tokenize(text)})
        vectors = {name: bag_vector(text, vocab) for name, text in docs.items()}
        return cls(docs=docs, vocab=vocab, vectors=vectors)

    def search(self, query: str, k: int = 3) -> list[tuple[str, float, str]]:
        q = bag_vector(query, self.vocab)
        scored = [(name, cosine(q, vec), self.docs[name]) for name, vec in self.vectors.items()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


@dataclass
class GraphStore:
    """Typed edges from wikilink patterns (zero LLM at write time)."""

    nodes: set[str]
    edges: list[tuple[str, str, str]]  # (src, rel, dst)

    @classmethod
    def from_notes(cls, docs: dict[str, str]) -> "GraphStore":
        nodes: set[str] = set()
        edges: list[tuple[str, str, str]] = []
        for text in docs.values():
            for m in WIKILINK.finditer(text):
                nodes.add(m.group(1).strip())
            for m in EDGE.finditer(text):
                src, rel, dst = m.group(1).strip(), m.group(2).lower(), m.group(3).strip()
                nodes.update([src, dst])
                edges.append((src, rel, dst))
        return cls(nodes=nodes, edges=edges)

    def query(self, entity: str, edge: str | None = None) -> list[tuple[str, str, str]]:
        entity_l = entity.lower()
        out = []
        for src, rel, dst in self.edges:
            if edge and rel != edge.lower():
                continue
            if src.lower() == entity_l or dst.lower() == entity_l:
                out.append((src, rel, dst))
        return out


class JsonMemoryStore:
    """Tiny durable memory: agent writes, fresh sessions read."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        if not self.path.exists():
            self._write({"human": {}, "audit": []})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_human(self) -> dict[str, str]:
        return dict(self._read().get("human", {}))

    def memory_replace(self, key: str, value: str, source: str = "user") -> None:
        data = self._read()
        data.setdefault("human", {})[key] = value
        data.setdefault("audit", []).append(
            {"op": "memory_replace", "key": key, "value": value, "source": source}
        )
        self._write(data)

    def clear(self) -> None:
        self._write({"human": {}, "audit": []})
