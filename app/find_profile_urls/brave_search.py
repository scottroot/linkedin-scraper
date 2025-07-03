"""
The Brave Search API does not log queries or associate them with your identity.
https://api-dashboard.search.brave.com/

Search Operators
ext:
    Returns web pages with a specific file extension.
    Example: to find the Honda GX120 Owner’s manual in PDF, type “Honda GX120
    ownners manual ext:pdf”.
filetype:
    Returns web pages created in the specified file type.
    Example: to find a web page created in PDF format about the evaluation of age-related cognitive changes, type “evaluation of age cognitive changes filetype:pdf”.
inbody:
    Returns web pages containing the specified term in the body of the page.
    Example: to find information about the Nvidia GeForce GTX 1080 Ti, making sure the page contains the keywords “founders edition” in the body, type “nvidia 1080 ti inbody:“founders edition””.
intitle:
    Returns webpages containing the specified term in the title of the page.
    Example: to find pages about SEO conferences making sure the results contain
    2023 in the title, type “seo conference intitle:2023”.
inpage:
    Returns webpages containing the specified term either in the title or in the
    body of the page.
    Example: to find pages about the 2024 Oscars containing the keywords
    “best costume design” in the page, type “oscars 2024 inpage:“best costume design””.
lang or language:
    Returns web pages written in the specified language. The language code must
    be in the ISO 639-1 two-letter code format.
    Example: to find information on visas only in Spanish, type “visas lang:es”.
loc or location:
    +: Returns web pages containing the specified term either in the title or
        the body of the page. Example: to find information about FreeSync GPU
        technology, making sure the keyword “FreeSync” appears in the result,
        type “gpu +freesync”.
    -: Returns web pages not containing the specified term neither in the title
        nor the body of the page. Example: to search web pages containing the
        keyword “office” while avoiding results with the term “Microsoft”, type
        “office -microsoft”.
    "": Returns web pages containing only exact matches to your query.
        Example: to find web pages about Harry Potter only containing the
        keywords “order of the phoenix” in that exact order, type “harry potter
        “order of the phoenix””.

----

Additionally, you can use logical operators in your queries.

AND:
    Only returns web pages meeting all the conditions. Example: to search for
    information on visas in English in web pages from the United Kingdom, type
    “visa loc:gb AND lang:en”.
OR:
    Returns web pages meeting any of the conditions. Example: to search for
    travelling requirements for Australia or New Zealand, type “travel requirements inpage:australia OR inpage:“new zealand””.
NOT:
    Returns web pages which do not meet the specified condition(s). Example: to
    search for information on Brave Search, but you want to exclude results from
    brave.com, type “brave search NOT site:brave.com”.


"""
import sys
sys.path.append("/Users/scomax/Documents/Git/linkedin-scraper")
from app.matching import normalize_company_name

from typing import List, Literal, Optional, Tuple
import requests
from dotenv import load_dotenv
import os
import json
from app.logger import get_logger
from difflib import SequenceMatcher


load_dotenv()


def brave_search(
    query: str,
    country: Optional[str] = "US",
    search_lang: Optional[str] = "en",
    ui_lang: Optional[str] = "en-US",
    count: Optional[int] = 20,
    offset: Optional[int] = 0,
    safesearch: Optional[Literal["off", "moderate", "strict"]] = "moderate",
    spellcheck: Optional[bool] = True,
    freshness: Optional[str] = None,
    text_decorations: Optional[bool] = True,
    result_filter: Optional[Literal["discussions", "faq", "infobox", "news", "query", "summarizer", "videos", "web", "locations"]] = "web",
):
    """
    Search the Brave search engine for a given query.

    Authentication:
        - The Brave Search API does not log queries or store search data.
        - Your Brave API key must be stored in the .env file as `BRAVE_API_KEY`.

    Args:
        - query: The client's search query term. The min query length is 1,
          max query length is 400, and the word limit 50.
        - country: The 2 character country code where the search results come
          from. The default value is US.
        - search_lang: The 2 or more character language code for which the
          search results are provided. This is optional and defaults to en.
        - ui_lang: User interface language preferred in response. Usually of the
          format <language_code>-<country_code> See RFC 9110.
        - count: The number of search results returned in response. The default
          is 20 and the maximum is 20. The actual number delivered may be less
          than requested.
        - offset: The zero based offset that indicates number of search result
          pages (count) to skip before returning the result. The default is 0
          and the maximum is 9. The actual number delivered may be less than
          requested.
        - safesearch: The safe search level. The default is moderate. Available
          options are:
            * off - No safe search.
            * moderate - Moderate safe search.
            * strict - Strict safe search.
        - spellcheck: A Boolean value that determines whether the spell checker
          should be enabled. The default is True.
        - freshness: Filters search results, when they were discovered, by date
          range. The following time deltas are supported.
            * Day - pd - Discovered in last 24 hours.
            * Week - pw - Discovered in last 7 Days.
            * Month - pm - Discovered in last 31 Days.
            * Year - py - Discovered in last 365 Days.
            A timeframe is also supported by specifying the date range in the
            format YYYY-MM-DDtoYYYY-MM-DD.
        - text_decorations: A Boolean value that determines whether display
          strings should contain decoration markers such as hit highlighting
          characters. If true, the strings may include markers. The default is
          True.
        - result_filter: A comma delimited list of result types to include in
          the search response.
            * Defaults to "web".
            * Available filters are:
                * discussions
                * faq
                * infobox
                * news
                * query
                * summarizer
                * videos
                * web
                * locations
        - extra_snippets: Extra snippets in results. The default is False.
        - summary: Enable summary for query. The default is False.
    """
    # Build params dict, only including non-default values
    params = {"q": query}  # query is always required

    # Only add parameters if they differ from defaults
    if country != "US":
        params["country"] = country
    if search_lang != "en":
        params["search_lang"] = search_lang
    if ui_lang != "en-US":
        params["ui_lang"] = ui_lang
    if count != 20:
        params["count"] = count
    if offset != 0:
        params["offset"] = offset
    if safesearch != "moderate":
        params["safesearch"] = safesearch
    if spellcheck != True:
        params["spellcheck"] = spellcheck
    if freshness is not None:
        params["freshness"] = freshness
    if text_decorations != True:
        params["text_decorations"] = text_decorations
    if result_filter is not None:
        params["result_filter"] = result_filter

    response = requests.get(
        "https://api.search.brave.com/res/v1/web/search",
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "x-subscription-token": os.getenv("BRAVE_API_KEY")
        },
        params=params
    ).json()



    response_query = response["query"]

    response_results = []
    for t in ["discussions", "faq", "infobox", "news", "summarizer", "videos",
              "web", "locations"]:
        if t in response:
            response_results.extend([
                {
                    "title": r["title"],
                    "url": r["url"],
                    "description": r["description"],
                    "site": r["profile"]["name"],
                    "url": r["profile"]["url"],
                }
                for r in response[t]["results"]
            ])

    return response_results


class BraveSearch:
    def __init__(self):
        self.logger = get_logger()

    def run_brave_search(self, name: str, company: str, limit: int = 5, threshold: float = 0.6) -> List[Tuple[str, str, float]]:
        """
        Search Brave for LinkedIn profiles with fuzzy validation

        Args:
            name (str): Person's name
            company (str): Company name
            limit (int): Maximum number of results to return
            threshold (float): Minimum fuzzy match threshold

        Returns:
            List[Tuple[str, str, float]]: List of (url, title, similarity_score) tuples
        """
        try:
            self.logger.info(f"Starting Brave search for '{name}' at '{company}' with threshold {threshold}")

            # Construct search query
            search_query = f'site:linkedin.com/in "{name}" "{company}"'

            # Perform Brave search
            self.logger.debug(f"Brave search query: {search_query}")
            results = brave_search(
                query=search_query,
                count=limit,
                result_filter="web"
            )

            self.logger.debug(f"Brave search returned {len(results)} raw results")
            for i, result in enumerate(results):
                self.logger.debug(f"Raw result {i+1}: {result}")

            validated_results = []
            for result in results:
                self.logger.debug(f"Processing result: {result.get('title', 'No title')} - {result.get('url', 'No URL')}")
                if "linkedin.com/in/" in result.get("url", ""):
                    title = result.get("title", "")

                    # Clean up the title - remove common LinkedIn suffixes
                    if title:
                        suffixes_to_remove = [
                            " | Professional Profile",
                            " | LinkedIn",
                            " - Professional Profile",
                            " - LinkedIn",
                            " | Business Profile",
                            " - Business Profile"
                        ]
                        for suffix in suffixes_to_remove:
                            if title.endswith(suffix):
                                title = title[:-len(suffix)].strip()
                                break

                    # Validate the title against the name
                    if title and title.strip():
                        # Clean title for comparison - remove location info
                        clean_title = title
                        # Remove location patterns like " - City, State, Country"
                        if " - " in clean_title:
                            clean_title = clean_title.split(" - ")[0].strip()

                        similarity = SequenceMatcher(None, name.lower(), clean_title.lower()).ratio()
                        self.logger.debug(f"Comparing '{name}' with '{clean_title}' (similarity: {similarity:.2f})")

                        if similarity >= threshold:
                            validated_results.append((result["url"], title, similarity))
                            self.logger.info(f"Brave: Valid match found - {title} (similarity: {similarity:.2f})")
                        else:
                            self.logger.debug(f"Brave: Skipping low similarity match - {title} (similarity: {similarity:.2f})")
                    else:
                        # Title is empty, extract name from LinkedIn URL for validation
                        url_parts = result["url"].split('/')
                        if len(url_parts) >= 5:
                            profile_name = url_parts[4].replace('-', ' ').replace('_', ' ')
                            similarity = SequenceMatcher(None, name.lower(), profile_name.lower()).ratio()
                            self.logger.debug(f"Comparing '{name}' with '{profile_name}' from URL (similarity: {similarity:.2f})")

                            if similarity >= threshold:
                                validated_results.append((result["url"], profile_name, similarity))
                                self.logger.info(f"Brave: Valid match found (from URL) - {profile_name} (similarity: {similarity:.2f})")
                            else:
                                self.logger.debug(f"Brave: Skipping low similarity match (from URL) - {profile_name} (similarity: {similarity:.2f})")
                        else:
                            # If we can't extract name from URL, include with lower confidence
                            validated_results.append((result["url"], "Unknown", 0.5))
                            self.logger.debug(f"Brave: Including URL with unknown name: {result['url']}")

            # Sort by similarity score (highest first)
            validated_results.sort(key=lambda x: x[2], reverse=True)

            self.logger.info(f"Brave search completed. Found {len(validated_results)} validated results")
            return validated_results

        except Exception as e:
            self.logger.error(f"Error in Brave search: {e}")
            return []


if __name__ == "__main__":
    # Example usage:
    NAME = "Anas Hayajneh"

    COMPANY = "aq network"

    query = f'site:linkedin.com/in "{NAME}" {COMPANY}'
    # results = brave_search(
    #     query,
    #     # spellcheck=False,
    #     result_filter="web"
    #     # country="mx",
    # )
    # print(json.dumps(results, indent=4))

    normalized_company_name = normalize_company_name(COMPANY)

    brave_search_instance = BraveSearch()
    brave_results = brave_search_instance.run_brave_search(
        NAME,
        normalized_company_name,
        limit=5,
        threshold=0.6
    )
    print(json.dumps(brave_results, indent=4))