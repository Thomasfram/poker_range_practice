from __future__ import annotations
from collections import Counter
from enum import Enum

from .hand_eval import Card, HandStrength, STRENGTH_LABELS, evaluate_hand


class BoardTexture(str, Enum):
    EXTRA_DRY     = 'TRES_DRY'
    INTERMEDIAIRE = 'INTERMEDIAIRE'
    DRAWY         = 'DRAWY'


BB_TEXTURE_LABELS = {
    'TRES_DRY':      'Très Dry',
    'INTERMEDIAIRE': 'Intermédiaire',
    'DRAWY':         'Drawy',
}

_CBET_FREQ_LABELS = {
    BoardTexture.EXTRA_DRY:      'range entier',
    BoardTexture.INTERMEDIAIRE:  '3/4 des mains',
    BoardTexture.DRAWY:          '1/2 des mains',
}

_VILLAIN_SIZING = {
    BoardTexture.EXTRA_DRY:      25,
    BoardTexture.INTERMEDIAIRE:  33,
    BoardTexture.DRAWY:          50,
}


def classify_board_vs_bb(board: list[Card]) -> BoardTexture:
    vals = sorted([c.value for c in board], reverse=True)
    suits = [c.suit for c in board]
    r1, r2, r3 = vals

    max_suit = max(Counter(suits).values())
    has_flush_draw = max_suit >= 2
    is_monotone = max_suit == 3

    pairs = [r for r, cnt in Counter(vals).items() if cnt >= 2]
    if pairs:
        pr = pairs[0]
        if pr >= 8:
            return BoardTexture.EXTRA_DRY
        if pr <= 3:
            return BoardTexture.INTERMEDIAIRE
        return BoardTexture.DRAWY

    if r1 <= 7:
        return BoardTexture.DRAWY

    low_connected    = r2 <= 7 and r3 <= 7 and (r2 - r3) <= 2
    highly_connected = (r1 - r3) <= 4

    if is_monotone and r1 <= 11:
        return BoardTexture.DRAWY
    if r1 >= 13:
        return BoardTexture.EXTRA_DRY if (r2 >= 6 and (r2 - r3) >= 5) else BoardTexture.INTERMEDIAIRE
    if r1 >= 8:
        if not has_flush_draw and not low_connected:
            return BoardTexture.EXTRA_DRY
        if highly_connected or is_monotone:
            return BoardTexture.DRAWY
        return BoardTexture.INTERMEDIAIRE
    return BoardTexture.DRAWY


def _sizing(texture: BoardTexture, stack_depth: int) -> int:
    deep = stack_depth >= 70
    return {
        BoardTexture.EXTRA_DRY:      33 if deep else 25,
        BoardTexture.INTERMEDIAIRE:  50 if deep else 33,
        BoardTexture.DRAWY:          66 if deep else 50,
    }[texture]


def _should_bet(strength: HandStrength, texture: BoardTexture) -> bool:
    if texture == BoardTexture.EXTRA_DRY:
        return True
    return strength in {
        HandStrength.MONSTER, HandStrength.STRONG, HandStrength.MEDIUM,
        HandStrength.DRAW_STRONG, HandStrength.BACKDOOR,
    }


def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    stack_depth: int,
) -> dict:
    strength = evaluate_hand(hole, board)
    texture  = classify_board_vs_bb(board)
    do_bet   = _should_bet(strength, texture)
    return {
        'texture':        texture.value,
        'texture_label':  BB_TEXTURE_LABELS[texture.value],
        'cbet_frequency': _CBET_FREQ_LABELS[texture],
        'hand_strength':  strength.value,
        'hand_label':     STRENGTH_LABELS[strength.value],
        'should_bet':     do_bet,
        'correct_sizing': _sizing(texture, stack_depth) if do_bet else None,
    }
