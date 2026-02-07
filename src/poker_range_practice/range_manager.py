"""
Range management - load and query poker ranges from JSON configuration.
"""
import json
from pathlib import Path
from .poker_hands import parse_range_notation


class RangeManager:
    """Manages loading and querying poker ranges."""
    
    def __init__(self, ranges_file="ranges.json"):
        """Initialize with path to ranges JSON file."""
        self.ranges_file = Path(ranges_file)
        self.ranges = {}
        self.load_ranges()
    
    def load_ranges(self):
        """Load ranges from JSON file."""
        if not self.ranges_file.exists():
            print(f"Warning: {self.ranges_file} not found. Creating empty ranges.")
            self.ranges = {}
            return
        
        try:
            with open(self.ranges_file, 'r') as f:
                self.ranges = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error loading ranges file: {e}")
            self.ranges = {}
    
    def get_range(self, position, action, stack_depth="standard"):
        """
        Get a range for given position, action, and stack depth.
        Returns a dictionary mapping Hand objects to action strings (e.g. "call", "3bet").
        For simple ranges, returns {"in_range": "range"} (or similar default).
        Returns None if not found.
        """
        try:
            range_data = self.ranges[position][action][stack_depth]
            
            # Case 1: Simple string range (Binary: In Range vs Fold)
            if isinstance(range_data, str):
                hands = parse_range_notation(range_data)
                # Map all hands to a default "in_range" action
                return {hand: "in_range" for hand in hands}
            
            # Case 2: Complex dict range (Multi-action: 3bet, call, etc)
            elif isinstance(range_data, dict):
                full_range = {}
                for sub_action, sub_range_str in range_data.items():
                    hands = parse_range_notation(sub_range_str)
                    for hand in hands:
                        # If a hand is in multiple sub-ranges (which shouldn't happen ideally),
                        # the last one overwrites. Future: handle mixed strategies.
                        full_range[hand] = sub_action
                return full_range
                
            else:
                print(f"Unknown range data type: {type(range_data)}")
                return None

        except KeyError:
            return None
    
    def get_available_positions(self):
        """Get list of available positions."""
        return list(self.ranges.keys())
    
    def get_available_actions(self, position):
        """Get list of available actions for a position."""
        if position not in self.ranges:
            return []
        return list(self.ranges[position].keys())
    
    def get_available_stack_depths(self, position, action):
        """Get list of available stack depths for a position/action."""
        if position not in self.ranges or action not in self.ranges[position]:
            return []
        return list(self.ranges[position][action].keys())

    def get_available_range_actions(self, position, action, stack_depth):
        """
        Get the specific actions available in a range (e.g. ['3bet', 'call', 'fold']).
        Returns a list of action strings.
        Always includes 'fold' (implicitly).
        """
        try:
            range_data = self.ranges[position][action][stack_depth]
            
            if isinstance(range_data, str):
                return ["in_range"]
            elif isinstance(range_data, dict):
                return list(range_data.keys())
            return []
        except KeyError:
            return []


if __name__ == "__main__":
    # Test range manager
    rm = RangeManager("ranges.json")
    print(f"Available positions: {rm.get_available_positions()}")
    
    if rm.get_available_positions():
        pos = rm.get_available_positions()[0]
        print(f"Actions for {pos}: {rm.get_available_actions(pos)}")
