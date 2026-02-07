
import os
import sys
import unittest
from pathlib import Path

# Add project root to path
project_root = Path("c:/Users/Thomas/Desktop/Range_test/src")
sys.path.append(str(project_root))

from poker_range_practice.range_manager import RangeManager
from poker_range_practice.poker_hands import Hand

class TestMultiActionRanges(unittest.TestCase):
    def setUp(self):
        self.ranges_path = project_root / "poker_range_practice/ranges.json"
        self.rm = RangeManager(self.ranges_path)
    
    def test_load_complex_range(self):
        # BB vs BTN 50bb should be a dict
        range_data = self.rm.ranges["BB"]["3bet vs BTN"]["50bb"]
        self.assertIsInstance(range_data, dict)
        self.assertIn("3bet", range_data)
        self.assertIn("call", range_data)
        
    def test_get_range_returns_dict(self):
        # Test BB vs BTN 50bb
        range_map = self.rm.get_range("BB", "3bet vs BTN", "50bb")
        self.assertIsInstance(range_map, dict)
        
        # AA should be 3bet
        aa = Hand("AA")
        self.assertIn(aa, range_map)
        self.assertEqual(range_map[aa], "3bet")
        
        # 72o should not be in range (implicit fold)
        seven_two = Hand("72o")
        self.assertNotIn(seven_two, range_map)
        
        # Check a call hand (e.g. 87s from ranges.json: "call": "... 87s ...")
        # "call": "A2s-ATs ... 87o, 76o, 65o, 54o"
        # Let's check a specific one
        hand_call = Hand("87s") # This is in call range according to json
        # JSON says: "call": "... 82s-86s..." wait, 87s is in 3bet_l: "3bet_l": "87s, 98s, ..."
        
        # Verify 87s is 3bet_l
        h87s = Hand("87s")
        self.assertEqual(range_map.get(h87s), "3bet_l")
        
        # Verify a call hand: JTs is in call
        hjts = Hand("JTs")
        self.assertEqual(range_map.get(hjts), "call")

    def test_get_range_simple(self):
        # Test BTN open 50bb (should be simple string -> dict with "in_range")
        range_map = self.rm.get_range("BTN", "open", "50bb")
        self.assertIsInstance(range_map, dict)
        
        aa = Hand("AA")
        self.assertEqual(range_map[aa], "in_range")

    def test_get_available_range_actions(self):
        # Complex
        actions = self.rm.get_available_range_actions("BB", "3bet vs BTN", "50bb")
        self.assertIn("3bet", actions)
        self.assertIn("call", actions)
        
        # Simple
        actions_simple = self.rm.get_available_range_actions("BTN", "open", "50bb")
        self.assertEqual(actions_simple, ["in_range"])

if __name__ == "__main__":
    unittest.main()
