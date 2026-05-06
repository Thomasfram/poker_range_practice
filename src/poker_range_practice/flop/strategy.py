from __future__ import annotations

from .hand_eval import Card
from . import cbet_vs_bb, cbet_vs_sb, cbet_bvb, cbet_limp_sb
from .bb_defense import get_bb_defense_recommendation  # noqa: F401  (re-exported)


def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    hero_pos: str,
    villain_pos: str,
    stack_depth: int,
    scenario: str | None = None,
) -> dict:
    if hero_pos == 'SB' and villain_pos == 'BB':
        if scenario == 'limp':
            return cbet_limp_sb.get_cbet_recommendation_limp_sb(hole, board, stack_depth)
        return cbet_bvb.get_cbet_recommendation_bvb(hole, board, stack_depth)
    if villain_pos == 'BB':
        return cbet_vs_bb.get_cbet_recommendation(hole, board, stack_depth)
    if villain_pos == 'SB':
        return cbet_vs_sb.get_cbet_recommendation(hole, board, stack_depth)
    raise ValueError(f"Villain non supporté: {villain_pos}")
