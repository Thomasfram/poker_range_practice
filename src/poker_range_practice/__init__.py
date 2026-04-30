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
from .flop_strategy import Card as FlopCard, get_cbet_recommendation


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


_base_dir = Path(__file__).parent
_range_manager = RangeManager(str(_base_dir / "ranges.json"))
_all_hands = generate_all_hands()


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
            action = "open_limp"

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
        if body.hero_position not in ("BTN", "CO"):
            raise HTTPException(status_code=400, detail="Position non supportée pour l'instant (BTN/CO uniquement)")
        if body.villain_position != "BB":
            raise HTTPException(status_code=400, detail="Villain non supporté pour l'instant (BB uniquement)")

        hole = [FlopCard(c.rank, c.suit) for c in body.hero_cards]
        board = [FlopCard(c.rank, c.suit) for c in body.board_cards]

        rec = get_cbet_recommendation(hole, board, body.hero_position, body.stack_depth)

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
