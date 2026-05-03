from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from itertools import combinations

RANK_VALUES = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
}

STRENGTH_LABELS = {
    'monster':     'Main forte (set / deux paires / quinte / couleur)',
    'strong':      'Main forte (top paire ou overpair)',
    'medium':      'Paire milieu bon kicker (7+)',
    'weak':        'Paire faible / paire milieu mauvais kicker',
    'draw_strong': 'Tirage fort (flush draw / OESD)',
    'draw_medium': 'Tirage faible (gutshot / paire + gutshot)',
    'backdoor':    'Backdoor draw uniquement',
    'sd_value':    'Showdown value (A/K-high, underpair)',
    'air':         'Air (sans tirage)',
}


@dataclass
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]


class HandStrength(str, Enum):
    MONSTER     = 'monster'
    STRONG      = 'strong'
    MEDIUM      = 'medium'
    WEAK        = 'weak'
    DRAW_STRONG = 'draw_strong'
    DRAW_MEDIUM = 'draw_medium'
    BACKDOOR    = 'backdoor'
    SD_VALUE    = 'sd_value'
    AIR         = 'air'


def _made_straight(cards: list[Card]) -> bool:
    vals = set(c.value for c in cards)
    if 14 in vals:
        vals.add(1)
    for lo in range(1, 11):
        if {lo, lo + 1, lo + 2, lo + 3, lo + 4}.issubset(vals):
            return True
    return False


def _oesd_or_gutshot(cards: list[Card]) -> tuple[bool, bool]:
    """Returns (has_oesd, has_gutshot) for any 4-card combo containing ≥1 hole card."""
    hole = cards[:2]
    oesd = gut = False
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
    # Two pair: two different hole cards each match a board card
    if len([v for v in set(hv) if v in b_set]) == 2:
        return HandStrength.MONSTER
    # Pocket pair + board trips = full house (e.g. TT on JJJ)
    # Note: pocket pair matching a board pair (TT on JJ4) is caught by the set check above
    if is_pocket_pair and any(cnt >= 3 for cnt in bv_count.values()):
        return HandStrength.MONSTER
    # Flush
    if max(Counter(c.suit for c in all5).values()) >= 5:
        return HandStrength.MONSTER
    # Straight
    if _made_straight(all5):
        return HandStrength.MONSTER
    # Overpair
    if is_pocket_pair and hv[0] > bv[0]:
        return HandStrength.STRONG
    # Top pair
    if bv[0] in hv:
        return HandStrength.STRONG

    hole_suits = [c.suit for c in hole]
    suit_count_all = Counter(c.suit for c in all5)
    has_flush_draw = any(
        suit_count_all[s] == 4 and hole_suits.count(s) >= 1
        for s in suit_count_all
    )
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

    if has_flush_draw or has_oesd:
        return HandStrength.DRAW_STRONG
    if has_gutshot:
        return HandStrength.DRAW_MEDIUM

    # Pocket pair below top board card (overpair already handled above)
    # e.g. TT on JJ4: above the 4 → MEDIUM; 33 on JJ4: below the 4 → SD_VALUE
    if is_pocket_pair:
        return HandStrength.SD_VALUE if hv[0] < bv[2] else HandStrength.MEDIUM

    # A/K overcards
    if max(hv) >= 13:
        return HandStrength.SD_VALUE

    # Backdoor flush
    has_backdoor = any(
        suit_count_all[s] == 3 and hole_suits.count(s) >= 1
        for s in suit_count_all
    )
    return HandStrength.BACKDOOR if has_backdoor else HandStrength.AIR
