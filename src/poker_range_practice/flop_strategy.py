from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Optional

RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
}

TEXTURE_LABELS = {
    'TRES_DRY': 'Très Dry',
    'INTERMEDIAIRE': 'Intermédiaire',
    'DRAWY': 'Drawy',
}

STRENGTH_LABELS = {
    'monster': 'Main forte (set / deux paires / quinte / couleur)',
    'strong': 'Main forte (top paire ou overpair)',
    'medium': 'Paire milieu bon kicker (7+)',
    'weak': 'Paire faible / paire milieu mauvais kicker',
    'draw_strong': 'Tirage fort (flush draw / OESD)',
    'draw_medium': 'Tirage faible (gutshot / paire + gutshot)',
    'backdoor': 'Backdoor draw uniquement',
    'sd_value': 'Showdown value (A/K-high, underpair)',
    'air': 'Air (sans tirage)',
}


class BoardTexture(str, Enum):
    TRES_DRY = 'TRES_DRY'
    INTERMEDIAIRE = 'INTERMEDIAIRE'
    DRAWY = 'DRAWY'


class HandStrength(str, Enum):
    MONSTER = 'monster'
    STRONG = 'strong'
    MEDIUM = 'medium'
    WEAK = 'weak'
    DRAW_STRONG = 'draw_strong'
    DRAW_MEDIUM = 'draw_medium'
    BACKDOOR = 'backdoor'
    SD_VALUE = 'sd_value'
    AIR = 'air'


@dataclass
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]


# ─── Board Texture ────────────────────────────────────────────────────────────

def classify_board_texture(board: list[Card]) -> BoardTexture:
    vals = sorted([c.value for c in board], reverse=True)
    suits = [c.suit for c in board]
    r1, r2, r3 = vals

    max_suit = max(Counter(suits).values())
    has_flush_draw = max_suit >= 2
    is_monotone = max_suit == 3

    rank_counts = Counter(vals)
    pairs = [r for r, cnt in rank_counts.items() if cnt >= 2]

    # Paired board
    if pairs:
        pr = pairs[0]
        if pr >= 8:
            return BoardTexture.TRES_DRY
        if pr <= 3:
            return BoardTexture.INTERMEDIAIRE
        return BoardTexture.DRAWY

    # Unpaired — 7-high or lower
    if r1 <= 7:
        return BoardTexture.DRAWY

    # Two low connected cards (drawy for BB range)
    low_connected = r2 <= 7 and r3 <= 7 and (r2 - r3) <= 2

    # All cards in a 4-rank window
    highly_connected = (r1 - r3) <= 4

    if is_monotone and r1 <= 11:
        return BoardTexture.DRAWY

    # A or K high
    if r1 >= 13:
        if r2 >= 6 and (r2 - r3) >= 5:
            return BoardTexture.TRES_DRY
        return BoardTexture.INTERMEDIAIRE

    # Q / J / T / 9 / 8 high
    if r1 >= 8:
        if not has_flush_draw and not low_connected:
            return BoardTexture.TRES_DRY
        if highly_connected or is_monotone:
            return BoardTexture.DRAWY
        return BoardTexture.INTERMEDIAIRE

    return BoardTexture.DRAWY


# ─── Hand Evaluator ───────────────────────────────────────────────────────────

def _made_straight(cards: list[Card]) -> bool:
    vals = set(c.value for c in cards)
    if 14 in vals:
        vals.add(1)
    for lo in range(1, 11):
        if {lo, lo+1, lo+2, lo+3, lo+4}.issubset(vals):
            return True
    return False


def _oesd_or_gutshot(cards: list[Card]) -> tuple[bool, bool]:
    """Returns (has_oesd, has_gutshot) for any 4-card combo containing ≥1 hole card."""
    hole = cards[:2]
    oesd = False
    gut = False
    for combo in combinations(cards, 4):
        if not any(c in hole for c in combo):
            continue
        vals = sorted(set(c.value for c in combo))
        ext = list(vals)
        if 14 in ext:
            ext = sorted(set(ext + [1]))
        for i in range(len(ext) - 3):
            window = ext[i: i + 4]
            if len(window) != 4:
                continue
            span = window[-1] - window[0]
            if span == 3:
                oesd = True
            elif span == 4:
                gut = True
    return oesd, gut


def evaluate_hand(hole: list[Card], board: list[Card]) -> HandStrength:
    all5 = hole + board
    hv = sorted([c.value for c in hole], reverse=True)
    bv = sorted([c.value for c in board], reverse=True)
    b_set = set(bv)

    is_pocket_pair = hv[0] == hv[1]
    bv_count = Counter(bv)

    # Set
    if is_pocket_pair and hv[0] in b_set:
        return HandStrength.MONSTER

    # Trips (two board + one hole)
    for v in hv:
        if bv_count[v] == 2:
            return HandStrength.MONSTER

    # Two pair (two different hole cards each pair with board)
    matched = [v for v in set(hv) if v in b_set]
    if len(matched) == 2:
        return HandStrength.MONSTER

    # Flush
    max_suit = max(Counter(c.suit for c in all5).values())
    if max_suit >= 5:
        return HandStrength.MONSTER

    # Straight
    if _made_straight(all5):
        return HandStrength.MONSTER

    # Overpair
    if is_pocket_pair and hv[0] > bv[0]:
        return HandStrength.STRONG

    # Top pair (any kicker)
    if bv[0] in hv:
        return HandStrength.STRONG

    # Flush draw (exactly 4 of same suit involving a hole card)
    hole_suits = [c.suit for c in hole]
    suit_count_all = Counter(c.suit for c in all5)
    has_flush_draw = any(
        suit_count_all[s] == 4 and hole_suits.count(s) >= 1
        for s in suit_count_all
    )

    # OESD / gutshot
    has_oesd, has_gutshot = _oesd_or_gutshot(all5)

    # Middle pair
    if bv[1] in hv:
        kicker = max(v for v in hv if v != bv[1])
        if has_flush_draw or has_oesd:
            return HandStrength.DRAW_STRONG
        if has_gutshot:
            return HandStrength.DRAW_MEDIUM
        if kicker >= 7:
            return HandStrength.MEDIUM
        return HandStrength.WEAK

    # Bottom pair
    if bv[2] in hv:
        if has_flush_draw or has_oesd:
            return HandStrength.DRAW_STRONG
        if has_gutshot:
            return HandStrength.DRAW_MEDIUM
        return HandStrength.WEAK

    # Strong draw (no pair)
    if has_flush_draw or has_oesd:
        return HandStrength.DRAW_STRONG

    # Gutshot
    if has_gutshot:
        return HandStrength.DRAW_MEDIUM

    # Pocket pair below board (underpair)
    if is_pocket_pair:
        if hv[0] < bv[2]:
            return HandStrength.SD_VALUE
        return HandStrength.WEAK  # middle underpair

    # A/K-high or strong overcards → showdown value
    if max(hv) >= 13:
        return HandStrength.SD_VALUE

    # Backdoor flush (3 of same suit)
    has_backdoor = any(
        suit_count_all[s] == 3 and hole_suits.count(s) >= 1
        for s in suit_count_all
    )
    if has_backdoor:
        return HandStrength.BACKDOOR

    return HandStrength.AIR


# ─── Cbet Strategy (BTN/CO vs BB) ────────────────────────────────────────────

def get_cbet_sizing(texture: BoardTexture, stack_depth: int) -> int:
    deep = stack_depth >= 70
    table = {
        BoardTexture.TRES_DRY:     33 if deep else 25,
        BoardTexture.INTERMEDIAIRE: 50 if deep else 33,
        BoardTexture.DRAWY:         66 if deep else 50,
    }
    return table[texture]


def should_cbet(strength: HandStrength, texture: BoardTexture) -> bool:
    """
    BTN/CO vs BB cbet decision.
    TRES_DRY  → bet range (everything)
    INTERMEDIAIRE → bet 3/4 (monster/strong/medium/draw_strong/backdoor)
    DRAWY     → bet 1/2  (monster/strong/medium/draw_strong/backdoor)
    """
    if texture == BoardTexture.TRES_DRY:
        return True

    bet_strengths = {
        HandStrength.MONSTER,
        HandStrength.STRONG,
        HandStrength.MEDIUM,
        HandStrength.DRAW_STRONG,
        HandStrength.BACKDOOR,
    }
    return strength in bet_strengths


def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    hero_pos: str,
    stack_depth: int,
) -> dict:
    texture = classify_board_texture(board)
    strength = evaluate_hand(hole, board)
    do_bet = should_cbet(strength, texture)
    sizing = get_cbet_sizing(texture, stack_depth) if do_bet else None

    freq_label = {
        BoardTexture.TRES_DRY: 'range entier',
        BoardTexture.INTERMEDIAIRE: '3/4 des mains',
        BoardTexture.DRAWY: '1/2 des mains',
    }[texture]

    return {
        'texture': texture.value,
        'texture_label': TEXTURE_LABELS[texture.value],
        'cbet_frequency': freq_label,
        'hand_strength': strength.value,
        'hand_label': STRENGTH_LABELS[strength.value],
        'should_bet': do_bet,
        'correct_sizing': sizing,
    }
