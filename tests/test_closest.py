"""Quick test to verify closest hand calculation."""
from poker_hands import Hand, parse_range_notation, find_closest_hand_in_range

# Test range
test_range_str = "22+, A2s+, ATo+, K9s+, KJo+, Q9s+, QJo, J9s+, JTo, T8s+, T9o, 98s, 87s, 76s, 65s, 54s"
range_hands = parse_range_notation(test_range_str)

print(f"Testing closest hand calculation...")
print(f"Range has {len(range_hands)} hands\n")

# Test cases
test_cases = [
    ("T5o", "Should be T9o or T8s"),
    ("K7o", "Should be KJo or K9s"),
    ("A9o", "Should be ATo"),
    ("33", "Should be in range (33 is in 22+)"),
]

for hand_str, expected in test_cases:
    hand = Hand(hand_str)
    in_range = hand in range_hands
    
    if in_range:
        print(f"✓ {hand} IS in range - {expected}")
    else:
        closest = find_closest_hand_in_range(hand, range_hands)
        print(f"✗ {hand} is NOT in range")
        print(f"  Closest: {closest} - {expected}")
    print()
