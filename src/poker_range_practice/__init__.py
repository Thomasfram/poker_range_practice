"""
Flask backend for poker range practice web app.
"""
import os
from flask import Flask, jsonify, request, send_from_directory
import random
from .poker_hands import generate_all_hands, find_closest_hand_in_range, find_bottom_of_range_category, Hand
from .range_manager import RangeManager

def create_app():
    app = Flask(__name__, static_url_path='', static_folder='static')

    # Global state
    # Use absolute path for ranges.json relative to this file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ranges_path = os.path.join(base_dir, "ranges.json")
    
    range_manager = RangeManager(ranges_path)
    all_hands = generate_all_hands()
    
    # Store current range in app config or a global dictionary to avoid global variable issues
    # For simplicity in this single-user local app, we'll keep a simple approach but make it accessible
    state = {'current_range': None}

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
        
        state['current_range'] = range_manager.get_range(position, action, stack_depth)
        
        if state['current_range'] is None:
            return jsonify({'error': 'Range not found'}), 404
        
        return jsonify({
            'success': True,
            'range_size': len(state['current_range'])
        })

    @app.route('/api/next-hand', methods=['GET'])
    def get_next_hand():
        """Get a random hand for practice."""
        if state['current_range'] is None:
            return jsonify({'error': 'No active practice session'}), 400
        
        hand = random.choice(all_hands)
        return jsonify({'hand': str(hand)})

    @app.route('/api/check-answer', methods=['POST'])
    def check_answer():
        """Check if the user's answer is correct."""
        current_range = state['current_range']
        
        if current_range is None:
            return jsonify({'error': 'No active practice session'}), 400
        
        data = request.json
        hand_str = data.get('hand')
        user_says_in_range = data.get('in_range', "not answered yet")
        
        hand = Hand(hand_str)
        actually_in_range = hand in current_range
        
        is_correct = user_says_in_range == actually_in_range
        
        response = {
            'correct': is_correct,
            'actually_in_range': actually_in_range
        }
        
        # If incorrect and hand is not in range, find closest hand
        if not is_correct and not actually_in_range:
            closest = find_closest_hand_in_range(hand, current_range)
            if closest:
                response['closest_hand'] = str(closest)
                response['closest_type'] = 'in_range'
                
        # If correct, show bottom of range
        elif is_correct:
            if actually_in_range:
                # Correctly identified IN range -> show lowest hand IN range
                bottom = find_bottom_of_range_category(hand, current_range)
                if bottom:
                    response['bottom_of_range'] = str(bottom)
            else:
                # Correctly identified OUT of range (fold) -> show lowest hand IN range (the boundary)
                closest = find_closest_hand_in_range(hand, current_range)
                if closest:
                    response['bottom_of_range'] = str(closest)
        
        return jsonify(response)
    
    return app

def main():
    print("Starting Poker Range Practice App...")
    print("Open your browser to: http://localhost:5000")
    app = create_app()
    app.run(debug=True, port=5000)

if __name__ == '__main__':
    main()
