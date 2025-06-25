# This module takes company names found on LinkedIn and compares them to a target company name
import os
import re
import time
import gc
from app.parse_profile import get_positions_and_company_match
from app.parse_profile.extract_experience import get_current_employer
from fuzzywuzzy import fuzz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.driver_and_login import get_driver, login, cleanup_driver
from app.find_urls import get_linkedin_url_candidates
import pandas as pd
from app.logger import get_logger


def process_contacts_batch(contacts_df, batch_size=1, delay_between_batches=10, log_callback=None, save_callback=None, stop_flag=None):
    """
    Process contacts in batches, checking employment status and updating the CSV

    Args:
        contacts_df: DataFrame with contact information
        batch_size: Number of contacts to process before saving
        delay_between_batches: Seconds to wait between batches to avoid rate limiting
        log_callback: Optional callback function for logging messages
        save_callback: Optional callback function for saving progress
        stop_flag: Optional threading.Event or similar to check for stop signal
    """
    logger = get_logger()

    def log(message):
        if log_callback:
            log_callback(message)
        else:
            logger.info(message)

    total_rows = len(contacts_df)
    log(f"Processing {total_rows} contacts in batches of {batch_size}")

    # Initialize a single browser session for all processing
    log("Initializing browser session...")
    linkedin_driver = None
    bing_driver = None

    try:
        if os.path.exists("linkedin_cookies.json"):
            linkedin_driver = get_driver(headless=True)
        else:
            linkedin_driver = get_driver(headless=False)
        bing_driver = get_driver(headless=True)


        # Login once at the beginning
        log("Logging into LinkedIn...")
        log("NOTE: A browser window will open. Please log in manually if needed.")
        login(linkedin_driver)
        log("Login successful!")

        for i in range(0, total_rows, batch_size):
            # Check stop flag before processing each batch
            if stop_flag and stop_flag.is_set():
                log("Stop signal received. Stopping processing.")
                return contacts_df

            batch_end = min(i + batch_size, total_rows)
            batch = contacts_df.iloc[i:batch_end]

            log(f"\n--- Processing batch {i//batch_size + 1} (rows {i+1}-{batch_end}) ---")

            for idx, row in batch.iterrows():
                # Check stop flag before processing each contact
                if stop_flag and stop_flag.is_set():
                    log("Stop signal received. Stopping processing.")
                    return contacts_df

                # Skip if already processed (Valid column has a boolean value)
                if pd.notna(row['Valid']) and isinstance(row['Valid'], bool):
                    log(f"Skipping {row['First Name']} {row['Last Name']} - already processed")
                    continue

                # Join first and last name
                full_name = f"{row['First Name']} {row['Last Name']}"
                company_name = row['Account Name']

                log(f"Checking: {full_name} at {company_name}")

                try:
                    profile_url = get_linkedin_url_candidates(
                        name=full_name,
                        company=company_name,
                        driver=bing_driver,
                        limit=1,
                        threshold=0.6
                    )[0]
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

                except Exception as e:
                    log(f"Error processing {full_name}: {e}")
                    # Mark as False if there's an error
                    contacts_df.at[idx, 'Valid'] = False
                    # Force garbage collection after error
                    gc.collect()

            # Save progress after each batch
            if save_callback:
                save_callback(contacts_df)
            else:
                # Default behavior: save to contacts.csv
                contacts_df.to_csv('contacts.csv', index=False)

            log(f"Batch {i//batch_size + 1} completed and saved")

            # TODO: do we really need GC??
            # Force garbage collection after each batch
            gc.collect()

            # TODO: why do we need to delay in between batches...???
            # # Delay between batches (except for the last batch)
            # if batch_end < total_rows:
            #     log(f"Waiting {delay_between_batches} seconds before next batch...")
            #     time.sleep(delay_between_batches)

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
