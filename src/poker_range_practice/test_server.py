
import os
import sys

# Add project root to path
project_root = os.path.abspath("src")
sys.path.append(project_root)

from poker_range_practice import create_app

if __name__ == "__main__":
    app = create_app()
    print("Starting verification server on port 5001...")
    app.run(debug=True, port=5001, use_reloader=False)
