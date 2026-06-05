import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import random
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "http://books.toscrape.com/catalogue/page-{}.html"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}

def scrape_page(page_num):
    url = BASE_URL.format(page_num)
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Page {page_num} failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    books = []

    for article in soup.select("article.product_pod"):
        title        = article.h3.a["title"]
        price        = float(article.select_one(".price_color").text.replace("£", "").replace("Â", "").strip())
        rating_word  = article.p["class"][1]
        rating       = RATING_MAP.get(rating_word, 0)
        availability = article.select_one(".availability").text.strip()
        in_stock     = 1 if availability == "In stock" else 0

        books.append({
            "title":        title,
            "price":        price,
            "rating":       rating,
            "rating_label": rating_word,
            "availability": availability,
            "in_stock":     in_stock,
        })

    return books

def scrape_all_books(total_pages=50):
    all_books = []
    print(f"Scraping {total_pages} pages from books.toscrape.com...")
    for page in range(1, total_pages + 1):
        page_books = scrape_page(page)
        all_books.extend(page_books)
        print(f"  Page {page:02d}/{total_pages} - {len(page_books)} books scraped")
        time.sleep(random.uniform(0.3, 0.7))
    return all_books

def generate_fallback_data(n=1000):
    print("WARNING: Using synthetic dataset for demonstration.")
    print("   Run on your local machine to scrape the real site.\n")
    np.random.seed(42)
    genres = ["Fiction", "Mystery", "Romance", "Science", "History",
              "Biography", "Children", "Fantasy", "Self-Help", "Travel"]
    titles = [f"{random.choice(genres)} Book {i+1}" for i in range(n)]
    prices = np.round(np.random.uniform(10, 60, n), 2)
    ratings = np.random.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.10, 0.20, 0.35, 0.30])
    rating_labels = {1:"One", 2:"Two", 3:"Three", 4:"Four", 5:"Five"}
    in_stock = np.random.choice([1, 0], n, p=[0.85, 0.15])
    availability = ["In stock" if s else "Out of stock" for s in in_stock]
    return pd.DataFrame({
        "title":        titles,
        "price":        prices,
        "rating":       ratings,
        "rating_label": [rating_labels[r] for r in ratings],
        "availability": availability,
        "in_stock":     in_stock,
    })

print("=" * 60)
print("WEB SCRAPING: BOOKS.TOSCRAPE.COM")
print("=" * 60)

try:
    test = requests.get("http://books.toscrape.com/catalogue/page-1.html",
                        headers=HEADERS, timeout=8)
    if test.status_code == 200 and "<article" in test.text:
        raw = scrape_all_books(total_pages=50)
        df  = pd.DataFrame(raw)
        print(f"\nScraping complete! Total books: {len(df)}")
    else:
        raise ConnectionError("Site returned non-200 or empty content.")
except Exception as e:
    print(f"\nWARNING: Live scraping unavailable ({e}).")
    df = generate_fallback_data(1000)

df.to_csv("books_data.csv", index=False)
print(f"Dataset saved as 'books_data.csv'  ({len(df)} rows)")

print("\nShape:", df.shape)
print("\nFirst 5 Rows:")
print(df.head())
print("\nData Types:")
print(df.dtypes)
print("\nMissing Values:")
print(df.isnull().sum())
print("\nPrice Statistics:")
print(df['price'].describe().round(2))
print("\nRating Distribution:")
print(df['rating'].value_counts().sort_index())
print("\nAvailability:")
print(df['availability'].value_counts())

sns.set_theme(style='whitegrid', palette='muted')
fig, axes = plt.subplots(2, 3, figsize=(17, 11))
fig.suptitle('Books.toscrape.com — Web Scraping Analysis',
             fontsize=18, fontweight='bold', y=1.01)

rating_counts = df['rating'].value_counts().sort_index()
star_labels   = ['⭐ One', '⭐⭐ Two', '⭐⭐⭐ Three', '⭐⭐⭐⭐ Four', '⭐⭐⭐⭐⭐ Five']
bar_colors    = ['#e74c3c','#e67e22','#f1c40f','#2ecc71','#27ae60']
axes[0, 0].bar(star_labels, [rating_counts.get(i, 0) for i in range(1, 6)],
               color=bar_colors, edgecolor='white', linewidth=1.2)
axes[0, 0].set_title('Rating Distribution')
axes[0, 0].set_ylabel('Number of Books')
axes[0, 0].tick_params(axis='x', rotation=20)
for bar in axes[0, 0].patches:
    axes[0, 0].text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.5,
                    str(int(bar.get_height())),
                    ha='center', fontsize=10, fontweight='bold')

axes[0, 1].hist(df['price'], bins=30, color='#3498db', edgecolor='white', alpha=0.9)
axes[0, 1].axvline(df['price'].mean(), color='red', linestyle='--', linewidth=2,
                   label=f"Mean: £{df['price'].mean():.2f}")
axes[0, 1].axvline(df['price'].median(), color='orange', linestyle='--', linewidth=2,
                   label=f"Median: £{df['price'].median():.2f}")
axes[0, 1].set_title('Price Distribution')
axes[0, 1].set_xlabel('Price (£)')
axes[0, 1].set_ylabel('Count')
axes[0, 1].legend()

avail_counts = df['availability'].value_counts()
axes[0, 2].pie(avail_counts.values,
               labels=avail_counts.index,
               autopct='%1.1f%%',
               colors=['#2ecc71', '#e74c3c'],
               startangle=90,
               wedgeprops=dict(edgecolor='white', linewidth=2))
axes[0, 2].set_title('Stock Availability')

avg_price_rating = df.groupby('rating')['price'].mean()
axes[1, 0].plot(avg_price_rating.index, avg_price_rating.values,
                marker='o', color='#9b59b6', linewidth=2.5, markersize=8)
axes[1, 0].fill_between(avg_price_rating.index, avg_price_rating.values,
                         alpha=0.15, color='#9b59b6')
axes[1, 0].set_title('Average Price by Rating')
axes[1, 0].set_xlabel('Star Rating')
axes[1, 0].set_ylabel('Average Price (£)')
axes[1, 0].set_xticks([1, 2, 3, 4, 5])

price_bins = pd.cut(df['price'], bins=[0, 20, 35, 50, 100],
                    labels=['£0–20', '£20–35', '£35–50', '£50+'])
price_bin_counts = price_bins.value_counts().sort_index()
axes[1, 1].bar(price_bin_counts.index, price_bin_counts.values,
               color=['#1abc9c','#3498db','#9b59b6','#e74c3c'],
               edgecolor='white', linewidth=1.2)
axes[1, 1].set_title('Books by Price Range')
axes[1, 1].set_xlabel('Price Range')
axes[1, 1].set_ylabel('Number of Books')
for bar in axes[1, 1].patches:
    axes[1, 1].text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + 0.5,
                    str(int(bar.get_height())),
                    ha='center', fontsize=10, fontweight='bold')

axes[1, 2].boxplot(
    [df[df['rating'] == r]['price'].values for r in range(1, 6)],
    labels=['1★', '2★', '3★', '4★', '5★'],
    patch_artist=True,
    boxprops=dict(facecolor='#3498db', color='navy'),
    medianprops=dict(color='red', linewidth=2),
    whiskerprops=dict(color='navy'),
    capprops=dict(color='navy'),
    flierprops=dict(marker='o', color='gray', alpha=0.4)
)
axes[1, 2].set_title('Price Distribution by Rating (Boxplot)')
axes[1, 2].set_xlabel('Star Rating')
axes[1, 2].set_ylabel('Price (£)')

plt.tight_layout()
plt.savefig('books_scraping.png', dpi=150, bbox_inches='tight')
plt.show()
print("\nPlot saved as 'books_scraping.png'")

print("\n" + "=" * 60)
print("KEY FINDINGS")
print("=" * 60)
print(f"  Total books scraped     : {len(df)}")
print(f"  Price range             : £{df['price'].min():.2f} – £{df['price'].max():.2f}")
print(f"  Average price           : £{df['price'].mean():.2f}")
print(f"  Most common rating      : {df['rating'].value_counts().idxmax()} stars")
print(f"  Books in stock          : {df['in_stock'].sum()} ({df['in_stock'].mean()*100:.1f}%)")
print(f"  Highest rated avg price : £{df[df['rating']==5]['price'].mean():.2f}")
print(f"  Lowest rated avg price  : £{df[df['rating']==1]['price'].mean():.2f}")
print("=" * 60)
