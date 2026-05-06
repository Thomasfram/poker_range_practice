from __future__ import annotations
from collections import Counter
from enum import Enum

from .hand_eval import Card, HandStrength, STRENGTH_LABELS, evaluate_hand


class BvBCategory(str, Enum):
    NUTS_ADVANTAGE                = 'nuts_advantage'        # A/K high dry
    BROADWAY_DRY_OR_DOUBLE        = 'broadway_dry_double'   # Q/J/T high dry OR 2+ broadway
    BROADWAY_CONNECTED_OR_LOW_DRY = 'broadway_conn_low_dry' # single BW connected OR low dry
    PAIRED                        = 'paired'
    MONOCOLOR                     = 'monocolor'
    LOW_CONNECTED                 = 'low_connected'         # all ≤9, gap ≤4


BVB_CATEGORY_LABELS = {
    'nuts_advantage':        'Flop haut avantage de nuts',
    'broadway_dry_double':   'Single BW dry / Double BW',
    'broadway_conn_low_dry': 'Single BW connecté / Low board déconnecté',
    'paired':                'Flop pairé',
    'monocolor':             'Flop monocolor',
    'low_connected':         'Flop bas connecté',
}


def _freq_label(cat: BvBCategory, stack_depth: int) -> str:
    deep = stack_depth >= 70
    if cat == BvBCategory.NUTS_ADVANTAGE:
        return '3/4 des mains (½ pot)'
    if cat == BvBCategory.BROADWAY_DRY_OR_DOUBLE:
        return '70% des mains (⅓ pot)'
    if cat == BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY:
        return '1/2 des mains (½ pot)'
    if cat == BvBCategory.PAIRED:
        return '1/2 des mains (¼ pot)' if deep else '3/4 des mains (¼ pot)'
    if cat == BvBCategory.MONOCOLOR:
        return '1/2 des mains (¼ pot)' if deep else '1/3 des mains (¼ pot)'
    if cat == BvBCategory.LOW_CONNECTED:
        return 'check range entier' if deep else '30% des mains (⅔ pot)'
    return ''


def classify_board_bvb(board: list[Card]) -> BvBCategory:
    vals  = sorted([c.value for c in board], reverse=True)
    suits = [c.suit for c in board]
    r1, r2, r3 = vals

    if max(Counter(suits).values()) == 3:
        return BvBCategory.MONOCOLOR

    if any(cnt >= 2 for cnt in Counter(vals).values()):
        return BvBCategory.PAIRED

    if r1 <= 9:
        return BvBCategory.LOW_CONNECTED if (r1 - r3) <= 4 else BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY

    bw_count = sum(1 for v in vals if v >= 10)
    if bw_count >= 2:
        return BvBCategory.BROADWAY_DRY_OR_DOUBLE

    # single broadway card
    if r1 >= 13:  # A or K top card
        is_dry = r2 >= 6 and (r2 - r3) >= 5
        return BvBCategory.NUTS_ADVANTAGE if is_dry else BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY
    else:  # Q, J, T top card
        return BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY if (r1 - r3) <= 4 else BvBCategory.BROADWAY_DRY_OR_DOUBLE


def _sizing(cat: BvBCategory) -> int:
    if cat == BvBCategory.LOW_CONNECTED:
        return 66
    return {
        BvBCategory.NUTS_ADVANTAGE:                50,
        BvBCategory.BROADWAY_DRY_OR_DOUBLE:        33,
        BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY: 50,
        BvBCategory.PAIRED:                        25,
        BvBCategory.MONOCOLOR:                     25,
    }[cat]


def _should_bet(strength: HandStrength, cat: BvBCategory, stack_depth: int) -> bool:
    deep = stack_depth >= 70

    if cat in (BvBCategory.NUTS_ADVANTAGE, BvBCategory.BROADWAY_DRY_OR_DOUBLE):
        return strength in {HandStrength.MONSTER, HandStrength.STRONG,
                            HandStrength.MEDIUM, HandStrength.DRAW_STRONG}

    if cat == BvBCategory.BROADWAY_CONNECTED_OR_LOW_DRY:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG, HandStrength.DRAW_STRONG}

    if cat == BvBCategory.PAIRED:
        if deep:
            return strength in {HandStrength.MONSTER, HandStrength.STRONG}
        return strength in {HandStrength.MONSTER, HandStrength.STRONG,
                            HandStrength.MEDIUM, HandStrength.DRAW_STRONG}

    if cat == BvBCategory.MONOCOLOR:
        if deep:
            return strength in {HandStrength.MONSTER, HandStrength.STRONG}
        return strength == HandStrength.MONSTER

    if cat == BvBCategory.LOW_CONNECTED:
        if deep:
            return False
        return strength == HandStrength.MONSTER

    return False


def get_cbet_recommendation_bvb(
    hole: list[Card],
    board: list[Card],
    stack_depth: int,
) -> dict:
    strength = evaluate_hand(hole, board)
    cat      = classify_board_bvb(board)
    do_bet   = _should_bet(strength, cat, stack_depth)
    return {
        'texture':        cat.value,
        'texture_label':  BVB_CATEGORY_LABELS[cat.value],
        'cbet_frequency': _freq_label(cat, stack_depth),
        'hand_strength':  strength.value,
        'hand_label':     STRENGTH_LABELS[strength.value],
        'should_bet':     do_bet,
        'correct_sizing': _sizing(cat) if do_bet else None,
    }
