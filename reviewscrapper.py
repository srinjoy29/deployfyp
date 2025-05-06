import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import random
import cloudscraper

# Random User Agents to reduce chance of getting blocked
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
]

def scrap_page(reviews_url):
    html_data = fetch_reviews_html(reviews_url)
    if html_data is None:
        return pd.DataFrame(columns=["Review"])

    reviews = extract_reviews(html_data)
    if not reviews:
        return pd.DataFrame(columns=["Review"])

    df_reviews = pd.DataFrame(reviews)
    df_reviews["Title"] = df_reviews.get("Title", pd.Series([""] * len(df_reviews)))
    df_reviews["Description"] = df_reviews.get("Description", pd.Series([""] * len(df_reviews)))
    df_reviews["Review"] = df_reviews["Title"].fillna('') + " " + df_reviews["Description"].fillna('')
    df_reviews = df_reviews[["Review"]]
    return df_reviews

def fetch_reviews_html(url):
    headers = {
        'authority': 'www.amazon.in',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://www.google.com/',
    }
    try:
        scraper = cloudscraper.create_scraper()  # This bypasses cloudflare and bot protections
        response = scraper.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        if soup.title:
            print(f"Fetched Page Title: {soup.title.string.strip()}")
        else:
            print("Could not fetch page title. Possibly blocked or wrong page.")
        
        return soup
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_reviews(soup):
    reviews = []
    review_boxes = soup.find_all('div', {'data-hook': 'review'})
    
    if not review_boxes:
        print("No reviews found on the page.")

    for box in review_boxes:
        name = box.select_one('.a-profile-name')
        stars = box.select_one('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]')
        title = box.select_one('[data-hook="review-title"]')
        date = box.select_one('[data-hook="review-date"]')
        description = box.select_one('[data-hook="review-body"]')

        review_data = {
            'Name': name.text.strip() if name else 'N/A',
            'Stars': stars.text.strip().split(' out')[0] if stars else 'N/A',
            'Title': title.text.strip() if title else '',
            'Date': parse_review_date(date.text.strip()) if date else 'N/A',
            'Description': description.text.strip() if description else '',
        }
        reviews.append(review_data)

    return reviews

def parse_review_date(date_text):
    try:
        if "on" in date_text:
            date_text = date_text.split(" on ")[-1]
        return datetime.strptime(date_text, '%d %B %Y').strftime("%d/%m/%Y")
    except ValueError:
        return 'N/A'

def web_scrapper(url):
    # Updated regex pattern to capture both formats of URLs
    pattern = r"(https:\/\/www\.amazon\.(in|com)\/[^\/]+)\/dp\/([^\/]+)"
    match = re.match(pattern, url)

    if match:
        product_url, _, product_id = match.groups()
        # Generating the reviews page URL
        reviews_url = f"{product_url}/product-reviews/{product_id}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        print("Fetching reviews from:", reviews_url)
        return scrap_page(reviews_url)
    else:
        print("Invalid Amazon product URL format.")
        return pd.DataFrame(columns=["Review"])

# Example usage
if __name__ == "__main__":
    product_link = input("Enter Amazon product URL: ").strip()
    df = web_scrapper(product_link)
    print(f"There are a total of {len(df)} reviews found.")
    print(df.head())
