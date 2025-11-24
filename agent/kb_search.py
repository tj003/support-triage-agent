import json
import logging
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set


class KnowledgeBaseSearch:
    """Lightweight keyword matcher with a small boost for exact symptom hits."""

    def __init__(
        self,
        kb_path: Optional[Path] = None,
        entries: Optional[Sequence[Dict[str, object]]] = None,
    ) -> None:
        if entries is None and kb_path is None:  # pragma: no cover - defensive
            raise ValueError("Provide either kb_path or entries")
        self.logger = logging.getLogger(__name__)
        if entries is not None:
            self.kb = list(entries)
        else:
            assert kb_path is not None  # narrow type
            self.kb = self._load_kb(kb_path)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def lookup(self, description: str, limit: int = 3) -> List[Dict[str, object]]:
        """Return the most relevant KB entries for a description."""
        desc_tokens = self._normalize_tokens(description)
        if not desc_tokens:
            return []

        ranked: List[Dict[str, object]] = []
        for entry in self.kb:
            entry_tokens = self._entry_tokens(entry)
            union = desc_tokens | entry_tokens
            if not union:
                continue

            overlap = desc_tokens & entry_tokens
            base_score = len(overlap) / len(union)
            if base_score == 0:
                continue

            symptom_bonus = 0.0
            if self._symptom_hit(description, entry.get("symptoms", [])):
                symptom_bonus = 0.1

            score = min(base_score + symptom_bonus, 1.0)
            ranked.append(
                {
                    "id": entry.get("id", "UNKNOWN"),
                    "title": entry.get("title", "Untitled"),
                    "recommended_action": entry.get("recommended_action", ""),
                    "similarity": round(score, 3),
                }
            )

        ranked.sort(key=lambda item: item["similarity"], reverse=True)
        return ranked[:limit]

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _load_kb(self, kb_path: Path) -> List[Dict[str, object]]:
        try:
            with kb_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except OSError as exc:  # pragma: no cover - filesystem guard
            self.logger.error("Failed to load KB file %s", kb_path, exc_info=exc)
            raise

    def _normalize_tokens(self, text: str) -> Set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    def _entry_tokens(self, entry: Dict[str, object]) -> Set[str]:
        tokens: Set[str] = set()
        tokens |= self._normalize_tokens(str(entry.get("title", "")))
        tokens |= self._normalize_tokens(str(entry.get("category", "")))
        symptoms: Iterable[str] = entry.get("symptoms", [])  # type: ignore[assignment]
        for symptom in symptoms:
            tokens |= self._normalize_tokens(symptom)
        return tokens

    def _symptom_hit(self, description: str, symptoms: Iterable[str]) -> bool:
        text = description.lower()
        for symptom in symptoms:
            candidate = symptom.strip().lower()
            if candidate and candidate in text:
                return True
        return False
