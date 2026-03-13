"""Enumeration des plans d'abonnement SOMA."""
from enum import Enum


class PlanCode(str, Enum):
    FREE = "free"
    AI = "ai"
    PERFORMANCE = "performance"

    @property
    def display_name(self) -> str:
        names = {"free": "SOMA Free", "ai": "SOMA AI", "performance": "SOMA Performance"}
        return names[self.value]

    @property
    def rank(self) -> int:
        ranks = {"free": 1, "ai": 2, "performance": 3}
        return ranks[self.value]

    def includes(self, other: "PlanCode") -> bool:
        """True si ce plan inclut les droits de l'autre plan."""
        return self.rank >= other.rank
