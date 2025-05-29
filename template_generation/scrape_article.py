import os
from dotenv import load_dotenv
from newspaper import Article

# Load environment variables
load_dotenv()
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')

def scrape_article(url, filename=None):
    """
    Scrape main article content from a URL and save raw text and HTML in the raw_data folder.
    """
    article = Article(url)
    article.download()
    article.parse()
    article_text = article.text
    article_html = article.html

    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    # Use a safe filename based on URL or custom name
    if not filename:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        base = os.path.basename(parsed_url.path).replace('.', '_') or "article"
        filename = base
    text_path = os.path.join(RAW_DATA_DIR, f"{filename}.txt")
    html_path = os.path.join(RAW_DATA_DIR, f"{filename}.html")

    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(article_text)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(article_html)
    print(f"Raw text saved to: {text_path}")
    print(f"Raw HTML saved to: {html_path}")
    return text_path, html_path

if __name__ == "__main__":
    test_url = "https://www.boutique-bleuetdefrance.fr/produit/animale-gummies/"  # Replace with your test URL
    scrape_article(test_url)