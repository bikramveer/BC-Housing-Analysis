# THIS IS A WEBSCRAPER FOR ZOLO AS A BACKUP,
# THIS SCRAPER IS NOT USED

import requests_html
from requests_html import HTMLSession
import pandas as pd
import time

def scrape_zolo_with_htmlsession(pages=2):
    session = HTMLSession()
    base_url = "https://www.zolo.ca/burnaby-real-estate/houses?page={}"
    all_listings = []

    for page in range(1, pages + 1):
        url = base_url.format(page)
        r = session.get(url)
        r.html.render(timeout=20)  # JavaScript rendering

        cards = r.html.find("article")

        for card in cards:
            try:
                address = card.find(".listing-card__address", first=True).text
                price = card.find(".listing-card__price", first=True).text
                beds = card.find(".listing-card__bedrooms", first=True).text
                baths = card.find(".listing-card__bathrooms", first=True).text
                sqft = card.find(".listing-card__size", first=True).text

                all_listings.append({
                    "Address": address,
                    "Price": price,
                    "Bedrooms": beds,
                    "Bathrooms": baths,
                    "SqFt": sqft,
                    "Age": "N/A",
                    "Parking": "N/A",
                    "TimeOnMarketDays": "N/A"
                })
            except Exception as e:
                print(f"Error: {e}")

        time.sleep(1)

    return pd.DataFrame(all_listings)

df = scrape_zolo_with_htmlsession(pages=2)
print(df.head())
