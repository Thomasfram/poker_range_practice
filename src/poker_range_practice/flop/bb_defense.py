from __future__ import annotations
from collections import Counter
from itertools import combinations

from .hand_eval import Card, HandStrength, STRENGTH_LABELS, evaluate_hand, _made_straight, _oesd_or_gutshot
from .cbet_vs_bb import BoardTexture, BB_TEXTURE_LABELS, classify_board_vs_bb


def _has_backdoor_straight(cards: list[Card]) -> bool:
    """True if any 3-card combo containing ≥1 hole card spans ≤4 ranks."""
    hole = cards[:2]
    for combo in combinations(cards, 3):
        if not any(c in hole for c in combo):
            continue
        cv = sorted(set(c.value for c in combo))
        if 14 in cv:
            cv = sorted(set(cv + [1]))
        for i in range(len(cv) - 2):
            if cv[i + 2] - cv[i] <= 4:
                return True
    return False


def get_bb_defense_recommendation(
    hole: list[Card],
    board: list[Card],
    stack_depth: int,
) -> dict:
    texture  = classify_board_vs_bb(board)
    strength = evaluate_hand(hole, board)

    hv             = sorted([c.value for c in hole], reverse=True)
    bv             = sorted([c.value for c in board], reverse=True)
    all5           = hole + board
    hole_suits     = [c.suit for c in hole]
    hole_is_suited = hole_suits[0] == hole_suits[1]
    suit_count     = Counter(c.suit for c in all5)
    b_set          = set(bv)
    bv_count       = Counter(bv)
    is_pocket_pair = hv[0] == hv[1]

    has_flush_draw = any(
        suit_count[s] == 4 and hole_suits.count(s) >= 1 for s in suit_count
    )
    has_oesd, has_gutshot = _oesd_or_gutshot(all5)
    has_bd_flush = any(
        suit_count[s] == 3 and hole_suits.count(s) >= 1 for s in suit_count
    )
    has_bd_straight = _has_backdoor_straight(all5)

    has_top_pair = bv[0] in hv
    has_mid_pair = bv[1] in hv
    has_bot_pair = bv[2] in hv
    top_kicker   = max((v for v in hv if v != bv[0]), default=0) if has_top_pair else 0

    is_set      = is_pocket_pair and hv[0] in b_set
    is_trips    = any(bv_count[v] >= 2 and v in set(hv) for v in b_set)
    is_straight = _made_straight(all5)
    is_flush    = max(suit_count.values()) >= 5

    _xr = {
        BoardTexture.EXTRA_DRY:      (4,   4,    5),
        BoardTexture.INTERMEDIAIRE:  (2.5, 3,    3.5),
        BoardTexture.DRAWY:          (2.5, 2.75, 3),
    }[texture]
    xr_mult = _xr[0] if stack_depth <= 30 else (_xr[1] if stack_depth <= 60 else _xr[2])

    villain_sizing = {
        BoardTexture.EXTRA_DRY:      25,
        BoardTexture.INTERMEDIAIRE:  33,
        BoardTexture.DRAWY:          50,
    }[texture]

    action = 'fold'

    if texture == BoardTexture.EXTRA_DRY:
        # XR value
        if strength == HandStrength.MONSTER:
            action = 'raise'
        elif is_pocket_pair and hv[0] > bv[0]:
            action = 'raise'
        elif has_top_pair and top_kicker >= 11:
            action = 'raise'
        # XR bluff
        elif has_gutshot:
            action = 'raise'
        elif has_bot_pair:
            action = 'raise'
        elif (max(hv) <= 12 and has_bd_flush
              and not has_top_pair and not has_mid_pair and not has_bot_pair):
            action = 'raise'
        elif ([v for v in hv if v > 9 and v not in b_set]
              and max(hv) != 13
              and has_bd_flush and has_bd_straight
              and not has_top_pair and not has_mid_pair and not has_bot_pair):
            action = 'raise'
        # Call
        elif strength == HandStrength.STRONG:
            action = 'call'
        elif strength in {HandStrength.MEDIUM, HandStrength.WEAK}:
            action = 'call'
        elif max(hv) >= 13 and has_bd_flush:
            action = 'call'
        elif max(hv) >= 12 and has_bd_flush:
            action = 'call'
        elif has_bd_flush and has_bd_straight:
            action = 'call'

    elif texture == BoardTexture.INTERMEDIAIRE:
        # XR value
        if strength == HandStrength.MONSTER:
            action = 'raise'
        elif has_top_pair and top_kicker >= (12 if hole_is_suited else 11):
            action = 'raise'
        # XR bluff
        elif has_oesd:
            action = 'raise'
        elif has_flush_draw:
            action = 'raise'
        elif has_gutshot and has_bd_flush:
            action = 'raise'
        elif (14 in hv and 14 not in b_set and has_bd_flush and has_bd_straight):
            action = 'raise'
        # Call
        elif 14 in hv and 14 not in b_set:
            action = 'call'
        elif (len([v for v in hv if v > bv[2] and v not in b_set]) >= 2 and has_bd_flush):
            action = 'call'
        elif strength in {HandStrength.STRONG, HandStrength.MEDIUM, HandStrength.WEAK}:
            action = 'call'

    elif texture == BoardTexture.DRAWY:
        # XR value: set / trips / straight only (not two pair, not flush)
        if is_set or is_trips or is_straight:
            action = 'raise'
        # XR bluff: OESD, any flush draw
        elif has_oesd or has_flush_draw:
            action = 'raise'
        # Call: top pair, flush, A-high+BDFD, 2 overcards+BDFD, middle pair
        elif has_top_pair or is_flush:
            action = 'call'
        elif 14 in hv and 14 not in b_set and has_bd_flush:
            action = 'call'
        elif len([v for v in hv if v > bv[2] and v not in b_set]) >= 2 and has_bd_flush:
            action = 'call'
        elif has_mid_pair:
            action = 'call'
        # Fold: bottom pair without draws
        elif has_bot_pair and not has_flush_draw and not has_bd_flush:
            action = 'fold'
        elif strength == HandStrength.WEAK:
            action = 'fold'

    return {
        'texture':        texture.value,
        'texture_label':  BB_TEXTURE_LABELS[texture.value],
        'action':         action,
        'raise_sizing':   xr_mult if action == 'raise' else None,
        'villain_sizing': villain_sizing,
        'hand_strength':  strength.value,
        'hand_label':     STRENGTH_LABELS[strength.value],
    }
