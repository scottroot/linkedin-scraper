from app.driver_and_login import get_driver, cleanup_driver, login
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def find_experience_section(driver):
    """Try multiple strategies to find the experience section"""

    # Common selectors for experience sections
    experience_selectors = [
        "section[data-view-name='profile-card']",
        "section[id*='experience']",
        "section[aria-labelledby*='experience']",
        ".pv-profile-section.experience-section",
        ".pvs-list",
        ".artdeco-card.pv-profile-section"
    ]

    for selector in experience_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"Found experience section with selector: {selector}")
                return elements
        except Exception as e:
            print(f"Error with selector {selector}: {e}")
            continue

    # If no specific selectors work, try finding by text content
    try:
        sections = driver.find_elements(By.TAG_NAME, "section")
        for section in sections:
            if "experience" in section.get_attribute("innerHTML").lower():
                print("Found experience section by text content")
                return [section]
    except Exception as e:
        print(f"Error searching by text content: {e}")

    return []

driver = get_driver(headless=True)
login(driver)
driver.get("https://linkedin.com/in/scott-hendrix")

# exp = find_experience_section(driver)
# for el in exp:
#     print(el.get_attribute('outerHTML'))
# print(exp)
# cleanup_driver(driver)
from bs4 import BeautifulSoup
try:
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "li.artdeco-list__item"))
    )

    # main = driver.find_element(By.TAG_NAME, "main")
    # html = main.get_attribute("innerHTML")
    # soup = BeautifulSoup(html, 'html.parser')
    # exp_div = soup.find("div", id="experience", class_="pv-profile-card__anchor")
    # print(exp_div)
    # parent_section = exp_div.find_parent("section")
    # print(parent_section.get_text())

    for i, section in enumerate(driver.find_elements(By.CSS_SELECTOR, "section.artdeco-card")):
        section_html = section.get_attribute('innerHTML') or ""
        soup = BeautifulSoup(section_html, 'html.parser')
        exp_div = soup.find("div", id="experience", class_="pv-profile-card__anchor")
        if(exp_div):
            print(exp_div)
            print("This is it: ", i)
except Exception as err:
    cleanup_driver(driver)
    raise
finally:
    cleanup_driver(driver)

