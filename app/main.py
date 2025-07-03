# This module takes company names found on LinkedIn and compares them to a target company name
import os
import time
import gc
from dotenv import load_dotenv
# Load environment variables
load_dotenv()


from app.driver_and_login import get_driver, login, cleanup_driver, health_check_driver
from app.find_profile_urls import find_profile_urls_and_validate
import pandas as pd
from app.logger import get_logger


def process_one_contact(
    full_name,
    company_name,
    linkedin_driver,
    bing_driver,
    idx,
    contacts_df,
    search_count,
    log,
    login_confirmation_callback=None,
    bing_timeout=20,
    search_threshold=0.6,
    linkedin_timeout=15,
    linkedin_threshold=75,
    max_candidates=3,
    early_exit_threshold=85
):
    """
    Process one contact, checking employment status and updating the CSV.

    This function now supports multi-candidate profile matching:
    1. Gets multiple LinkedIn profile candidates (up to max_candidates)
    2. Checks each candidate's employment history for company matches
    3. Stops early if a high-confidence match is found (score >= early_exit_threshold)
    4. Uses the best match found to determine employment status

    Args:
        full_name: Person's full name
        company_name: Company name to search for
        linkedin_driver: Selenium driver for LinkedIn
        bing_driver: Selenium driver for Bing search
        idx: DataFrame index for updating results
        contacts_df: DataFrame to update with results
        search_count: Current search count for logging
        log: Logging function
        login_confirmation_callback: Optional callback for login confirmation
        bing_timeout: Timeout for Bing search operations
        search_threshold: Fuzzy match threshold for search results (0.0-1.0)
        linkedin_timeout: Timeout for LinkedIn page loading
        linkedin_threshold: Company name match threshold percentage (0-100)
        max_candidates: Maximum number of profile candidates to check
        early_exit_threshold: Score threshold for early exit (0-100)
    """
    try:
        # Search and validate profiles with fallback logic
        best_match, best_profile_url = find_profile_urls_and_validate(
            full_name=full_name,
            company_name=company_name,
            linkedin_driver=linkedin_driver,
            bing_driver=bing_driver,
            search_count=search_count,
            idx=idx,
            log=log,
            max_candidates=max_candidates,
            search_threshold=search_threshold,
            linkedin_threshold=linkedin_threshold,
            linkedin_timeout=linkedin_timeout,
            bing_timeout=bing_timeout,
            early_exit_threshold=early_exit_threshold
        )

        if best_match:
            company_match = best_match['company_match']
            best_match_info = company_match['any_match']
            best_score = best_match_info['match_result']['score']
            is_currently_employed = company_match['has_current_match']

            log(f"Search #{search_count} (Row {idx+1}): Best match found with score {best_score}")
            log(f"Search #{search_count} (Row {idx+1}): Currently employed: {is_currently_employed}")
            log(f"Search #{search_count} (Row {idx+1}): Result: {is_currently_employed}")

            # Update the Valid column - True if they currently work there, False if they worked there in the past
            contacts_df.at[idx, 'Valid'] = is_currently_employed

            # Add the Profile URL to the DataFrame
            if best_profile_url:
                contacts_df.at[idx, 'Profile URL'] = best_profile_url
                log(f"Search #{search_count} (Row {idx+1}): Profile URL recorded: {best_profile_url}")

            # Add note about historical match if applicable
            if not is_currently_employed and company_match['has_any_match']:
                contacts_df.at[idx, 'Note'] = 'Historical match found'
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid company matches found in any candidate profiles from either search")
            contacts_df.at[idx, 'Valid'] = False
            contacts_df.at[idx, 'Note'] = 'No company match found in any profile'
            # Clear Profile URL if no match found
            if 'Profile URL' in contacts_df.columns:
                contacts_df.at[idx, 'Profile URL'] = ''

    except IndexError as e:
        log(f"Search #{search_count} (Row {idx+1}): Error: No LinkedIn profiles found for {full_name} at {company_name} (likely rate limited)")
        contacts_df.at[idx, 'Note'] = 'Profile not found - Maybe rate limited?'
        # Clear Profile URL if there's an error
        if 'Profile URL' in contacts_df.columns:
            contacts_df.at[idx, 'Profile URL'] = ''
        # Force garbage collection after error
        gc.collect()
    except Exception as e:
        log(f"Search #{search_count} (Row {idx+1}): Error processing {full_name}: {str(e)}")
        log(f"Search #{search_count} (Row {idx+1}): Error type: {type(e).__name__}")
        # Mark as False if there's an error
        contacts_df.at[idx, 'Note'] = str(e)
        # Clear Profile URL if there's an error
        if 'Profile URL' in contacts_df.columns:
            contacts_df.at[idx, 'Profile URL'] = ''
        # Force garbage collection after error
        gc.collect()

        # Check if we're around the 50 mark and log it
        if 45 <= search_count <= 55:
            log(f"Search #{search_count} (Row {idx+1}): WARNING - Error occurred around the 50-contact mark. This might indicate rate limiting or resource issues.")


def process_contacts_batch(
        contacts_df,
        batch_size=1,
        delay_between_batches=10,
        log_callback=None,
        save_callback=None,
        stop_flag=None,
        login_confirmation_callback=None,
        bing_timeout=20,
        search_threshold=0.6,
        linkedin_timeout=15,
        linkedin_threshold=75,
        keep_linkedin_open=False
    ):
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
        bing_timeout: Timeout in seconds for Bing search operations
        search_threshold: Fuzzy match threshold for search results (0.0-1.0)
        linkedin_timeout: Timeout in seconds for LinkedIn page loading
        linkedin_threshold: Company name match threshold percentage (0-100)
        keep_linkedin_open: If True, keep LinkedIn browser visible even when cookies exist
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

    # Add Profile URL column if it doesn't exist
    if 'Profile URL' not in contacts_df.columns:
        contacts_df['Profile URL'] = ''

    total_rows = len(contacts_df)
    log(f"Processing {total_rows} contacts in batches of {batch_size}")

    # Track search statistics
    search_count = 0

    # Initialize a single browser session for all processing
    log("Initializing browser session...")
    linkedin_driver = None
    bing_driver = None

    try:
        if os.path.exists("linkedin_cookies.json") and not keep_linkedin_open:
            linkedin_driver = get_driver(headless=True)
        else:
            linkedin_driver = get_driver(headless=False)
            if keep_linkedin_open:
                log("NOTE: Keep LinkedIn Browser Open is enabled - browser window will be visible")
            else:
                log("NOTE: A browser window will open. Please log in.")

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

                # Health check before processing each contact
                if not health_check_driver(linkedin_driver, "LinkedIn"):
                    log(f"Search #{search_count} (Row {idx+1}): Restarting LinkedIn driver...")

                    if os.path.exists("linkedin_cookies.json") and not keep_linkedin_open:
                        linkedin_driver = get_driver(headless=True)
                    else:
                        linkedin_driver = get_driver(headless=False)
                    login(linkedin_driver, login_confirmation_callback)
                    log("LinkedIn driver restarted successfully")

                if not health_check_driver(bing_driver, "Bing"):
                    log(f"Search #{search_count} (Row {idx+1}): Restarting Bing driver...")
                    bing_driver = get_driver(headless=True)
                    log("Bing driver restarted successfully")

                process_one_contact(
                    full_name,
                    company_name,
                    linkedin_driver,
                    bing_driver,
                    idx,
                    contacts_df,
                    search_count,
                    log,
                    login_confirmation_callback,
                    bing_timeout,
                    search_threshold,
                    linkedin_timeout,
                    linkedin_threshold,
                    max_candidates=5,
                    early_exit_threshold=85
                )

            # Only save and delay if contacts were actually processed in this batch
            if batch_processed:
                # Save progress after each batch
                if save_callback:
                    save_callback(contacts_df)
                else:
                    # Default behavior: save to contacts.csv
                    contacts_df.to_csv('contacts.csv', index=False, encoding='utf-8')

                log(f"Batch {i//batch_size + 1} completed and saved")

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



