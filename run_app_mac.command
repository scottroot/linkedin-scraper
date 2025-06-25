#!/bin/bash
# LinkedIn Contact Validator GUI Launcher for Mac
# This script automatically detects conda availability and launches the GUI appropriately

echo "LinkedIn Contact Validator GUI Launcher for Mac"
echo "=============================================="

# Get the directory where this script is located and change to it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Script directory: $SCRIPT_DIR"
cd "$SCRIPT_DIR"

# Function to check if conda is available
check_conda() {
    if command -v conda &> /dev/null; then
        return 0  # conda is available
    else
        return 1  # conda is not available
    fi
}

# Function to check if the scraper environment exists
check_scraper_env() {
    conda env list | grep -q "scraper"
    return $?
}

# Check if conda is available
if check_conda; then
    echo "✓ Conda detected"

    # Check if scraper environment exists
    if check_scraper_env; then
        echo "✓ Conda environment 'scraper' found"
        echo "Activating conda environment 'scraper'..."

        # Activate the scraper environment
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate scraper

        if [ $? -eq 0 ]; then
            echo "✓ Environment activated successfully!"
            echo "Starting GUI with conda environment..."
            echo "Current directory: $(pwd)"
            echo "Looking for: $(pwd)/gui_main.py"
            python gui_main.py
        else
            echo "✗ Failed to activate conda environment 'scraper'"
            echo "Falling back to system Python..."
            python gui_main.py
        fi
    else
        echo "⚠ Conda environment 'scraper' not found"
        echo "Using system Python instead..."
        python gui_main.py
    fi
else
    echo "⚠ Conda not detected"
    echo "Using system Python..."
    python gui_main.py
fi

echo "GUI closed."