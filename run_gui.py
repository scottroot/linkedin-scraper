#!/usr/bin/env python3
"""
LinkedIn Contact Validator GUI Launcher
Run this script to start the GUI application.

Note: Make sure to activate the 'scraper' conda environment first:
    conda activate scraper
    python run_gui.py
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_main import main
    print("Starting LinkedIn Contact Validator GUI...")
    print("Make sure you have activated the 'scraper' conda environment!")
    main()
except ImportError as e:
    print(f"Error importing GUI modules: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you have activated the 'scraper' conda environment:")
    print("   conda activate scraper")
    print("2. Install required packages:")
    print("   pip install -r requirements.txt")
    print("3. Make sure PySide6 is available in your environment")
    print("4. If you encounter NumPy compatibility issues, try:")
    print("   pip install 'numpy<2.0.0'")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)