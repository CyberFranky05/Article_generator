import os
from dotenv import load_dotenv
import openai
from template_generation.scrape_article import scrape_article
from template_generation.parse_article import parse_article


# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')
TEMPLATE_PATH = os.path.join(DATA_DIR, 'templates', 'template.md')

def extract_article_metadata(article_text):
    words = article_text.split()
    headers = [line for line in article_text.splitlines() if line.lower().startswith(("##", "###", "####"))]
    return {
        "word_count": len(words),
        "estimated_read_time": f"{len(words) // 200} min",
        "section_headers": headers
    }


def generate_template(article_text, language="en", detail_level="standard", focus=None, custom_section=None, user_instructions=None): 
    detail_map = {
        "basic": "Keep the template concise with only essential sections.",
        "standard": "Include all standard sections and subsections for a comprehensive article.",
        "in-depth": "Make the template very detailed, with many subsections, prompts, and advanced structure."
    }
    focus_text = f"Focus especially on: {focus}." if focus else ""
    custom_section_text = f"Add a custom section: {custom_section}." if custom_section else ""
    user_instructions_text = f"- {user_instructions}" if user_instructions else ""

    prompt = f"""
You are an expert content strategist and technical writer.

Generate a universal, reusable Markdown template for high-quality product articles or reviews in {language.upper()}.

Instructions:
- {detail_map.get(detail_level, detail_map['standard'])}
- {focus_text}
- {custom_section_text}
- f"Follow the users instructions: {user_instructions_text}"
- Use clear Markdown headings and subheadings.
- For each section, provide a short description or placeholder text (e.g., [Insert product description here]).
- Use bullet points, numbered lists, and tables where appropriate.
- Do NOT copy any actual product-specific content from the article; only use it to inspire the structure and flow.
- Ensure the template is easy to follow and encourages thorough, unbiased, and engaging content.

Web page content for reference: {article_text}

Generate only the Markdown template, focusing strictly on article-related information.
"""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in article structure and content generation."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.7
    )
    return response.choices[0].message.content

def save_template_to_md(template, path=TEMPLATE_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(template)
    return path

def run_pipeline(url):
    print("[1] Scraping article...")
    text_path, html_path = scrape_article(url)

    print("[2] Cleaning article...")
    cleaned_article_path = os.path.join(RAW_DATA_DIR, "article_cleaned.html")
    parsed_article_md_path = os.path.join(DATA_DIR, "parsed_article.md")
    parse_article(html_path, cleaned_article_path, parsed_article_md_path)

    print("[3] Reading cleaned article text...")
    with open(cleaned_article_path, 'r', encoding='utf-8') as f:
        article_text = f.read()

    print("[4] Generating template...")
    template = generate_template(article_text)

    print("[5] Saving template...")
    saved_path = save_template_to_md(template)
    print(f"✅ Template saved to: {saved_path}")

if __name__ == "__main__":
    test_url = "https://www.boutique-bleuetdefrance.fr/produit/animale-gummies/"  # Replace with your test URL
    run_pipeline(test_url)

