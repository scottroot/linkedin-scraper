# This module takes company names found on LinkedIn and compares them to a target company name
import os
import re
import time
import gc
from typing import Literal
from app.parse_profile import get_positions_and_company_match
from app.parse_profile.extract_experience import get_current_employer
from fuzzywuzzy import fuzz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.driver_and_login import get_driver, login, cleanup_driver
from app.find_profile_urls import get_linkedin_url_candidates
import pandas as pd
from app.logger import get_logger


def health_check(driver, driver_name: Literal["LinkedIn", "Bing"], search_count, log, login_confirmation_callback=None):
    try:
        # Test if browsers are still responsive
        driver.current_url  # This will throw an exception if browser is dead
        log(f"Search #{search_count}: {driver_name} browser health check - OK")
    except Exception as e:
        log(f"Search #{search_count}: WARNING - Browser health check failed: {str(e)}")
        try:
            cleanup_driver(driver)
        except:
            pass
        driver = get_driver(headless=True)
        if driver_name == "LinkedIn":
            login(driver, login_confirmation_callback)
        log(f"{driver_name} browser restarted successfully")

    return driver


def process_one_contact(
    full_name,
    company_name,
    linkedin_driver,
    bing_driver,
    idx,
    contacts_df,
    search_count,
    log,
    login_confirmation_callback=None
):
    """
    Process one contact, checking employment status and updating the CSV
    """
    try:
        # Check browser health before each search
        try:
            if bing_driver:
                bing_driver.current_url  # Test if browser is responsive
            if linkedin_driver:
                linkedin_driver.current_url  # Test if browser is responsive
        except Exception as browser_error:
            print(f"Browser health check failed: {browser_error}")
            log("Attempting to restart browsers...")
            # Restart browsers if they're unresponsive
            if bing_driver:
                cleanup_driver(bing_driver)
            if linkedin_driver:
                cleanup_driver(linkedin_driver)

            # Reinitialize browsers
            bing_driver = get_driver(headless=True)
            if os.path.exists("linkedin_cookies.json"):
                linkedin_driver = get_driver(headless=True)
            else:
                linkedin_driver = get_driver(headless=False)
            login(linkedin_driver, login_confirmation_callback)
            log("Browsers restarted successfully")

        # Get LinkedIn URL candidates
        url_candidates = get_linkedin_url_candidates(
            name=full_name,
            company=company_name,
            driver=bing_driver,
            limit=1,
            threshold=0.6
        )

        # Check if we got any results
        if not url_candidates:
            log(f"Search #{search_count} (Row {idx+1}): No LinkedIn profiles found for {full_name} at {company_name}")
            if search_count > 45:  # Log when we're approaching the 50 limit
                log(f"Search #{search_count} (Row {idx+1}): This might be due to rate limiting (approaching 50 search limit)")
            contacts_df.at[idx, 'Note'] = 'Profile not found'
            return

        profile_url = url_candidates[0]

        # Check employment status using the shared driver
        positions_and_company_match = get_positions_and_company_match(
            driver=linkedin_driver,
            profile_url=profile_url,
            target_company=company_name,
            threshold=75,
            verbose=False
        )

        is_employed = positions_and_company_match['company_match']['has_match']

        # Update the Valid column
        contacts_df.at[idx, 'Valid'] = is_employed and len(positions_and_company_match['current_positions']) > 0

        log(f"Result: {is_employed}")

        # TODO: decide if we need this stupid delay...
        # # Small delay between individual checks
        # log("Waiting 2 seconds between individual contact checks to avoid rate limiting...")
        # time.sleep(2)

    except IndexError as e:
        log(f"Search #{search_count} (Row {idx+1}): Error: No LinkedIn profiles found for {full_name} at {company_name} (likely rate limited)")
        contacts_df.at[idx, 'Note'] = 'Profile not found - Maybe rate limited?'
        # Force garbage collection after error
        gc.collect()
    except Exception as e:
        log(f"Search #{search_count} (Row {idx+1}): Error processing {full_name}: {str(e)}")
        log(f"Search #{search_count} (Row {idx+1}): Error type: {type(e).__name__}")
        # Mark as False if there's an error
        contacts_df.at[idx, 'Note'] = str(e)
        # Force garbage collection after error
        gc.collect()

        # Check if we're around the 50 mark and log it
        if 45 <= search_count <= 55:
            log(f"Search #{search_count} (Row {idx+1}): WARNING - Error occurred around the 50-contact mark. This might indicate rate limiting or resource issues.")


def process_contacts_batch(contacts_df, batch_size=1, delay_between_batches=10, log_callback=None, save_callback=None, stop_flag=None, login_confirmation_callback=None):
    """
    Process contacts in batches, checking employment status and updating the CSV

    Args:
        contacts_df: DataFrame with contact information
        batch_size: Number of contacts to process before saving
        delay_between_batches: Seconds to wait between batches to avoid rate limiting
        log_callback: Optional callback function for logging messages
        save_callback: Optional callback function for saving progress
        stop_flag: Optional threading.Event or similar to check for stop signal
        login_confirmation_callback: Optional callback function for login confirmation (GUI button)
    """
    logger = get_logger()

    def log(message):
        if log_callback:
            log_callback(message)
        else:
            logger.info(message)

    # Add Note column if it doesn't exist
    if 'Note' not in contacts_df.columns:
        contacts_df['Note'] = ''

    total_rows = len(contacts_df)
    log(f"Processing {total_rows} contacts in batches of {batch_size}")

    # Track search statistics
    search_count = 0

    # Initialize a single browser session for all processing
    log("Initializing browser session...")
    linkedin_driver = None
    bing_driver = None

    try:
        if os.path.exists("linkedin_cookies.json"):
            linkedin_driver = get_driver(headless=True)
        else:
            linkedin_driver = get_driver(headless=False)
            log("NOTE: A browser window will open. Please log.")

        bing_driver = get_driver(headless=True)


        # Login once at the beginning
        log("Logging into LinkedIn...")
        login(linkedin_driver, login_confirmation_callback)
        log("Login successful!")

        for i in range(0, total_rows, batch_size):
            # Check stop flag before processing each batch
            if stop_flag and stop_flag.is_set():
                log("Stop signal received. Stopping processing.")
                return contacts_df

            batch_end = min(i + batch_size, total_rows)
            batch = contacts_df.iloc[i:batch_end]

            log(f"\n--- Processing batch {i//batch_size + 1} (rows {i+1}-{batch_end}) ---")
            log(f"Progress: {i+1}/{total_rows} contacts processed so far")

            # Track if any contacts in this batch were actually processed (not skipped)
            batch_processed = False

            for idx, row in batch.iterrows():
                # Check stop flag before processing each contact
                if stop_flag and stop_flag.is_set():
                    log("Stop signal received. Stopping processing.")
                    return contacts_df

                # Skip if already processed (Valid column has a boolean value)
                skip_valid = pd.notna(row['Valid']) and isinstance(row['Valid'], bool)
                skip_note = 'Note' in row and str(row['Note']).strip() == 'Profile not found'
                if skip_valid or skip_note:
                    log(f"Skipping {row['First Name']} {row['Last Name']} - already processed or marked as 'Profile not found'")
                    continue

                # Mark that we're processing at least one contact in this batch
                batch_processed = True

                # Join first and last name
                full_name = f"{row['First Name']} {row['Last Name']}"
                company_name = row['Account Name']

                search_count += 1
                log(f"Search #{search_count} (Row {idx+1}): Checking {full_name} at {company_name}")

                process_one_contact(
                    full_name,
                    company_name,
                    linkedin_driver,
                    bing_driver,
                    idx,
                    contacts_df,
                    search_count,
                    log,
                    login_confirmation_callback
                )

            # Only save and delay if contacts were actually processed in this batch
            if batch_processed:
                # Save progress after each batch
                if save_callback:
                    save_callback(contacts_df)
                else:
                    # Default behavior: save to contacts.csv
                    contacts_df.to_csv('contacts.csv', index=False)

                log(f"Batch {i//batch_size + 1} completed and saved")

                # Check browser health every 10 searches
                if search_count % 10 == 0:
                    linkedin_driver = health_check(linkedin_driver, "LinkedIn", search_count, log, login_confirmation_callback)
                    bing_driver = health_check(bing_driver, "Bing", search_count, log, login_confirmation_callback)

                gc.collect()

                # Delay between batches (except for the last batch) to avoid rate limiting
                if batch_end < total_rows:
                    log(f"Waiting {delay_between_batches} seconds before next batch...")
                    time.sleep(delay_between_batches)
            else:
                log(f"Batch {i//batch_size + 1} completed (all contacts already processed - no save/delay needed)")

            # Check stop flag
            if stop_flag and stop_flag.is_set():
                log("Stop signal received. Stopping processing.")
                break

        log(f"\nAll {total_rows} contacts processed successfully!")
        return contacts_df

    except Exception as e:
        log(f"Error during processing: {e}")
        raise

    finally:
        # Always close the browser when done
        if linkedin_driver:
            log("Closing LinkedIn browser...")
            cleanup_driver(linkedin_driver)
        if bing_driver:
            log("Closing Bing browser...")
            cleanup_driver(bing_driver)
        # Force garbage collection after cleanup
        gc.collect()
