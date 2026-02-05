"""
Poker hand representation and range expansion logic.
"""

class Hand:
    """Represents a poker starting hand."""
    
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    RANK_VALUES = {r: i for i, r in enumerate(RANKS)}
    
    def __init__(self, hand_str):
        """
        Initialize a hand from string notation.
        Examples: 'AA', 'AKs', 'T9o'
        """
        self.hand_str = hand_str.strip()
        self.parse()
    
    def parse(self):
        """Parse the hand string into components."""
        if len(self.hand_str) < 2:
            raise ValueError(f"Invalid hand: {self.hand_str}")
        
        self.rank1 = self.hand_str[0]
        self.rank2 = self.hand_str[1]
        
        # Validate ranks
        if self.rank1 not in self.RANKS or self.rank2 not in self.RANKS:
            raise ValueError(f"Invalid ranks in hand: {self.hand_str}")
        
        # Ensure rank1 >= rank2 for consistency
        if self.RANK_VALUES[self.rank1] < self.RANK_VALUES[self.rank2]:
            self.rank1, self.rank2 = self.rank2, self.rank1
        
        # Determine if pair, suited, or offsuit
        if self.rank1 == self.rank2:
            self.is_pair = True
            self.is_suited = None
        else:
            self.is_pair = False
            if len(self.hand_str) >= 3:
                suit_char = self.hand_str[2].lower()
                if suit_char == 's':
                    self.is_suited = True
                elif suit_char == 'o':
                    self.is_suited = False
                else:
                    raise ValueError(f"Invalid suit designation: {self.hand_str}")
            else:
                raise ValueError(f"Non-pair hands must specify s or o: {self.hand_str}")
    
    def __str__(self):
        """Return canonical string representation."""
        if self.is_pair:
            return f"{self.rank1}{self.rank2}"
        else:
            return f"{self.rank1}{self.rank2}{'s' if self.is_suited else 'o'}"
    
    def __eq__(self, other):
        """Check equality with another hand."""
        if not isinstance(other, Hand):
            return False
        return str(self) == str(other)
    
    def __hash__(self):
        """Make Hand hashable for use in sets."""
        return hash(str(self))
    
    def __repr__(self):
        return f"Hand('{self}')"
    
    def distance_to(self, other):
        """
        Calculate a simple distance metric to another hand.
        Used to find the "closest" hand in range.
        """
        # Simple heuristic: sum of rank differences
        rank1_diff = abs(self.RANK_VALUES[self.rank1] - self.RANK_VALUES[other.rank1])
        rank2_diff = abs(self.RANK_VALUES[self.rank2] - self.RANK_VALUES[other.rank2])
        
        # Penalize if suited/offsuit differs
        suit_penalty = 0
        if not self.is_pair and not other.is_pair:
            if self.is_suited != other.is_suited:
                suit_penalty = 1
        
        return rank1_diff + rank2_diff + suit_penalty


def generate_all_hands():
    """Generate all 169 possible starting hands."""
    hands = []
    
    # Pairs
    for rank in Hand.RANKS:
        hands.append(Hand(f"{rank}{rank}"))
    
    # Non-pairs
    for i, rank1 in enumerate(Hand.RANKS):
        for rank2 in Hand.RANKS[:i]:  # rank2 < rank1
            hands.append(Hand(f"{rank1}{rank2}s"))
            hands.append(Hand(f"{rank1}{rank2}o"))
    
    return hands


def parse_range_notation(range_str):
    """
    Parse compact range notation into a set of Hand objects.
    
    Examples:
        "22+" -> all pairs from 22 to AA
        "A2s+" -> all suited aces from A2s to AKs
        "ATo+" -> all offsuit aces from ATo to AKo
        "K9s+, KJo+" -> K9s-KAs and KJo-KAo
        "AKs, AKo" -> just AKs and AKo
    """
    if not range_str or not range_str.strip():
        return set()
    
    hands = set()
    
    # Split by comma
    parts = [p.strip() for p in range_str.split(',')]
    
    for part in parts:
        if not part:
            continue
        
        if part.endswith('+'):
            # Range notation
            base_hand_str = part[:-1]
            expanded = expand_plus_notation(base_hand_str)
            hands.update(expanded)
        elif '-' in part and not part.startswith('-'):
            # Explicit range like "A5s-A9s"
            expanded = expand_dash_notation(part)
            hands.update(expanded)
        else:
            # Single hand
            try:
                hands.add(Hand(part))
            except ValueError as e:
                print(f"Warning: Could not parse hand '{part}': {e}")
    
    return hands


def expand_plus_notation(base_hand_str):
    """
    Expand + notation.
    Examples:
        "22+" -> all pairs from 22 to AA
        "A2s+" -> A2s, A3s, A4s, ..., AKs
        "ATo+" -> ATo, AJo, AQo, AKo
    """
    base_hand = Hand(base_hand_str)
    hands = []
    
    if base_hand.is_pair:
        # All pairs from this pair to AA
        start_idx = Hand.RANK_VALUES[base_hand.rank1]
        for i in range(start_idx, len(Hand.RANKS)):
            rank = Hand.RANKS[i]
            hands.append(Hand(f"{rank}{rank}"))
    else:
        # Non-pair: expand to all hands with same first rank
        rank1 = base_hand.rank1
        rank2_start = base_hand.rank2
        start_idx = Hand.RANK_VALUES[rank2_start]
        rank1_idx = Hand.RANK_VALUES[rank1]
        
        # Go from rank2_start up to (but not including) rank1
        for i in range(start_idx, rank1_idx):
            rank2 = Hand.RANKS[i]
            if base_hand.is_suited:
                hands.append(Hand(f"{rank1}{rank2}s"))
            else:
                hands.append(Hand(f"{rank1}{rank2}o"))
    
    return hands


def expand_dash_notation(range_str):
    """
    Expand dash notation like "A5s-A9s", "JTo-J8o", or "77-22" (pairs).
    """
    parts = range_str.split('-')
    if len(parts) != 2:
        raise ValueError(f"Invalid dash notation: {range_str}")
    
    start_hand = Hand(parts[0].strip())
    end_hand = Hand(parts[1].strip())
    
    hands = []
    
    # Check if both are pairs
    if start_hand.is_pair and end_hand.is_pair:
        # Pair range like "77-22"
        start_idx = Hand.RANK_VALUES[start_hand.rank1]
        end_idx = Hand.RANK_VALUES[end_hand.rank1]
        
        # Make sure start_idx <= end_idx
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        for i in range(start_idx, end_idx + 1):
            rank = Hand.RANKS[i]
            hands.append(Hand(f"{rank}{rank}"))
        
        return hands
    
    # Non-pair range - ensure same rank1 and suited/offsuit
    if start_hand.rank1 != end_hand.rank1:
        raise ValueError(f"Dash notation must have same first rank: {range_str}")
    if start_hand.is_suited != end_hand.is_suited:
        raise ValueError(f"Dash notation must have same suited/offsuit: {range_str}")
    
    rank1 = start_hand.rank1
    start_idx = Hand.RANK_VALUES[start_hand.rank2]
    end_idx = Hand.RANK_VALUES[end_hand.rank2]
    
    # Make sure start_idx <= end_idx
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    
    for i in range(start_idx, end_idx + 1):
        rank2 = Hand.RANKS[i]
        if start_hand.is_suited:
            hands.append(Hand(f"{rank1}{rank2}s"))
        else:
            hands.append(Hand(f"{rank1}{rank2}o"))
    
    return hands


def find_closest_hand_in_range(hand, range_hands):
    """
    Find the closest hand in a range to the given hand.
    Returns the closest Hand object.
    Excludes pairs from the result.
    
    Rules (Strict Priority):
    1. Same high card & suitedness (closest low card)
    2. Closest high card & suitedness (closest low card)
    """
    if not range_hands:
        return None
    
    # Filter out pairs from range_hands (unless hand is pair? user said closest shouldn't be pair)
    # Assuming user plays non-pair hand. If user plays pair, closest should probably be pair
    if hand.is_pair:
        pair_candidates = [h for h in range_hands if h.is_pair]
        if not pair_candidates:
            # Fallback to non-pairs? or just return closest rank matches
            non_pair_hands = [h for h in range_hands if not h.is_pair]
            if not non_pair_hands: return None
            return min(non_pair_hands, key=lambda h: hand.distance_to(h))
        # For pairs, just find closest rank
        return min(pair_candidates, key=lambda h: abs(Hand.RANK_VALUES[h.rank1] - Hand.RANK_VALUES[hand.rank1]))
    
    # Non-pair hand logic
    non_pair_hands = [h for h in range_hands if not h.is_pair]
    if not non_pair_hands:
        return None
        
    candidates_suiting = [h for h in non_pair_hands if h.is_suited == hand.is_suited]
    
    if not candidates_suiting:
        # Fallback to wrong suitedness if strictly necessary
        candidates_suiting = non_pair_hands

    # Sort candidates by distance of high card, then distance of low card
    def strict_priority_sort(h):
        rank1_dist = abs(Hand.RANK_VALUES[h.rank1] - Hand.RANK_VALUES[hand.rank1])
        rank2_dist = abs(Hand.RANK_VALUES[h.rank2] - Hand.RANK_VALUES[hand.rank2])
        return (rank1_dist, rank2_dist)

    closest = min(candidates_suiting, key=strict_priority_sort)
    return closest


def find_bottom_of_range_category(hand, range_hands):
    """
    Find the "bottom" of the current hand's category in the range.
    The bottom is the hand with the lowest Rank2 that is still in the range,
    matching Rank1 and Suitedness.
    
    Example: Hand A9s, Range A5s+. Bottom is A5s.
    """
    if not range_hands:
        return None
        
    # Filter for exact category match: Same High Card, Same Suitedness/Pair status
    if hand.is_pair:
         # For pairs, category is just pairs? or specific pair?
         # Pairs usually grouped together "22+". Bottom is the lowest pair.
         candidates = [h for h in range_hands if h.is_pair]
    else:
        candidates = [
            h for h in range_hands 
            if not h.is_pair 
            and h.rank1 == hand.rank1 
            and h.is_suited == hand.is_suited
        ]
        
    if not candidates:
        return None
        
    # The "bottom" is the one with the lowest Rank2 (or Rank1 for pairs)
    if hand.is_pair:
        bottom = min(candidates, key=lambda h: Hand.RANK_VALUES[h.rank1])
    else:
        bottom = min(candidates, key=lambda h: Hand.RANK_VALUES[h.rank2])
        
    return bottom


if __name__ == "__main__":
    # Test the range parser
    test_range = "22+, A2s+, ATo+, K9s+, KJo+, Q9s+, QJo, J9s+, JTo, T8s+, T9o, 98s, 87s, 76s, 65s, 54s"
    hands = parse_range_notation(test_range)
    print(f"Parsed {len(hands)} hands from range:")
    print(sorted([str(h) for h in hands]))
    
    # Test closest hand
    test_hand = Hand("T5o")
    closest = find_closest_hand_in_range(test_hand, hands)
    print(f"\nClosest hand to {test_hand} in range: {closest}")
