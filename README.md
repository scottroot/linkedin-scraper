# LinkedIn Employment Checker

This tool checks if people from your contacts list are currently employed at specific companies by looking at their LinkedIn profiles.

## What it does:
- Reads a list of contacts from a CSV file
- Checks each person's LinkedIn profile to see if they work at the company listed
- Updates the CSV with True/False results
- Processes contacts in small batches to avoid being blocked

## Setup:
### Run these commands in Terminal (Mac) or Command Prompt (Windows)

1. **Activate the conda environment:**
   ```bash
   conda activate scraper
   ```

2. **Install Python requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Make sure you have Chrome browser installed**

4. **Prepare your contacts.csv file** with these exact column names:
   - `First Name`
   - `Last Name`
   - `Account Name` (this is the company name)
   - `Valid` (will be filled automatically)

## How to run:

### Option 1: GUI Interface (Recommended)

#### Method A: Using the launcher script (easiest)
```bash
./run_app_mac.sh
```

#### Method B: Manual activation
1. **Activate conda environment and start the GUI:**
   ```bash
   conda activate scraper
   python run_gui.py
   ```
   or
   ```bash
   conda activate scraper
   python gui_main.py
   ```

2. **Using the GUI:**
   - Select your input CSV file using the "Browse" button
   - Choose an output folder for the results
   - Click "Load & Validate CSV" to check your file structure
   - Review the file information and any warnings/issues
   - Click "Advanced Options" if you need to customize settings
   - Click "Start Processing" to begin validation
   - Monitor progress in the real-time log window

### Option 2: Command Line Interface

1. **Activate conda environment and run the script:**
   ```bash
   conda activate scraper
   python main.py
   ```

2. **Optional: Start from a specific row:**
   ```bash
   conda activate scraper
   python main.py --start-row 10
   ```
   This will skip the first 10 rows and start processing from row 11.

3. **Optional: Limit the number of rows to process:**
   ```bash
   conda activate scraper
   python main.py --limit 50
   ```
   This will only consider the first 50 rows (including already processed ones).

4. **Optional: Combine start row and limit:**
   ```bash
   conda activate scraper
   python main.py --start-row 10 --limit 100
   ```
   This will process rows 10-109 (100 rows total, starting from row 10).

5. **Optional: Customize batch settings:**
   ```bash
   conda activate scraper
   python main.py --start-row 5 --limit 20 --batch-size 3 --delay 60
   ```
   - `--start-row`: Row number to start from (0-indexed)
   - `--limit`: Maximum number of rows to consider (including already processed ones)
   - `--batch-size`: Number of contacts to process before saving
   - `--delay`: Seconds to wait between batches

## GUI Features:
- **File Selection**: Easy browsing for input CSV and output folder
- **CSV Validation**: Automatic checking of file structure and data quality
- **Real-time Progress**: Live updates during processing
- **Advanced Options**: Configurable batch size, delays, and row limits
- **Error Handling**: Clear error messages and warnings
- **Progress Saving**: Automatic saving after each batch

## Notes:
- **Important**: Always activate the 'scraper' conda environment before running the tool
- The tool is respectful and includes delays to avoid being blocked
- If you stop the script, you can restart it and it will skip already processed contacts
- Use `--start-row` to resume from where you left off if the script was interrupted
- Use `--limit` to process only a subset of your contacts (useful for testing or processing large files in chunks)
- The `--limit` parameter counts total rows considered, not just unprocessed rows
- The GUI saves results as `contacts_validated.csv` in your selected output folder
- The command-line version saves results in the same `contacts.csv` file