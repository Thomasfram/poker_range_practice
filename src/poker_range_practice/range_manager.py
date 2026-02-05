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
        Returns a set of Hand objects, or None if not found.
        """
        try:
            range_str = self.ranges[position][action][stack_depth]
            return parse_range_notation(range_str)
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


if __name__ == "__main__":
    # Test range manager
    rm = RangeManager("ranges.json")
    print(f"Available positions: {rm.get_available_positions()}")
    
    if rm.get_available_positions():
        pos = rm.get_available_positions()[0]
        print(f"Actions for {pos}: {rm.get_available_actions(pos)}")
