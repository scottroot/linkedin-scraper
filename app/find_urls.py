# from googlesearch import search
from typing import List
from app.driver_and_login import get_driver, cleanup_driver
from selenium.webdriver.common.by import By


class BingSearch:
    def __init__(self):
        self.bing_driver = get_driver(headless=True)

    def run_bing_search(self, name, company, limit=5):
        try:
            site = "site%3Alinkedin.com%2Fin%20"
            name = '"' + name.replace(" ", "%20") + '"'
            company = company.replace(" ", "%20")# + '"'
            params = "&".join([
                "qs=n",  # Query suggestion behavior. n means no suggestions.
                "form=QBRE",  # Form type. QBRE means it was entered directly into the Bing search bar.
                "sp=-1",  # Controls spelling corrections. -1 means Bing should decide automatically.
                "ghc=1",  # Enables grouping of related results (grouped hit count).
                "lq=0",  # Local query flag; 0 usually means no local context used.
                "sk=",  # Search keywords. Empty here, possibly reserved.
                "ajf=100"  # Possibly related to autocomplete or justification features.
            ])
            url = "https://www.bing.com/search?" + params + "&q=" + site + "%20" + name + "%20" + company
            print(f"Searching Bing for: {name} at {company}")
            self.bing_driver.get(url)

            result_container = self.bing_driver.find_element(By.ID, "b_results")
            result_items = result_container.find_elements(By.CSS_SELECTOR, "li.b_algo")

            print(f"Found {len(result_items)} search results")

            links = []
            for item in result_items:
                if len(links) >= limit:
                    break
                try:
                    link = item.find_element(By.CSS_SELECTOR, "h2 a")
                    href = link.get_attribute("href")
                    if href and "bing.com" not in href:
                        links.append(href)
                        print(f"Found LinkedIn URL: {href}")
                except:
                    continue  # skip malformed items

            print(f"Returning {len(links)} valid LinkedIn URLs")
            for l in links:
                print(f"\t- {l}")
            print()
            return links
        except Exception as e:
            print(f"Error running Bing search: {e}")
            cleanup_driver(self.bing_driver)
            raise e

    def cleanup(self):
        cleanup_driver(self.bing_driver)


def get_linkedin_url_candidates(name, company, limit=5) -> List[str]:
    """
    Search for LinkedIn profile URLs for a given name and company

    Args:
        name (str): Person's name
        company (str): Company name
        limit (int): Maximum number of results to return

    Returns:
        list: List of LinkedIn profile URLs
    """
    try:
        print(f"Starting LinkedIn URL search for '{name}' at '{company}'")
        # results = search(
        #     f'site:linkedin.com/in "{name}" "{company}"',
        #     num_results=limit
        # )
        # return list(results)
        bing_search = BingSearch()
        links = bing_search.run_bing_search(name, company, limit=limit)
        bing_search.cleanup()
        print(f"URL search completed. Found {len(links)} URLs")
        return links
    except Exception as e:
        print(f"Error searching for LinkedIn URLs: {e}")
        return []


if __name__ == "__main__":
    name = "Scott Hendrix"
    company = "LCN Services LLC"
    limit = 10

    results = get_linkedin_url_candidates(name, company, limit)

    for r in results:
        print(r)

    # bing_search = BingSearch()
    # links = bing_search.run_bing_search("Scott Hendrix", "LCN Services LLC", limit=1)
    # for l in links:
    #     print(l)

    # bing_search.cleanup()