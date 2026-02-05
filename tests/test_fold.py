"""Test correct fold feedback."""
from poker_hands import parse_range_notation, find_closest_hand_in_range, Hand

# Range: ATo+ (ATo, AJo, AQo, AKo)
range_str = "ATo+"
range_hands = parse_range_notation(range_str)

print(f"Range: {range_str}\n")

# Scenario: User has A9o and folds. (Correct Fold)
# We want to show "Bottom of range: ATo"
hand = Hand("A9o")
closest = find_closest_hand_in_range(hand, range_hands)

print(f"Hand: {hand} (Out of range)")
print(f"Closest IN range (Boundary): {closest}")
print("This is what will be shown as 'Bottom of range' when user correctly folds.")
