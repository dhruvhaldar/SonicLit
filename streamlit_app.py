import sys
import os
import runpy

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Run the main Streamlit application
script_path = os.path.join(os.path.dirname(__file__), 'src', 'soniclit', 'gui', 'web', 'app.py')
runpy.run_path(script_path, run_name='__main__')
