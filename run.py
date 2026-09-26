import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
