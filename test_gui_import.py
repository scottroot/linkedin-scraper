#!/usr/bin/env python3
"""
Test script to verify GUI imports work correctly
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all the necessary imports"""
    print("Testing imports...")

    try:
        # Test NumPy
        import numpy
        print(f"✓ NumPy {numpy.__version__}")

        # Test PySide6
        import PySide6
        print(f"✓ PySide6 {PySide6.__version__}")

        # Test PySide6 specific imports
        from PySide6.QtWidgets import QApplication, QMainWindow
        from PySide6.QtCore import Signal, Qt
        from PySide6.QtGui import QFont
        print("✓ PySide6 widgets imported")

        # Test pandas
        import pandas
        print(f"✓ Pandas {pandas.__version__}")

        # Test main module
        from main import process_contacts_batch
        print("✓ Main processing module imported")

        # Test GUI module
        from gui_main import LinkedInScraperGUI, MessageProcessor
        print("✓ GUI modules imported")

        print("\n🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_gui_creation():
    """Test if GUI can be created (without showing it)"""
    try:
        from PySide6.QtWidgets import QApplication
        from gui_main import LinkedInScraperGUI

        # Create QApplication instance
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        # Create GUI instance
        gui = LinkedInScraperGUI()
        print("✓ GUI instance created successfully")

        # Clean up
        gui.close()
        return True

    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

if __name__ == "__main__":
    print("LinkedIn Scraper - GUI Import Test")
    print("=" * 40)

    if test_imports():
        print("\nTesting GUI creation...")
        if test_gui_creation():
            print("\n✅ All tests passed! The GUI should work correctly.")
            print("\nYou can now run:")
            print("  python run_gui.py")
        else:
            print("\n❌ GUI creation test failed.")
    else:
        print("\n❌ Import test failed.")
        print("\nPlease run the dependency installation helper:")
        print("  python install_dependencies.py")