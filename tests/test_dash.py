"""Test dash notation parsing."""
from poker_hands import parse_range_notation

# Test the SB limp range with dash notation
test_range = "77-22, K6s-K2s, Q7s-Q2s, J8s-J2s, T7s-T2s, 97s-92s, 86s-82s, 75s-72s, 64s-62s, 53s-52s, 43s-42s, 32s, A8o-A2o, K9o-K2o, Q9o-Q3o, J9o-J4o, T8o-T6o, 97o-96o, 87o-86o, 76o"

print("Testing dash notation parsing...")
print(f"Input: {test_range[:80]}...")
print()

try:
    hands = parse_range_notation(test_range)
    print(f"✓ Successfully parsed {len(hands)} hands")
    print()
    
    # Show some examples
    print("Sample hands from range:")
    sample = sorted([str(h) for h in hands])[:20]
    for hand in sample:
        print(f"  {hand}")
    print(f"  ... and {len(hands) - 20} more")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
