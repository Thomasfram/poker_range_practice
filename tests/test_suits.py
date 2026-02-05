"""Test suit/offsuit strict matching."""
from poker_hands import parse_range_notation, find_bottom_of_range_category, find_closest_hand_in_range, Hand

# Range: A2s+ (all suited aces), ATo+ (high offsuit aces only)
range_str = "A2s+, ATo+"
range_hands = parse_range_notation(range_str)

print(f"Range: {range_str}\n")

# Test 1: Hand A9s (Suited)
# Should match against suited aces. Bottom of A2s+ is A2s.
hand1 = Hand("A9s")
bottom1 = find_bottom_of_range_category(hand1, range_hands)
print(f"Hand {hand1} (Suited). Expect bottom of suited checks -> A2s")
print(f"Result: {bottom1}")
print()

# Test 2: Hand AKo (Offsuit)
# Should match against offsuit aces. Bottom of ATo+ is ATo.
# Should NOT match against A2s (suited).
hand2 = Hand("AKo")
bottom2 = find_bottom_of_range_category(hand2, range_hands)
print(f"Hand {hand2} (Offsuit). Expect bottom of offsuit checks -> ATo")
print(f"Result: {bottom2}")
print()

# Test 3: Hand A9o (Offsuit, OUT of range)
# Closest IN range should be ATo (closest offsuit).
# Should NOT be A9s (suited) even if rank matches perfectly.
hand3 = Hand("A9o")
closest3 = find_closest_hand_in_range(hand3, range_hands)
print(f"Hand {hand3} (Offsuit, OUT). Closest IN range should be ATo (Offsuit match > Rank match with wrong suit)")
# Current logic: "Same high card & suitedness (closest low card)" is rule #1.
print(f"Result: {closest3}")
