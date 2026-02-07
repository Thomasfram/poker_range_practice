
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000"

def test_api():
    print("Testing API...")
    s = requests.Session()
    
    # 1. Start Session (Complex Range)
    print("\n1. Start Session (BB vs BTN 50bb)...")
    payload = {
        "position": "BB",
        "action": "3bet vs BTN",
        "stack_depth": "50bb"
    }
    try:
        r = s.post(f"{BASE_URL}/api/start", json=payload, timeout=5)
        if r.status_code != 200:
            print(f"FAIL: Status {r.status_code}, Body: {r.text}")
            sys.exit(1)
            
        data = r.json()
        print(f"Response: {data}")
        
        if "available_actions" not in data:
            print("FAIL: available_actions missing")
            sys.exit(1)
        
        actions = data["available_actions"]
        if "3bet" not in actions or "call" not in actions:
            print(f"FAIL: Expected 3bet/call in actions, got {actions}")
            sys.exit(1)
            
        print("PASS: Start Session")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    # 2. Check Answer (Correct 3bet)
    print("\n2. Check Answer (AA -> 3bet)...")
    payload = {
        "hand": "AA",
        "action": "3bet"
    }
    try:
        r = s.post(f"{BASE_URL}/api/check-answer", json=payload, timeout=5)
        if r.status_code != 200:
            print(f"FAIL: check-answer Status {r.status_code}, Body: {r.text}")
            sys.exit(1)
            
        data = r.json()
        print(f"Response: {data}")
        
        if not data.get("correct"):
            print("FAIL: AA should be correct 3bet")
            sys.exit(1)
        if data.get("actual_action") != "3bet":
            print(f"FAIL: actual_action should be 3bet, got {data.get('actual_action')}")
            sys.exit(1)
            
        print("PASS: AA -> 3bet")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    # 3. Check Answer (Incorrect Call on 3bet hand)
    print("\n3. Check Answer (AA -> call)...")
    payload = {
        "hand": "AA",
        "action": "call"
    }
    try:
        r = s.post(f"{BASE_URL}/api/check-answer", json=payload, timeout=5)
        data = r.json()
        print(f"Response: {data}")
        
        if data.get("correct"):
            print("FAIL: AA -> call should be incorrect")
            sys.exit(1)
        if data.get("actual_action") != "3bet":
            print("FAIL: actual_action should be 3bet")
            sys.exit(1)
            
        print("PASS: AA -> call (Incorrect)")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    # 4. Check Answer (Fold)
    print("\n4. Check Answer (72o -> fold)...")
    payload = {
        "hand": "72o",
        "action": "fold"
    }
    try:
        r = s.post(f"{BASE_URL}/api/check-answer", json=payload, timeout=5)
        data = r.json()
        print(f"Response: {data}")
        
        if not data.get("correct"):
            print("FAIL: 72o -> fold should be correct")
            sys.exit(1)
            
        print("PASS: 72o -> fold")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    test_api()
