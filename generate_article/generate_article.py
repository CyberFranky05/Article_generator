import os
import re
from openai import OpenAI
from dotenv import load_dotenv

def split_template_sections(template_path):
    '''Split the template Markdown file into sections based on headings.'''
    with open(template_path, 'r', encoding='utf-8') as f:
        template_text = f.read()
    sections = []
    current_title = None
    current_content = []
    for line in template_text.splitlines():
        heading_match = re.match(r'^(#+)\s+(.*)', line)
        if heading_match and heading_match.group(1) == "##":
            if current_title:
                sections.append((current_title, "\n".join(current_content).strip()))
            current_title = heading_match.group(2).strip()
            current_content = []
        else:
            current_content.append(line)
    if current_title:
        sections.append((current_title, "\n".join(current_content).strip()))
    return sections

def load_metadata(json_path):
    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_parsed_article(parsed_article_path):
    with open(parsed_article_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def generate_section_content(
    section_title, 
    section_template, 
    meta, 
    parsed_article, 
    client,
    article_length="medium", 
    tone="neutral", 
    custom_instructions=None, 
    content_so_far=None
):
    
    if (article_length == "short"):
        tokens = 500
    elif (article_length == "medium"):
        tokens = 1000
    elif (article_length == "long"):
        tokens = 1500
    else:
        toknes = 800
    """
    Generate content for a single section using GPT, outputting HTML.
    """
    prompt = (
        f"You are an expert SEO copywriter. Generate the '{section_title}' section for a product article in HTML format.\n"
        f"Section template (in Markdown):\n{section_template}\n\n"
        f"Metadata:\nTitle: {meta['title']}\nSnippet: {meta['snippet']}\nHighlights: {', '.join(meta.get('highlighted_words', []))}\n\n"
        f"Sample article for style reference:\n{parsed_article}\n\n"
        f"Article length: {article_length}\n"
        f"Tone: {tone}\n"
    )
    if custom_instructions:
        prompt += f"Custom instructions: {custom_instructions}\n"
    if content_so_far:
        prompt += f"Content generated so far:\n{content_so_far}\n\n"
    prompt += (
        "Write only the content for this section, in valid HTML. "
        "Be detailed, original, and match the tone and style of the sample article. "
        "Do not repeat previous sections."
    )
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant skilled at SEO article writing."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def generate_full_article_section_by_section(
    template_path, 
    meta, 
    parsed_article, 
    client,
    article_length="medium", 
    tone="neutral", 
    custom_instructions=None
):
    """
    Generate the full article by generating each section one by one and merging them.
    """
    sections = split_template_sections(template_path)
    article_sections = []
    content_so_far = ""
    for idx, (section_title, section_template) in enumerate(sections):
        section_content = generate_section_content(
            section_title, section_template, meta, parsed_article, client,
            article_length=article_length,
            tone=tone,
            custom_instructions=custom_instructions,
            content_so_far=content_so_far if idx > 0 else None
        )
        article_sections.append(section_content)
        content_so_far += "\n\n" + section_content
    return "\n\n".join(article_sections)

def save_article(content, save_path):
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(content)

def generate_articles_from_metadata(
    template_path, 
    json_path, 
    parsed_article_path, 
    client, 
    output_dir,
    article_length="medium", 
    tone="neutral", 
    custom_instructions=None
):
    """
    Generate articles for all metadata entries in the JSON file.
    """
    os.makedirs(output_dir, exist_ok=True)
    metadata_list = load_metadata(json_path)
    parsed_article = load_parsed_article(parsed_article_path)
    articles = []
    for idx, meta in enumerate(metadata_list):
        article_content = generate_full_article_section_by_section(
            template_path,
            meta, 
            parsed_article, 
            client,
            article_length=article_length,
            tone=tone,
            custom_instructions=custom_instructions
        )
        save_path = os.path.join(output_dir, f'article_{idx+1}.html')
        save_article(article_content, save_path)
        articles.append(save_path)
    return articles

if __name__ == "__main__":
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)

    template_path = r'd:\\automation_zip\\data\\templates\\template.md'
    parsed_article_path = r'd:\\automation_zip\\data\\parsed_article.txt'
    json_path = r'd:\\automation_zip\\data\\search\\search_results.json'

    # For demonstration, use the first metadata entry
    meta = load_metadata(json_path)[0]
    parsed_article = load_parsed_article(parsed_article_path)

    # Example usage with new options
    full_article = generate_full_article_section_by_section(
        template_path, meta, parsed_article, client,
        article_length="long",
        tone="indepth",
        custom_instructions="Highlight the product's unique selling points and avoid technical jargon."
    )
    save_path = r'd:\automation_zip\data\generated_Article\section_by_section_article.html'
    save_article(full_article, save_path)
    print(f"Article saved to {save_path}")