"""Test the improved bottom of range logic."""
from poker_hands import parse_range_notation, generate_all_hands, find_bottom_of_range_category, find_closest_hand_in_range, Hand

# Test range: A5s+ (A5s...AKs)
range_str = "A5s+"
range_hands = parse_range_notation(range_str)

print(f"Range: {range_str}")

# Case 1: A9s (In range)
hand1 = Hand("A9s")
bottom1 = find_bottom_of_range_category(hand1, range_hands)
print(f"Hand {hand1} (In range). Bottom should be A5s.")
print(f"Result: {bottom1}")
print()

# Case 2: A4s (Out of range) - strictly closest hand in range
hand2 = Hand("A4s")
closest2 = find_closest_hand_in_range(hand2, range_hands)
print(f"Hand {hand2} (Out of range). Closest IN range should be A5s.")
print(f"Result: {closest2}")
print()

# Case 3: 72o (Out of range) - no 7x in range. Range: 99+, AJs+
range_str_3 = "99+, AJs+"
range_hands_3 = parse_range_notation(range_str_3)
hand3 = Hand("72o") # Out
# Closest should be something with closest high card to 7. that is 9. so probably 99 (pair? excluded?) or...
# Wait, AJs+ is AJs, AQs, AKs. 99+ is pairs.
# If exclude pairs... then AJs/AQs/AKs are only options.
# Closest high card to 7 is A (rank 12 vs 5).
# If range had T9s...
range_str_4 = "T9s"
range_hands_4 = parse_range_notation(range_str_4)
closest3 = find_closest_hand_in_range(hand3, range_hands_4) 
# 72o vs T9s (suited? 72o is offsuit).
# If no offsuit candidates, returns closest suited? 
# My code: candidates_suiting = [h for h in non_pair_hands if h.is_suited == hand.is_suited]
# If 72o (off) and range only T9s (suited). candidates_suiting is empty.
# Fallback to non_pair_hands.
# strict_priority_sort: rank1 dist (7 vs T = 3). rank2 dist (2 vs 9 = 7).
print(f"Hand {hand3} (Out) vs Range {range_str_4}. Closest should be T9s (only choice).")
print(f"Result: {closest3}")
print()


# Case 4: 95o out of range. Range 96o+.
range_str_5 = "96o+"
range_hands_5 = parse_range_notation(range_str_5)
hand5 = Hand("95o")
closest5 = find_closest_hand_in_range(hand5, range_hands_5)
print(f"Hand {hand5} (Out) vs Range {range_str_5}. Closest should be 96o.")
print(f"Result: {closest5}")
