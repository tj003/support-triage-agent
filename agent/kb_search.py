import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class KBSearch:
    """Keyword-overlap based KB search."""

    def __init__(
        self,
        kb_path: Optional[Path] = None,
        entries: Optional[List[Dict[str, object]]] = None,
    ) -> None:
        if entries is not None:
            self.kb = entries
        elif kb_path is not None:
            self.kb = self._load_kb(kb_path)
        else:  # pragma: no cover - defensive
            raise ValueError("kb_path or entries must be provided")

    def _load_kb(self, kb_path: Path) -> List[Dict[str, object]]:
        with kb_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def _normalize_tokens(self, text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _entry_tokens(self, entry: Dict[str, object]) -> set[str]:
        tokens: set[str] = set()
        tokens |= self._normalize_tokens(str(entry.get("title", "")))
        tokens |= self._normalize_tokens(str(entry.get("category", "")))
        symptoms: Iterable[str] = entry.get("symptoms", [])  # type: ignore[assignment]
        for symptom in symptoms:
            tokens |= self._normalize_tokens(symptom)
        return tokens

    def search(self, description: str, max_results: int = 3) -> List[Dict[str, object]]:
        desc_tokens = self._normalize_tokens(description)
        if not desc_tokens:
            return []

        scored: List[Dict[str, object]] = []
        for entry in self.kb:
            entry_tokens = self._entry_tokens(entry)
            union = desc_tokens | entry_tokens
            if not union:
                continue
            overlap = desc_tokens & entry_tokens
            score = len(overlap) / len(union)
            if score <= 0:
                continue
            scored.append(
                {
                    "id": entry["id"],
                    "title": entry["title"],
                    "recommended_action": entry.get("recommended_action", ""),
                    "similarity": round(score, 3),
                }
            )

        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored[:max_results]
