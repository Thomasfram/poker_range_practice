"""
Flask backend for poker range practice web app.
"""
import os
from flask import Flask, jsonify, request, send_from_directory, session
import random
from .poker_hands import generate_all_hands, find_closest_hand_in_range, find_bottom_of_range_category, Hand
from .range_manager import RangeManager

def create_app():
    app = Flask(__name__, static_url_path='', static_folder='static')
    # Use a consistent secret key so all workers share the same Session Interface
    app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_poker_practice_local')

    # Global state
    # Use absolute path for ranges.json relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ranges_path = os.path.join(base_dir, "ranges.json")
    
    range_manager = RangeManager(ranges_path)
    all_hands = generate_all_hands()
    
    def get_current_range():
        """Helper to get current range based on session."""
        if 'config' not in session:
            return None
        
        cfg = session['config']
        return range_manager.get_range(cfg['position'], cfg['action'], cfg['stack_depth'])

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/api/positions', methods=['GET'])
    def get_positions():
        """Get all available positions."""
        positions = range_manager.get_available_positions()
        return jsonify(positions)

    @app.route('/api/actions/<position>', methods=['GET'])
    def get_actions(position):
        """Get available actions for a position."""
        actions = range_manager.get_available_actions(position)
        return jsonify(actions)

    @app.route('/api/stack-depths/<position>/<action>', methods=['GET'])
    def get_stack_depths(position, action):
        """Get available stack depths for a position/action."""
        stack_depths = range_manager.get_available_stack_depths(position, action)
        return jsonify(stack_depths)

    @app.route('/api/start', methods=['POST'])
    def start_practice():
        """Start practice session with given configuration."""
        data = request.json
        position = data.get('position')
        action = data.get('action')
        stack_depth = data.get('stack_depth')
        
        # Validate existence
        current_range = range_manager.get_range(position, action, stack_depth)
        
        if current_range is None:
            return jsonify({'error': 'Range not found'}), 404
        
        # Get available actions for this specific range
        range_actions = range_manager.get_available_range_actions(position, action, stack_depth)
        
        # Store in session
        session['config'] = {
            'position': position,
            'action': action,
            'stack_depth': stack_depth
        }
        
        return jsonify({
            'success': True,
            'range_size': len(current_range),
            'available_actions': range_actions
        })

    @app.route('/api/next-hand', methods=['GET'])
    def get_next_hand():
        """Get a random hand for practice."""
        current_range = get_current_range()
        if current_range is None:
            return jsonify({'error': 'No active practice session'}), 400
        
        hand = random.choice(all_hands)
        return jsonify({'hand': str(hand)})

    @app.route('/api/check-answer', methods=['POST'])
    def check_answer():
        """Check if the user's answer is correct."""
        current_range = get_current_range()
        
        if current_range is None:
            return jsonify({'error': 'No active practice session'}), 400
        
        data = request.json
        hand_str = data.get('hand')
        if not hand_str:
            return jsonify({'error': 'No hand provided'}), 400

        # User's selected action (e.g. "3bet", "call", "fold", "in_range")
        user_action = data.get('action')
        
        hand = Hand(hand_str)
        
        # Determine actual action for this hand
        # current_range is now a dict: {Hand: ActionString}
        actual_action = current_range.get(hand, "fold")
        
        is_correct = (user_action == actual_action)
        
        response = {
            'correct': is_correct,
            'actual_action': actual_action,
            'user_action': user_action
        }
        
        # If incorrect
        if not is_correct:
            # If actual valid action is NOT "fold", find closest hand with THAT action?
            # Or just find closest hand in general "in range" (non-fold)?
            
            # Logic: If hand should be folded, but user picked action -> Show closest valid hand for that action?
            # Or if hand should be action X, but user picked action Y...
            
            # Simplified "closest" logic for now:
            # If actual is "fold", find closest non-fold hand
            if actual_action == "fold":
                # Find closest hand that is present in the range (any action)
                # Create set of hands from dict keys
                range_hands = set(current_range.keys())
                closest = find_closest_hand_in_range(hand, range_hands)
                if closest:
                    response['closest_hand'] = str(closest)
                    closest_action = current_range.get(closest)
                    # response['closest_type'] = closest_action # Optional info
            else:
                 # Actual is some active action.
                 # If user picked "fold", show bottom of that specific action range?
                pass

        # If correct and NOT fold, show bottom of range for that action
        if is_correct and actual_action != "fold":
             # Filter range to only hands with this action
             specific_range_hands = [h for h, act in current_range.items() if act == actual_action]
             bottom = find_bottom_of_range_category(hand, specific_range_hands)
             if bottom:
                response['bottom_of_range'] = str(bottom)
        
        return jsonify(response)
    
    return app

def main():
    print("Starting Poker Range Practice App...")
    print("Open your browser to: http://localhost:5000")
    app = create_app()
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()
