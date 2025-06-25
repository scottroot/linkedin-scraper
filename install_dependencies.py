#!/usr/bin/env python3
"""
Dependency Installation Helper
This script helps install the correct versions of dependencies to avoid compatibility issues.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"  Error: {e.stderr}")
        return False

def main():
    print("LinkedIn Scraper - Dependency Installation Helper")
    print("=" * 50)

    # Check if we're in a conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV')
    if conda_env:
        print(f"✓ Detected conda environment: {conda_env}")
    else:
        print("⚠ No conda environment detected. Consider using:")
        print("  conda create -n scraper python=3.11")
        print("  conda activate scraper")

    # Step 1: Downgrade NumPy to avoid compatibility issues
    print("\nStep 1: Installing compatible NumPy version...")
    success = run_command(
        "pip install 'numpy<2.0.0'",
        "Installing NumPy < 2.0.0"
    )

    if not success:
        print("\nTrying alternative approach...")
        run_command(
            "pip uninstall numpy -y && pip install 'numpy<2.0.0'",
            "Reinstalling NumPy"
        )

    # Step 2: Install PySide6
    print("\nStep 2: Installing PySide6...")
    run_command(
        "pip install 'PySide6>=6.5.0'",
        "Installing PySide6"
    )

    # Step 3: Install other dependencies
    print("\nStep 3: Installing other dependencies...")
    run_command(
        "pip install -r requirements.txt",
        "Installing all requirements"
    )

    # Step 4: Test imports
    print("\nStep 4: Testing imports...")
    try:
        import numpy
        print(f"✓ NumPy version: {numpy.__version__}")

        import PySide6
        print(f"✓ PySide6 version: {PySide6.__version__}")

        from PySide6.QtCore import Signal
        print("✓ PySide6 Signal import successful")

        import pandas
        print(f"✓ Pandas version: {pandas.__version__}")

        print("\n🎉 All dependencies installed successfully!")
        print("\nYou can now run the GUI with:")
        print("  python run_gui.py")

    except ImportError as e:
        print(f"✗ Import test failed: {e}")
        print("\nPlease try running the installation commands manually:")
        print("  pip install 'numpy<2.0.0'")
        print("  pip install 'PySide6>=6.5.0'")
        print("  pip install -r requirements.txt")

if __name__ == "__main__":
    main()