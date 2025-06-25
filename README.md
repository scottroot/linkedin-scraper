# LinkedIn Employment Checker

This tool checks if people from your contacts list are currently employed at specific companies by looking at their LinkedIn profiles.

## What it does:
- Reads a list of contacts from a CSV file
- Checks each person's LinkedIn profile to see if they work at the company listed
- Updates the CSV with True/False results
- Processes contacts in small batches to avoid being blocked

## Setup:
### Run these commands in Terminal (Mac) or Command Prompt (Windows)

1. **Install Python requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Make sure you have Chrome browser installed**

3. **Prepare your contacts.csv file** in the root directory with these exact column names:
   - `First Name`
   - `Last Name`
   - `Account Name` (this is the company name)
   - `Valid` (will be filled automatically)

## How to run:

1. **Run the script:**
   ```bash
   python main.py
   ```

2. **Optional: Start from a specific row:**
   ```bash
   python main.py --start-row 10
   ```
   This will skip the first 10 rows and start processing from row 11.

3. **Optional: Limit the number of rows to process:**
   ```bash
   python main.py --limit 50
   ```
   This will only consider the first 50 rows (including already processed ones).

4. **Optional: Combine start row and limit:**
   ```bash
   python main.py --start-row 10 --limit 100
   ```
   This will process rows 10-109 (100 rows total, starting from row 10).

5. **Optional: Customize batch settings:**
   ```bash
   python main.py --start-row 5 --limit 20 --batch-size 3 --delay 60
   ```
   - `--start-row`: Row number to start from (0-indexed)
   - `--limit`: Maximum number of rows to consider (including already processed ones)
   - `--batch-size`: Number of contacts to process before saving
   - `--delay`: Seconds to wait between batches

6. **When the browser opens:**
   - Log into your LinkedIn account manually
   - Complete any CAPTCHA if needed
   - Press Enter in the terminal when you're logged in

7. **Let it run:**
   - The tool will process your contacts automatically
   - It saves progress after each batch, so you can stop and restart if needed
   - Results will be saved in the same contacts.csv file

## Notes:
- The tool is respectful and includes delays to avoid being blocked
- If you stop the script, you can restart it and it will skip already processed contacts
- Use `--start-row` to resume from where you left off if the script was interrupted
- Use `--limit` to process only a subset of your contacts (useful for testing or processing large files in chunks)
- The `--limit` parameter counts total rows considered, not just unprocessed rows
- Make sure your contacts.csv file is in the same folder as main.py