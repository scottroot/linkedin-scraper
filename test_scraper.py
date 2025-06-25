#!/usr/bin/env python3
"""
Test script to debug LinkedIn scraper crashes
"""

import sys
import traceback
import gc
from linkedin_scraper.driver_and_login import get_driver, login, cleanup_driver
from linkedin_scraper.find_urls import get_linkedin_url_candidates
from linkedin_scraper.check_company import get_current_employer_with_matching_and_driver

def test_single_profile():
    """Test scraping a single profile to identify crash point"""
    print("Testing single profile scraping...")

    # Test data
    name = "John Doe"
    company = "Microsoft"

    try:
        print("1. Creating WebDriver...")
        driver = get_driver()
        print("✓ WebDriver created successfully")

        print("2. Logging into LinkedIn...")
        login(driver)
        print("✓ Login successful")

        print("3. Getting LinkedIn URL candidates...")
        profile_urls = get_linkedin_url_candidates(name, company, limit=1)
        print(f"✓ Found {len(profile_urls)} profile URLs")

        if profile_urls:
            test_url = profile_urls[0]
            print(f"4. Testing profile: {test_url}")

            try:
                result = get_current_employer_with_matching_and_driver(
                    driver,
                    test_url,
                    company,
                    verbose=True
                )
                print("✓ Profile scraping completed successfully")
                print(f"Result: {result}")

            except Exception as e:
                print(f"✗ Error during profile scraping: {e}")
                print("Full traceback:")
                traceback.print_exc()
                return False
        else:
            print("No profile URLs found to test")

    except Exception as e:
        print(f"✗ Error during setup: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False

    finally:
        print("5. Cleaning up...")
        cleanup_driver(driver)
        gc.collect()
        print("✓ Cleanup completed")

    return True

def test_memory_usage():
    """Test memory usage during scraping"""
    print("\nTesting memory usage...")

    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Initial memory usage: {initial_memory:.2f} MB")

    # Run the test
    success = test_single_profile()

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Final memory usage: {final_memory:.2f} MB")
    print(f"Memory increase: {final_memory - initial_memory:.2f} MB")

    return success

if __name__ == "__main__":
    print("LinkedIn Scraper Debug Test")
    print("=" * 50)

    try:
        # Test memory usage
        success = test_memory_usage()

        if success:
            print("\n✓ All tests passed!")
        else:
            print("\n✗ Tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)