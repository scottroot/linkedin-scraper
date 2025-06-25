# LinkedIn Employment Checker

This tool checks if people from your contacts list are currently employed at specific companies by looking at their LinkedIn profiles.

## Quick Start

### 1. Prepare your contacts.csv file
Place your `contacts.csv` file in the root directory with these exact column names:
- `First Name`
- `Last Name`
- `Account Name` (this is the company name)
- `Valid` (will be filled automatically)

### 2. Run the application
**Windows users:** Double-click `run_app_windows.bat`

**Mac users:** Double-click `run_app_mac.command`

![Application Screenshot](img/instructions.png)

### 3. Important Notes
⚠️ **Risk Warning:** The application may crash due to:
- Rate limiting by LinkedIn
- Blocking by search engines (Google/Bing)
- Network connectivity issues
- Browser automation detection

If the app crashes, you can restart it and it will continue from where it left off.

## What it does
- Reads your contacts from the CSV file
- Checks each person's LinkedIn profile to see if they work at the listed company
- Updates the CSV with True/False results
- Processes contacts in small batches to minimize blocking