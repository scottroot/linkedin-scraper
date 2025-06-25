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
    from app.logger import get_logger

    logger = get_logger()
    logger.info("Starting LinkedIn Contact Validator GUI...")
    logger.info("Make sure you have activated the 'scraper' conda environment!")
    main()
except ImportError as e:
    logger = get_logger()
    logger.error(f"Error importing GUI modules: {e}")
    logger.error("\nTroubleshooting:")
    logger.error("1. Make sure you have activated the 'scraper' conda environment:")
    logger.error("   conda activate scraper")
    logger.error("2. Install required packages:")
    logger.error("   pip install -r requirements.txt")
    logger.error("3. Make sure PySide6 is available in your environment")
    logger.error("4. If you encounter NumPy compatibility issues, try:")
    logger.error("   pip install 'numpy<2.0.0'")
    sys.exit(1)
except Exception as e:
    logger = get_logger()
    logger.error(f"Error starting GUI: {e}")
    sys.exit(1)