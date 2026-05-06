from __future__ import annotations
from collections import Counter
from enum import Enum

from .hand_eval import Card, HandStrength, STRENGTH_LABELS, evaluate_hand


class LimpSbCategory(str, Enum):
    PAIRED_LOW        = 'paired_low'        # pair ≤ 6 → check range
    PAIRED_MID        = 'paired_mid'        # pair 7-9 → 33%
    PAIRED_HIGH       = 'paired_high'       # pair T+ → ≥50%
    NUTS_ADVANTAGE    = 'nuts_advantage'    # A-high single or 2+ broadway → 50%
    CONNECTED_OR_MONO = 'connected_or_mono' # connected or monocolor (non-BW) → 25%
    DISCONNECTED      = 'disconnected'      # else → 50%


LIMP_SB_CATEGORY_LABELS = {
    'paired_low':        'Flop pairé low (2-6)',
    'paired_mid':        'Flop pairé mid (7-9)',
    'paired_high':       'Flop pairé high (T+)',
    'nuts_advantage':    'A high / Double BW',
    'connected_or_mono': 'Connecté ou monocolor',
    'disconnected':      'Déconnecté',
}


def _freq_label(cat: LimpSbCategory, stack_depth: int) -> str:
    shallow = stack_depth <= 30  # 25bb path
    if cat == LimpSbCategory.PAIRED_LOW:
        return 'check range entier'
    if cat == LimpSbCategory.PAIRED_MID:
        return 'check range (25bb)' if shallow else '1/3 des mains (½ pot)'
    if cat == LimpSbCategory.PAIRED_HIGH:
        return '~40% des mains (½ pot)' if shallow else '≥50% des mains (½ pot)'
    if cat == LimpSbCategory.NUTS_ADVANTAGE:
        return '~40% des mains (½ pot)' if shallow else '1/2 des mains (½ pot)'
    if cat == LimpSbCategory.CONNECTED_OR_MONO:
        return '~25% des mains (½ pot)'
    if cat == LimpSbCategory.DISCONNECTED:
        return '1/2 des mains (½ pot)'
    return ''


def classify_board_limp_sb(board: list[Card]) -> LimpSbCategory:
    vals  = sorted([c.value for c in board], reverse=True)
    suits = [c.suit for c in board]
    r1, r2, r3 = vals

    # Monocolor first
    if max(Counter(suits).values()) == 3:
        return LimpSbCategory.CONNECTED_OR_MONO

    # Paired boards — split by rank
    pair_ranks = [r for r, cnt in Counter(vals).items() if cnt >= 2]
    if pair_ranks:
        pr = pair_ranks[0]
        if pr <= 6:
            return LimpSbCategory.PAIRED_LOW
        if pr <= 9:
            return LimpSbCategory.PAIRED_MID
        return LimpSbCategory.PAIRED_HIGH

    # A-high (single broadway A at top)
    if r1 == 14:
        return LimpSbCategory.NUTS_ADVANTAGE

    # Double broadway (2+ cards with value ≥ 10)
    bw_count = sum(1 for v in vals if v >= 10)
    if bw_count >= 2:
        return LimpSbCategory.NUTS_ADVANTAGE

    # Connected (straight-draw potential, gap ≤ 4)
    if (r1 - r3) <= 4:
        return LimpSbCategory.CONNECTED_OR_MONO

    return LimpSbCategory.DISCONNECTED


def _should_bet(strength: HandStrength, cat: LimpSbCategory, stack_depth: int) -> bool:
    shallow = stack_depth <= 30

    if cat == LimpSbCategory.PAIRED_LOW:
        return False

    if cat == LimpSbCategory.PAIRED_MID:
        if shallow:
            return False
        return strength in {HandStrength.MONSTER, HandStrength.STRONG}

    if cat == LimpSbCategory.PAIRED_HIGH:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG, HandStrength.MEDIUM}

    if cat == LimpSbCategory.NUTS_ADVANTAGE:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG,
                            HandStrength.MEDIUM, HandStrength.DRAW_STRONG}

    if cat == LimpSbCategory.CONNECTED_OR_MONO:
        return strength == HandStrength.MONSTER

    if cat == LimpSbCategory.DISCONNECTED:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG,
                            HandStrength.MEDIUM, HandStrength.DRAW_STRONG,
                            HandStrength.SD_VALUE}

    return False


def get_cbet_recommendation_limp_sb(
    hole: list[Card],
    board: list[Card],
    stack_depth: int,
) -> dict:
    strength = evaluate_hand(hole, board)
    cat      = classify_board_limp_sb(board)
    do_bet   = _should_bet(strength, cat, stack_depth)
    return {
        'texture':        cat.value,
        'texture_label':  LIMP_SB_CATEGORY_LABELS[cat.value],
        'cbet_frequency': _freq_label(cat, stack_depth),
        'hand_strength':  strength.value,
        'hand_label':     STRENGTH_LABELS[strength.value],
        'should_bet':     do_bet,
        'correct_sizing': 50 if do_bet else None,  # always ½ pot (1bb) in limped pot
    }
