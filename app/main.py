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
from app.driver_and_login import get_driver, login, cleanup_driver, health_check_driver
from app.find_profile_urls import get_linkedin_url_candidates, BingSearch, BraveSearch
import pandas as pd
from app.logger import get_logger
from app.parse_profile.evaluate_company_match import normalize_company_name




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
        best_match = search_and_validate_profiles(
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

        # Determine final result based on best match found
        if best_match:
            # Extract the best match information
            company_match = best_match['company_match']
            best_match_info = company_match['any_match']
            best_score = best_match_info['match_result']['score']

            # Determine if they are currently employed at the target company
            is_currently_employed = company_match['has_current_match']

            log(f"Search #{search_count} (Row {idx+1}): Best match found with score {best_score}")
            log(f"Search #{search_count} (Row {idx+1}): Currently employed: {is_currently_employed}")
            log(f"Search #{search_count} (Row {idx+1}): Result: {is_currently_employed}")

            # Update the Valid column - True if they currently work there, False if they worked there in the past
            contacts_df.at[idx, 'Valid'] = is_currently_employed

            # Add note about historical match if applicable
            if not is_currently_employed and company_match['has_any_match']:
                contacts_df.at[idx, 'Note'] = 'Historical match found'
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid company matches found in any candidate profiles from either search")
            contacts_df.at[idx, 'Valid'] = False
            contacts_df.at[idx, 'Note'] = 'No company match found in any profile'

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


def search_and_validate_profiles(
    full_name,
    company_name,
    linkedin_driver,
    bing_driver,
    search_count,
    idx,
    log,
    max_candidates=3,
    search_threshold=0.6,
    linkedin_threshold=75,
    linkedin_timeout=15,
    bing_timeout=20,
    early_exit_threshold=85
):
    """
    Search for profiles using Bing first, then Brave if no valid matches found.
    Returns the best match found or None if no valid matches.
    """
    # Step 1: Try Bing search first
    log(f"Search #{search_count} (Row {idx+1}): Starting Bing search for {full_name} at {company_name}")

    url_candidates = get_linkedin_url_candidates(
        name=full_name,
        company=company_name,
        driver=bing_driver,
        limit=max_candidates,
        threshold=search_threshold,
        bing_timeout=bing_timeout
    )

    if url_candidates:
        log(f"Search #{search_count} (Row {idx+1}): Bing found {len(url_candidates)} candidates")

        # Validate Bing candidates
        best_match = validate_profile_candidates(
            url_candidates,
            full_name,
            company_name,
            linkedin_driver,
            search_count,
            idx,
            log,
            linkedin_threshold,
            linkedin_timeout,
            early_exit_threshold,
            search_source="Bing"
        )

        if best_match:
            log(f"Search #{search_count} (Row {idx+1}): Valid match found from Bing search")
            return best_match
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid matches from Bing candidates, trying Brave search")
    else:
        log(f"Search #{search_count} (Row {idx+1}): Bing search returned no candidates, trying Brave search")

    # Step 2: Try Brave search if Bing failed or returned no valid matches
    log(f"Search #{search_count} (Row {idx+1}): Starting Brave search for {full_name} at {company_name}")

    clean_company = normalize_company_name(company_name)
    brave_search_instance = BraveSearch()
    brave_results = brave_search_instance.run_brave_search(
        full_name,
        clean_company,
        limit=max_candidates,
        threshold=search_threshold
    )

    if brave_results:
        # Extract URLs from Brave results
        brave_urls = [result[0] for result in brave_results]
        log(f"Search #{search_count} (Row {idx+1}): Brave found {len(brave_urls)} candidates")

        # Validate Brave candidates
        best_match = validate_profile_candidates(
            brave_urls,
            full_name,
            company_name,
            linkedin_driver,
            search_count,
            idx,
            log,
            linkedin_threshold,
            linkedin_timeout,
            early_exit_threshold,
            search_source="Brave"
        )

        if best_match:
            log(f"Search #{search_count} (Row {idx+1}): Valid match found from Brave search")
            return best_match
        else:
            log(f"Search #{search_count} (Row {idx+1}): No valid matches from Brave candidates either")
    else:
        log(f"Search #{search_count} (Row {idx+1}): Brave search returned no candidates")

    # No valid matches found from either search
    log(f"Search #{search_count} (Row {idx+1}): No valid matches found from either Bing or Brave search")
    return None


def validate_profile_candidates(
    url_candidates,
    full_name,
    company_name,
    linkedin_driver,
    search_count,
    idx,
    log,
    linkedin_threshold,
    linkedin_timeout,
    early_exit_threshold,
    search_source="Unknown"
):
    """
    Validate a list of profile candidates and return the best match.
    """
    best_match = None
    best_score = 0
    best_profile_url = None
    found_good_match = False

    for i, profile_url in enumerate(url_candidates):
        try:
            log(f"Search #{search_count} (Row {idx+1}): Checking {search_source} candidate {i+1}/{len(url_candidates)}: {profile_url}")

            # Check employment status using the shared driver
            positions_and_company_match = get_positions_and_company_match(
                driver=linkedin_driver,
                profile_url=profile_url,
                target_company=company_name,
                threshold=linkedin_threshold,
                verbose=False,
                timeout=linkedin_timeout
            )

            # Check if this profile has a company match (current or historical)
            company_match = positions_and_company_match['company_match']

            if company_match['has_any_match']:
                # Get the best match score from this profile
                best_match_info = company_match['any_match']
                current_best_score = best_match_info['match_result']['score']

                # Log the type of match found
                match_type = "current position" if company_match['has_current_match'] else "historical position"
                log(f"Search #{search_count} (Row {idx+1}): {search_source} candidate {i+1} has company match in {match_type} with score {current_best_score}")

                # Update best match if this score is higher
                if current_best_score > best_score:
                    best_score = current_best_score
                    best_match = positions_and_company_match
                    best_profile_url = profile_url
                    log(f"Search #{search_count} (Row {idx+1}): New best match found! Score: {best_score}")

                # If we have a very good match (high confidence), stop checking other candidates
                if current_best_score >= early_exit_threshold:
                    log(f"Search #{search_count} (Row {idx+1}): Found excellent match with score {current_best_score} - stopping search")
                    found_good_match = True
                    break
            else:
                log(f"Search #{search_count} (Row {idx+1}): {search_source} candidate {i+1} has no company match in any position")

        except Exception as e:
            log(f"Search #{search_count} (Row {idx+1}): Error checking {search_source} candidate {i+1}: {e}")
            continue

        # If we found a good match, stop checking other candidates
        if found_good_match:
            log(f"Search #{search_count} (Row {idx+1}): Stopping {search_source} candidate search early due to excellent match")
            break

    # Log if we checked all candidates
    if not found_good_match and len(url_candidates) > 1:
        log(f"Search #{search_count} (Row {idx+1}): Checked all {len(url_candidates)} {search_source} candidates")

    return best_match
