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


@dataclass
class Card:
    rank: str
    suit: str

    @property
    def value(self) -> int:
        return RANK_VALUES[self.rank]


class HandStrength(str, Enum):
    MONSTER   = 'monster'
    STRONG    = 'strong'
    MEDIUM    = 'medium'
    WEAK      = 'weak'
    DRAW_STRONG = 'draw_strong'
    DRAW_MEDIUM = 'draw_medium'
    BACKDOOR  = 'backdoor'
    SD_VALUE  = 'sd_value'
    AIR       = 'air'


# ─── Hand Evaluator (shared) ─────────────────────────────────────────────────

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
    # Two pair: pocket pair + board pair (e.g. TT on JJ4)
    if is_pocket_pair and any(cnt >= 2 for cnt in bv_count.values()):
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

    # Pocket underpair / middle underpair
    if is_pocket_pair:
        return HandStrength.SD_VALUE if hv[0] < bv[2] else HandStrength.WEAK

    # A/K overcards
    if max(hv) >= 13:
        return HandStrength.SD_VALUE

    # Backdoor flush
    has_backdoor = any(
        suit_count_all[s] == 3 and hole_suits.count(s) >= 1
        for s in suit_count_all
    )
    return HandStrength.BACKDOOR if has_backdoor else HandStrength.AIR


# ═══════════════════════════════════════════════════════════════════════════════
#  BTN / CO  vs  BB
# ═══════════════════════════════════════════════════════════════════════════════

class BoardTexture(str, Enum):
    EXTRA_DRY    = 'TRES_DRY'
    INTERMEDIAIRE = 'INTERMEDIAIRE'
    DRAWY       = 'DRAWY'


BB_TEXTURE_LABELS = {
    'TRES_DRY':     'Très Dry',
    'INTERMEDIAIRE': 'Intermédiaire',
    'DRAWY':        'Drawy',
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

    low_connected  = r2 <= 7 and r3 <= 7 and (r2 - r3) <= 2
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


def _sizing_vs_bb(texture: BoardTexture, stack_depth: int) -> int:
    deep = stack_depth >= 70
    return {
        BoardTexture.EXTRA_DRY:      33 if deep else 25,
        BoardTexture.INTERMEDIAIRE:  50 if deep else 33,
        BoardTexture.DRAWY:          66 if deep else 50,
    }[texture]


def _should_bet_vs_bb(strength: HandStrength, texture: BoardTexture) -> bool:
    if texture == BoardTexture.EXTRA_DRY:
        return True
    return strength in {
        HandStrength.MONSTER, HandStrength.STRONG, HandStrength.MEDIUM,
        HandStrength.DRAW_STRONG, HandStrength.BACKDOOR,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  BTN  vs  SB
# ═══════════════════════════════════════════════════════════════════════════════

class SbCategory(str, Enum):
    # Best flops (range bet or high freq)
    RANGE_LOW_MID_PAIR = 'range_low_mid_pair'  # pairé 2-9  → 100%, 33%
    RANGE_NINE_EIGHT   = 'range_nine_eight'    # 9/8 high   → 100%, 50%
    RANGE_LOW_BOARD    = 'range_low_board'     # ≤7 high    → 100%, 50%
    QJT_HIGH           = 'qjt_high'           # Q/J/T high (1 broadway) → 66%, 50%
    DOUBLE_BROADWAY    = 'double_broadway'     # 2+ broadway → 66%, 50%
    # Average flops
    AK_DRY             = 'ak_dry'             # A/K high sec → 66%, 33%
    # Bad flops
    HIGH_PAIR          = 'high_pair'          # pairé T+    → 30%, 33%
    AK_DRAWY           = 'ak_drawy'           # A/K high drawy → 50%, 50%
    MONOCOLOR          = 'monocolor'          # monotone → <50%, 33%


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

    # Monotone overrides everything
    if max_suit == 3:
        return SbCategory.MONOCOLOR

    pairs = [r for r, cnt in Counter(vals).items() if cnt >= 2]
    if pairs:
        pr = pairs[0]
        return SbCategory.HIGH_PAIR if pr >= 10 else SbCategory.RANGE_LOW_MID_PAIR

    # Unpaired boards
    if r1 <= 7:
        return SbCategory.RANGE_LOW_BOARD

    if r1 <= 9:  # 8 or 9 high
        return SbCategory.RANGE_NINE_EIGHT

    if r1 >= 13:  # A or K high
        dry = r2 >= 6 and (r2 - r3) >= 5
        return SbCategory.AK_DRY if dry else SbCategory.AK_DRAWY

    # T / J / Q high (r1 in 10-12)
    broadway_count = sum(1 for v in vals if v >= 10)
    return SbCategory.DOUBLE_BROADWAY if broadway_count >= 2 else SbCategory.QJT_HIGH


def _sizing_vs_sb(cat: SbCategory) -> int:
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


def _should_bet_vs_sb(strength: HandStrength, cat: SbCategory) -> bool:
    # Range bet boards
    if cat in (SbCategory.RANGE_LOW_MID_PAIR,
               SbCategory.RANGE_NINE_EIGHT,
               SbCategory.RANGE_LOW_BOARD):
        return True

    # 30% freq — only best monsters
    if cat == SbCategory.HIGH_PAIR:
        return strength == HandStrength.MONSTER

    # 66% freq boards (QJT, double broadway, AK dry)
    if cat in (SbCategory.QJT_HIGH, SbCategory.DOUBLE_BROADWAY, SbCategory.AK_DRY):
        return strength in {
            HandStrength.MONSTER, HandStrength.STRONG, HandStrength.MEDIUM,
            HandStrength.DRAW_STRONG, HandStrength.BACKDOOR,
        }

    # 50% freq — AK drawy
    if cat == SbCategory.AK_DRAWY:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG, HandStrength.DRAW_STRONG}

    # Monocolor — only made hands
    if cat == SbCategory.MONOCOLOR:
        return strength in {HandStrength.MONSTER, HandStrength.STRONG}

    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  Public entry-point
# ═══════════════════════════════════════════════════════════════════════════════

def get_cbet_recommendation(
    hole: list[Card],
    board: list[Card],
    hero_pos: str,
    villain_pos: str,
    stack_depth: int,
) -> dict:
    strength = evaluate_hand(hole, board)

    if villain_pos == 'BB':
        texture  = classify_board_vs_bb(board)
        do_bet   = _should_bet_vs_bb(strength, texture)
        sizing   = _sizing_vs_bb(texture, stack_depth) if do_bet else None
        freq_lbl = {
            BoardTexture.EXTRA_DRY:      'range entier',
            BoardTexture.INTERMEDIAIRE: '3/4 des mains',
            BoardTexture.DRAWY:         '1/2 des mains',
        }[texture]
        return {
            'texture':        texture.value,
            'texture_label':  BB_TEXTURE_LABELS[texture.value],
            'cbet_frequency': freq_lbl,
            'hand_strength':  strength.value,
            'hand_label':     STRENGTH_LABELS[strength.value],
            'should_bet':     do_bet,
            'correct_sizing': sizing,
        }

    if villain_pos == 'SB':
        cat    = classify_board_vs_sb(board)
        do_bet = _should_bet_vs_sb(strength, cat)
        sizing = _sizing_vs_sb(cat) if do_bet else None
        return {
            'texture':        cat.value,
            'texture_label':  SB_CATEGORY_LABELS[cat.value],
            'cbet_frequency': SB_FREQ_LABELS[cat.value],
            'hand_strength':  strength.value,
            'hand_label':     STRENGTH_LABELS[strength.value],
            'should_bet':     do_bet,
            'correct_sizing': sizing,
        }

    raise ValueError(f"Villain non supporté: {villain_pos}")


# ═══════════════════════════════════════════════════════════════════════════════
#  BB  vs  BTN/CO  — Defense (check-raise / call / fold)
# ═══════════════════════════════════════════════════════════════════════════════

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
        elif len([v for v in hv if v not in b_set]) >= 2 and has_bd_flush:
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
