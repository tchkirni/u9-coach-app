"""Core dataclasses and scoring helpers."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, MutableMapping, Optional

from core.constants import POSITION_WEIGHTS


@dataclass
class Player:
    id: int
    name: str
    birth_year: int
    preferred_position: Optional[str] = None
    foot: Optional[str] = None
    base_ratings: Dict[str, int] = field(default_factory=dict)


@dataclass
class Match:
    id: int
    date: str
    opponent: str
    competition: str
    performances: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Training:
    id: int
    date: str
    theme: str
    type: str
    notes: str = ""
    attendances: List[Dict[str, Any]] = field(default_factory=list)


def _get_base_ratings(player: Any) -> Mapping[str, int]:
    if hasattr(player, "base_ratings"):
        return getattr(player, "base_ratings") or {}
    if isinstance(player, MutableMapping):
        return player.get("base_ratings", {}) or {}
    return {}


def compute_position_scores(player: Any) -> Dict[str, Optional[float]]:
    ratings = _get_base_ratings(player)
    scores: Dict[str, Optional[float]] = {}
    for pos, weights in POSITION_WEIGHTS.items():
        num = 0
        den = 0
        for skill, weight in weights.items():
            note = ratings.get(skill)
            if note is not None and weight > 0:
                num += note * weight
                den += weight
        scores[pos] = round(num / den, 2) if den > 0 else None
    return scores


def best_position_from_scores(scores: Mapping[str, Optional[float]]) -> Optional[str]:
    valid = {k: v for k, v in scores.items() if v is not None}
    if not valid:
        return None
    return max(valid, key=valid.get)
