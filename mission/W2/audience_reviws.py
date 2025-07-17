import requests
from bs4 import BeautifulSoup
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def scrape_rotten_tomatoes_reviews_selenium(url):
    all_reviews_data = []
    print(f"Scraping reviews from {url} using Selenium...")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.audience-review-row[data-qa="review-item"]'))
        )
        print("Initial page loaded.")

        count = 0

        while True:
            if count == 30:
                break
            count += 1

            try:
                load_more_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'rt-button[data-qa="load-more-btn"]'))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)
                load_more_button.click()
                print("Clicked 'Load More' button.")
                time.sleep(random.uniform(2, 4))
            except (NoSuchElementException, TimeoutException):
                print("No more 'Load More' button found or button not clickable.")
                break
            except Exception as e:
                print(f"An error occurred while clicking 'Load More': {e}")
                break

        print("All reviews loaded. Parsing page source.")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        review_blocks = soup.find_all('div', class_='audience-review-row', attrs={'data-qa': 'review-item'})

        if not review_blocks:
            print("Error: No review blocks found after loading all content.")
            return []

        for block in review_blocks:
            review_text = None
            sentiment_label = None

            # 리뷰 텍스트 추출
            text_element = block.find('p', attrs={'data-qa': 'review-text'})
            if text_element:
                review_text = text_element.get_text(strip=True)

            # 감성 라벨: rating-stars-group 사용
            stars_group = block.find('rating-stars-group')
            if stars_group and stars_group.has_attr('score'):
                try:
                    score = float(stars_group['score'])
                    if score >= 3:
                        sentiment_label = 'Positive'
                    else:
                        sentiment_label = 'Negative'
                except ValueError:
                    print(f"Invalid score format: {stars_group['score']}")

            if review_text and sentiment_label:
                all_reviews_data.append({
                    'text': review_text,
                    'sentiment': sentiment_label
                })

    except Exception as e:
        print(f"An unexpected error occurred during Selenium scraping: {e}")
    finally:
        if driver:
            driver.quit()

    return all_reviews_data

if __name__ == "__main__":
    target_url = "https://www.rottentomatoes.com/m/a_minecraft_movie/reviews?type=verified_audience"
    reviews_data = scrape_rotten_tomatoes_reviews_selenium(target_url)

    if reviews_data:
        print(f"\nSuccessfully scraped {len(reviews_data)} reviews.")
        with open("critic_reviews_labeled_minecraft.json", "w", encoding="utf-8") as f:
            json.dump(reviews_data, f, ensure_ascii=False, indent=4)
        print("Labeled reviews saved to critic_reviews_labeled.json")
    else:
        print("No reviews scraped or an error occurred.")
