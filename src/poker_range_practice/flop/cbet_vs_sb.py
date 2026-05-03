from __future__ import annotations
from collections import Counter
from enum import Enum

from .hand_eval import Card, HandStrength, STRENGTH_LABELS, evaluate_hand


class SbCategory(str, Enum):
    RANGE_LOW_MID_PAIR = 'range_low_mid_pair'  # pairé 2-9  → 100%, 33%
    RANGE_NINE_EIGHT   = 'range_nine_eight'    # 9/8 high   → 100%, 50%
    RANGE_LOW_BOARD    = 'range_low_board'     # ≤7 high    → 100%, 50%
    QJT_HIGH           = 'qjt_high'            # Q/J/T high (1 broadway) → 66%, 50%
    DOUBLE_BROADWAY    = 'double_broadway'     # 2+ broadway → 66%, 50%
    AK_DRY             = 'ak_dry'             # A/K high sec → 66%, 33%
    HIGH_PAIR          = 'high_pair'           # pairé T+    → 30%, 33%
    AK_DRAWY           = 'ak_drawy'            # A/K high drawy → 50%, 50%
    MONOCOLOR          = 'monocolor'           # monotone → <50%, 33%


SB_CATEGORY_LABELS = {
    'range_low_mid_pair': 'Flop pairé mid/low (2-9) — Range bet 33%',
    'range_nine_eight':   '9/8 high — Range bet 50%',
    'range_low_board':    'Low board (≤7) — Range bet 50%',
    'qjt_high':           'Q/J/T high — Bet 66% sizing 50%',
    'double_broadway':    'Double broadway — Bet 66% sizing 50%',
    'ak_dry':             'A/K high sec — Bet 66% sizing 33%',
    'high_pair':          'Flop pairé haut (T+) — Bet 30% sizing 33%',
    'ak_drawy':           'A/K high drawy — Bet 50% sizing 50%',
    'monocolor':          'Board monocolor — Bet <50% sizing 33%',
}

SB_FREQ_LABELS = {
    'range_low_mid_pair': 'range entier (33%)',
    'range_nine_eight':   'range entier (50%)',
    'range_low_board':    'range entier (50%)',
    'qjt_high':           '2/3 des mains (50%)',
    'double_broadway':    '2/3 des mains (50%)',
    'ak_dry':             '2/3 des mains (33%)',
    'high_pair':          '30% des mains (33%)',
    'ak_drawy':           '1/2 des mains (50%)',
    'monocolor':          '<50% des mains (33%)',
}


def classify_board_vs_sb(board: list[Card]) -> SbCategory:
    vals = sorted([c.value for c in board], reverse=True)
    suits = [c.suit for c in board]
    r1, r2, r3 = vals

    max_suit = max(Counter(suits).values())

    if max_suit == 3:
        return SbCategory.MONOCOLOR

    pairs = [r for r, cnt in Counter(vals).items() if cnt >= 2]
    if pairs:
        pr = pairs[0]
        return SbCategory.HIGH_PAIR if pr >= 10 else SbCategory.RANGE_LOW_MID_PAIR

    if r1 <= 7:
        return SbCategory.RANGE_LOW_BOARD
    if r1 <= 9:
        return SbCategory.RANGE_NINE_EIGHT
    if r1 >= 13:
        dry = r2 >= 6 and (r2 - r3) >= 5
        return SbCategory.AK_DRY if dry else SbCategory.AK_DRAWY

    broadway_count = sum(1 for v in vals if v >= 10)
    return SbCategory.DOUBLE_BROADWAY if broadway_count >= 2 else SbCategory.QJT_HIGH


def _sizing(cat: SbCategory) -> int:
    return {
        SbCategory.RANGE_LOW_MID_PAIR: 33,
        SbCategory.RANGE_NINE_EIGHT:   50,
        SbCategory.RANGE_LOW_BOARD:    50,
        SbCategory.QJT_HIGH:           50,
        SbCategory.DOUBLE_BROADWAY:    50,
        SbCategory.AK_DRY:             33,
        SbCategory.HIGH_PAIR:          33,
        SbCategory.AK_DRAWY:           50,
        SbCategory.MONOCOLOR:          33,
    }[cat]


def _should_bet(strength: HandStrength, cat: SbCategory) -> bool:
    if cat in (SbCategory.RANGE_LOW_MID_PAIR,
               SbCategory.RANGE_NINE_EIGHT,
               SbCategory.RANGE_LOW_BOARD):
        return True
    if cat == SbCategory.HIGH_PAIR:
        return strength == HandStrength.MONSTER
    if cat in (SbCategory.QJT_HIGH, SbCategory.DOUBLE_BROADWAY, SbCategory.AK_DRY):
        return strength in {
            HandStrength.MONSTER, HandStrength.STRONG, HandStrength.MEDIUM,
            HandStrength.DRAW_STRONG, HandStrength.BACKDOOR,
        }
    if cat == SbCategory.AK_DRAWY:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG, HandStrength.DRAW_STRONG}
    if cat == SbCategory.MONOCOLOR:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG}
    return False


def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    stack_depth: int,
) -> dict:
    strength = evaluate_hand(hole, board)
    cat      = classify_board_vs_sb(board)
    do_bet   = _should_bet(strength, cat)
    return {
        'texture':        cat.value,
        'texture_label':  SB_CATEGORY_LABELS[cat.value],
        'cbet_frequency': SB_FREQ_LABELS[cat.value],
        'hand_strength':  strength.value,
        'hand_label':     STRENGTH_LABELS[strength.value],
        'should_bet':     do_bet,
        'correct_sizing': _sizing(cat) if do_bet else None,
    }
