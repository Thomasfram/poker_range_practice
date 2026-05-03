from __future__ import annotations

from .hand_eval import Card
from . import cbet_vs_bb, cbet_vs_sb
from .bb_defense import get_bb_defense_recommendation  # noqa: F401  (re-exported)


def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    hero_pos: str,
    villain_pos: str,
    stack_depth: int,
) -> dict:
    if villain_pos == 'BB':
        return cbet_vs_bb.get_cbet_recommendation(hole, board, stack_depth)
    if villain_pos == 'SB':
        return cbet_vs_sb.get_cbet_recommendation(hole, board, stack_depth)
    raise ValueError(f"Villain non supporté: {villain_pos}")
