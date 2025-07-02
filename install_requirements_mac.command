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

# Function to get the appropriate Python command
get_python_cmd() {
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
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

            # Install requirements
            pip install -r requirements.txt

        else
            echo "✗ Failed to activate conda environment 'scraper'"
            echo "If you use Python via Conda then you must specify which env to use in the .env file..."
        fi
    else
        echo "⚠ Conda environment 'scraper' not found"
            echo "If you use Python via Conda then you must specify which env to use in the .env file..."
    fi
else
    echo "⚠ Conda not detected"
    echo "Using system Python..."

    # Get the appropriate Python command
    PYTHON_CMD=$(get_python_cmd)
    if [ -n "$PYTHON_CMD" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt
    else
        echo "✗ No Python command found (neither 'python' nor 'python3')"
        exit 1
    fi
fi

echo "Installation complete."
echo ""
echo ".--------------------------------------------."
echo "| ▄▖    ▗   ▜ ▜   ▗ ▘      ▄▖       ▜   ▗    |"
echo "| ▐ ▛▌▛▘▜▘▀▌▐ ▐ ▀▌▜▘▌▛▌▛▌  ▌ ▛▌▛▛▌▛▌▐ █▌▜▘█▌ |"
echo "| ▟▖▌▌▄▌▐▖█▌▐▖▐▖█▌▐▖▌▙▌▌▌  ▙▖▙▌▌▌▌▙▌▐▖▙▖▐▖▙▖ |"
echo "|                                 ▌          |"
echo "'--------------------------------------------'"
