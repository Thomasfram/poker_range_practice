"""
FastAPI backend for poker range practice web app.
"""

import os
import random
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

from .poker_hands import (
    generate_all_hands,
    find_closest_hand_in_range,
    find_bottom_of_range_category,
    Hand,
)
from .range_manager import RangeManager
from .flop import (
    Card as FlopCard,
    get_cbet_recommendation,
    get_bb_defense_recommendation,
    classify_board_vs_bb,
    BB_TEXTURE_LABELS,
    BoardTexture,
)


class EvalStartRequest(BaseModel):
    positions: list[str]
    stack_depths: list[str]


class EvalCheckRequest(BaseModel):
    hand: str
    scenario_action: str
    user_action: str
    position: str
    stack_depth: str


class StartRequest(BaseModel):
    position: str
    action: str
    stack_depth: str


class CheckAnswerRequest(BaseModel):
    hand: str
    action: str


class FlopHeroHandRequest(BaseModel):
    hero: str
    villain: str
    stackDepth: int


class CardData(BaseModel):
    rank: str
    suit: str


class CheckCbetRequest(BaseModel):
    hero_cards: list[CardData]
    board_cards: list[CardData]
    hero_position: str
    villain_position: str
    stack_depth: int
    user_action: str          # "bet" | "check"
    user_sizing: Optional[int] = None


class BoardInfoRequest(BaseModel):
    board_cards: list[CardData]


class BBDealRequest(BaseModel):
    villain_position: str
    stack_depth: int


class CheckBBDefenseRequest(BaseModel):
    hero_cards: list[CardData]
    board_cards: list[CardData]
    villain_position: str
    stack_depth: int
    user_action: str           # "fold" | "call" | "raise"
    user_sizing: Optional[float] = None  # XR multiplier if raise


_base_dir = Path(__file__).parent
_range_manager = RangeManager(str(_base_dir / "ranges.json"))
_all_hands = generate_all_hands()

_ALL_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
_ALL_SUITS = ['♠', '♥', '♦', '♣']


def _deal_concrete_hand(
    abstract: str,
    deck: list[tuple[str, str]],
) -> tuple[Optional[list[tuple[str, str]]], list[tuple[str, str]]]:
    """Instantiate an abstract hand (e.g. 'AKs') from `deck`. Returns (cards, new_deck) or (None, deck)."""
    deck = list(deck)
    rank1 = abstract[0]
    rank2 = abstract[1] if len(abstract) >= 2 else abstract[0]
    hand_type = abstract[2] if len(abstract) > 2 else 'pair'

    if hand_type == 'pair':
        opts = [(r, s) for r, s in deck if r == rank1]
        if len(opts) < 2:
            return None, deck
        c1, c2 = random.sample(opts, 2)
        deck.remove(c1)
        deck.remove(c2)
        return [c1, c2], deck

    if hand_type == 's':
        suit_order = random.sample(_ALL_SUITS, 4)
        for suit in suit_order:
            c1 = next(((r, s) for r, s in deck if r == rank1 and s == suit), None)
            c2 = next(((r, s) for r, s in deck if r == rank2 and s == suit), None)
            if c1 and c2:
                deck.remove(c1)
                deck.remove(c2)
                return [c1, c2], deck
        return None, deck

    # offsuit
    c1_opts = [(r, s) for r, s in deck if r == rank1]
    random.shuffle(c1_opts)
    for c1 in c1_opts:
        c2_opts = [(r, s) for r, s in deck if r == rank2 and s != c1[1]]
        if c2_opts:
            c2 = random.choice(c2_opts)
            deck.remove(c1)
            deck.remove(c2)
            return [c1, c2], deck
    return None, deck


def create_app() -> FastAPI:
    app = FastAPI()

    secret_key = os.environ.get("SECRET_KEY", "dev_key_for_poker_practice_local")
    app.add_middleware(SessionMiddleware, secret_key=secret_key)

    @app.get("/api/positions")
    def get_positions():
        return _range_manager.get_available_positions()

    @app.get("/api/actions/{position}")
    def get_actions(position: str):
        return _range_manager.get_available_actions(position)

    @app.get("/api/stack-depths/{position}/{action}")
    def get_stack_depths(position: str, action: str):
        return _range_manager.get_available_stack_depths(position, action)

    @app.post("/api/start")
    def start_practice(body: StartRequest, request: Request):
        current_range = _range_manager.get_range(body.position, body.action, body.stack_depth)
        if current_range is None:
            raise HTTPException(status_code=404, detail="Range not found")

        range_actions = _range_manager.get_available_range_actions(
            body.position, body.action, body.stack_depth
        )

        request.session["config"] = {
            "position": body.position,
            "action": body.action,
            "stack_depth": body.stack_depth,
        }

        return {
            "success": True,
            "range_size": len(current_range),
            "available_actions": range_actions,
        }

    @app.get("/api/next-hand")
    def get_next_hand(request: Request):
        config = request.session.get("config")
        if config is None:
            raise HTTPException(status_code=400, detail="No active practice session")

        current_range = _range_manager.get_range(
            config["position"], config["action"], config["stack_depth"]
        )
        if current_range is None:
            raise HTTPException(status_code=400, detail="No active practice session")

        hand = random.choice(_all_hands)
        return {"hand": str(hand)}

    @app.post("/api/check-answer")
    def check_answer(body: CheckAnswerRequest, request: Request):
        config = request.session.get("config")
        if config is None:
            raise HTTPException(status_code=400, detail="No active practice session")

        current_range = _range_manager.get_range(
            config["position"], config["action"], config["stack_depth"]
        )
        if current_range is None:
            raise HTTPException(status_code=400, detail="No active practice session")

        hand = Hand(body.hand)
        actual_action = current_range.get(hand, "fold")
        is_correct = body.action == actual_action

        response = {
            "correct": is_correct,
            "actual_action": actual_action,
            "user_action": body.action,
        }

        if not is_correct and actual_action == "fold":
            range_hands = set(current_range.keys())
            closest = find_closest_hand_in_range(hand, range_hands)
            if closest:
                response["closest_hand"] = str(closest)

        if is_correct and actual_action != "fold":
            specific_range_hands = [
                h for h, act in current_range.items() if act == actual_action
            ]
            bottom = find_bottom_of_range_category(hand, specific_range_hands)
            if bottom:
                response["bottom_of_range"] = str(bottom)

        return response

    @app.post("/api/flop/hero-hand")
    def get_flop_hero_hand(body: FlopHeroHandRequest):
        stack_depth = f"{body.stackDepth}bb"

        action = "open"
        if body.hero == "BB":
            if body.villain == "BTN":
                action = "vs BTN"
            elif body.villain == "CO":
                action = "vs CO"
            elif body.villain == "SB":
                action = "vs sb_raise"
        elif body.hero == "BTN":
            if body.villain == "BB":
                action = "vs BB"
        elif body.hero == "SB":
            action = "open"

        current_range = _range_manager.get_range(body.hero, action, stack_depth)

        valid_hands = []
        if current_range:
            valid_hands = [str(h) for h, act in current_range.items() if act != "fold"]

        if not valid_hands:
            valid_hands = [str(h) for h in _all_hands]

        chosen_hand = random.choice(valid_hands)
        return {"hand": chosen_hand, "action_used": action}

    @app.post("/api/flop/check-cbet")
    def check_cbet(body: CheckCbetRequest):
        supported = {
            "BTN": ("BB", "SB"),
            "CO":  ("BB",),
            "SB":  ("BB",),
        }
        if body.hero_position not in supported:
            raise HTTPException(status_code=400, detail=f"Position héro non supportée : {body.hero_position}")
        if body.villain_position not in supported[body.hero_position]:
            raise HTTPException(
                status_code=400,
                detail=f"Situation {body.hero_position} vs {body.villain_position} non supportée"
            )

        hole = [FlopCard(c.rank, c.suit) for c in body.hero_cards]
        board = [FlopCard(c.rank, c.suit) for c in body.board_cards]

        rec = get_cbet_recommendation(
            hole, board, body.hero_position, body.villain_position, body.stack_depth
        )

        user_bets = body.user_action == "bet"
        is_correct = user_bets == rec["should_bet"]

        if is_correct and user_bets and body.user_sizing is not None:
            is_correct = abs(body.user_sizing - rec["correct_sizing"]) <= 8

        return {
            "correct": is_correct,
            "correct_action": "bet" if rec["should_bet"] else "check",
            "correct_sizing": rec["correct_sizing"],
            "texture": rec["texture"],
            "texture_label": rec["texture_label"],
            "cbet_frequency": rec["cbet_frequency"],
            "hand_strength": rec["hand_strength"],
            "hand_label": rec["hand_label"],
        }

    @app.post("/api/flop/bb-deal")
    def bb_deal(body: BBDealRequest):
        if body.villain_position not in ('BTN', 'CO'):
            raise HTTPException(status_code=400, detail="Villain doit être BTN ou CO")

        stack_str = f"{body.stack_depth}bb"

        # BB's calling range
        bb_action = f"vs {body.villain_position}"
        bb_range = _range_manager.get_range('BB', bb_action, stack_str) or {}
        valid_bb = [str(h) for h, act in bb_range.items() if act != 'fold']
        if not valid_bb:
            valid_bb = [str(h) for h in _all_hands]

        # Villain's opening range
        villain_range = _range_manager.get_range(body.villain_position, 'open', stack_str) or {}
        valid_villain = [str(h) for h, act in villain_range.items() if act != 'fold']
        if not valid_villain:
            valid_villain = [str(h) for h in _all_hands]

        # Build and shuffle deck
        deck: list[tuple[str, str]] = [(r, s) for r in _ALL_RANKS for s in _ALL_SUITS]
        random.shuffle(deck)

        # Deal BB hand
        bb_abstract = random.choice(valid_bb)
        bb_cards, deck = _deal_concrete_hand(bb_abstract, deck)
        if bb_cards is None:
            bb_abstract = random.choice(valid_bb)
            bb_cards, deck = _deal_concrete_hand(bb_abstract, deck)
        if bb_cards is None:
            bb_cards = [deck.pop(0), deck.pop(0)]

        # Burn + deal flop
        deck.pop(0)
        flop = [deck.pop(0), deck.pop(0), deck.pop(0)]
        flop_cards = [FlopCard(r, s) for r, s in flop]

        # Board texture for villain cbet sizing
        texture = classify_board_vs_bb(flop_cards)
        villain_sizing = {
            BoardTexture.EXTRA_DRY:      25,
            BoardTexture.INTERMEDIAIRE:  33,
            BoardTexture.DRAWY:          50,
        }[texture]

        # Filter villain range to hands that cbet on this flop
        cbet_candidates: list[tuple[str, list[tuple[str, str]]]] = []
        for villain_abstract in valid_villain:
            v_cards, _ = _deal_concrete_hand(villain_abstract, list(deck))
            if v_cards is None:
                continue
            v_hole = [FlopCard(r, s) for r, s in v_cards]
            try:
                rec = get_cbet_recommendation(
                    v_hole, flop_cards, body.villain_position, 'BB', body.stack_depth
                )
                if rec['should_bet']:
                    cbet_candidates.append((villain_abstract, v_cards))
            except Exception:
                pass

        if cbet_candidates:
            villain_abstract, villain_cards = random.choice(cbet_candidates)
        else:
            # Fallback: any instantiable villain hand
            villain_abstract, villain_cards = None, None
            random.shuffle(valid_villain)
            for va in valid_villain:
                vc, _ = _deal_concrete_hand(va, list(deck))
                if vc is not None:
                    villain_abstract, villain_cards = va, vc
                    break
            if villain_cards is None:
                villain_cards = [deck.pop(0), deck.pop(0)]

        return {
            'bb_hand':         bb_abstract,
            'bb_cards':        [{'rank': r, 'suit': s} for r, s in bb_cards],
            'flop_cards':      [{'rank': r, 'suit': s} for r, s in flop],
            'villain_hand':    villain_abstract,
            'villain_cards':   [{'rank': r, 'suit': s} for r, s in villain_cards],
            'villain_sizing':  villain_sizing,
            'texture':         texture.value,
            'texture_label':   BB_TEXTURE_LABELS[texture.value],
        }

    @app.post("/api/flop/board-info")
    def get_board_info(body: BoardInfoRequest):
        board = [FlopCard(c.rank, c.suit) for c in body.board_cards]
        texture = classify_board_vs_bb(board)
        villain_sizing = {
            BoardTexture.EXTRA_DRY:      25,
            BoardTexture.INTERMEDIAIRE:  33,
            BoardTexture.DRAWY:          50,
        }[texture]
        return {
            'texture':        texture.value,
            'texture_label':  BB_TEXTURE_LABELS[texture.value],
            'villain_sizing': villain_sizing,
        }

    @app.post("/api/flop/bb-defense")
    def check_bb_defense(body: CheckBBDefenseRequest):
        if body.villain_position not in ('BTN', 'CO'):
            raise HTTPException(status_code=400, detail=f"Villain non supporté: {body.villain_position}")

        hole  = [FlopCard(c.rank, c.suit) for c in body.hero_cards]
        board = [FlopCard(c.rank, c.suit) for c in body.board_cards]

        rec = get_bb_defense_recommendation(hole, board, body.stack_depth)

        is_correct = body.user_action == rec['action']
        if is_correct and body.user_action == 'raise' and body.user_sizing is not None:
            correct_mult = rec['raise_sizing'] or 0
            is_correct = abs(body.user_sizing - correct_mult) <= 0.5

        return {
            'correct':         is_correct,
            'correct_action':  rec['action'],
            'correct_sizing':  rec['raise_sizing'],
            'texture':         rec['texture'],
            'texture_label':   rec['texture_label'],
            'villain_sizing':  rec['villain_sizing'],
            'hand_strength':   rec['hand_strength'],
            'hand_label':      rec['hand_label'],
        }

    # ── Eval mode ──────────────────────────────────────────────────────────────

    @app.get("/api/eval/stack-depths/{position}")
    def eval_stack_depths(position: str):
        return _range_manager.get_eval_stack_depths(position)

    @app.post("/api/eval/start")
    def eval_start(body: EvalStartRequest, request: Request):
        combos = []
        for pos in body.positions:
            for depth in body.stack_depths:
                scenarios = _range_manager.get_eval_scenarios(pos, depth)
                if scenarios:
                    combos.append({"position": pos, "stack_depth": depth, "scenario_count": len(scenarios)})
        if not combos:
            raise HTTPException(status_code=404, detail="Aucun scénario disponible")
        request.session["eval_config"] = {"combos": combos}
        total_scenarios = sum(c["scenario_count"] for c in combos)
        return {"success": True, "scenario_count": total_scenarios}

    @app.get("/api/eval/next-hand")
    def eval_next_hand(request: Request):
        config = request.session.get("eval_config")
        if config is None:
            raise HTTPException(status_code=400, detail="No active eval session")
        combo = random.choice(config["combos"])
        scenarios = _range_manager.get_eval_scenarios(combo["position"], combo["stack_depth"])
        if not scenarios:
            raise HTTPException(status_code=400, detail="No scenarios available")
        scenario = random.choice(scenarios)

        hand = None
        parent_open = scenario.get('parent_open')
        if parent_open:
            parent_pos, parent_action = parent_open
            parent_range = _range_manager.get_range(parent_pos, parent_action, combo['stack_depth'])
            if parent_range:
                opened_hands = [h for h, act in parent_range.items() if act != 'fold']
                if opened_hands:
                    hand = random.choice(opened_hands)
        if hand is None:
            hand = random.choice(_all_hands)

        return {
            "hand": str(hand),
            "position":           combo["position"],
            "stack_depth":        combo["stack_depth"],
            "scenario_action":    scenario["action"],
            "scenario_label":     scenario["label"],
            "available_actions":  scenario["available_actions"],
        }

    @app.post("/api/eval/check-answer")
    def eval_check_answer(body: EvalCheckRequest, request: Request):
        if request.session.get("eval_config") is None:
            raise HTTPException(status_code=400, detail="No active eval session")
        current_range = _range_manager.get_range(
            body.position, body.scenario_action, body.stack_depth
        )
        if current_range is None:
            raise HTTPException(status_code=400, detail="Range not found")

        hand = Hand(body.hand)
        actual_action = current_range.get(hand, "fold")
        is_correct = body.user_action == actual_action

        response = {
            "correct":      is_correct,
            "actual_action": actual_action,
            "user_action":  body.user_action,
        }
        if not is_correct and actual_action == "fold":
            closest = find_closest_hand_in_range(hand, set(current_range.keys()))
            if closest:
                response["closest_hand"] = str(closest)
        if is_correct and actual_action != "fold":
            specific = [h for h, act in current_range.items() if act == actual_action]
            bottom = find_bottom_of_range_category(hand, specific)
            if bottom:
                response["bottom_of_range"] = str(bottom)
        return response

    # Static files mounted last so API routes take precedence
    app.mount("/", StaticFiles(directory=str(_base_dir / "static"), html=True), name="static")

    return app


def main():
    import uvicorn
    print("Starting Poker Range Practice App...")
    print("Open your browser to: http://localhost:5000")
    uvicorn.run("poker_range_practice:create_app", factory=True, host="0.0.0.0", port=5000, reload=True)


if __name__ == "__main__":
    main()
