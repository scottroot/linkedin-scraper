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
            # print(url)
            self.bing_driver.get(url)

            result_container = self.bing_driver.find_element(By.ID, "b_results")
            result_items = result_container.find_elements(By.CSS_SELECTOR, "li.b_algo")

            links = []
            for item in result_items:
                if len(links) >= limit:
                    break
                try:
                    link = item.find_element(By.CSS_SELECTOR, "h2 a")
                    href = link.get_attribute("href")
                    if href and "bing.com" not in href:
                        links.append(href)
                except:
                    continue  # skip malformed items

            return links
        except Exception as e:
            # print(f"Error running Bing search: {e}")
            cleanup_driver(self.bing_driver)
            raise e

    def cleanup(self):
        cleanup_driver(self.bing_driver)


# Example usage
if __name__ == "__main__":
    bing_search = BingSearch()
    links = bing_search.run_bing_search("Scott Hendrix", "LCN Services LLC", limit=1)
    for l in links:
        print(l)

    bing_search.cleanup()