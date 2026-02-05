"""Test the bottom of range functionality."""
from poker_hands import parse_range_notation, generate_all_hands, find_closest_out_of_range, Hand

# Test with a simple range
test_range = "A9o+, A5s+"
range_hands = parse_range_notation(test_range)
all_hands = generate_all_hands()

print(f"Range: {test_range}")
print(f"Hands in range: {sorted([str(h) for h in range_hands])}")
print()

# Test with a hand IN range
test_hand = Hand("A9o")
print(f"Testing with {test_hand} (should be IN range)")
print(f"Is in range: {test_hand in range_hands}")

bottom = find_closest_out_of_range(test_hand, range_hands, all_hands)
print(f"Bottom of range: {bottom}")
print()

# Test with another hand IN range
test_hand2 = Hand("AJs")
print(f"Testing with {test_hand2} (should be IN range)")
print(f"Is in range: {test_hand2 in range_hands}")

bottom2 = find_closest_out_of_range(test_hand2, range_hands, all_hands)
print(f"Bottom of range: {bottom2}")
