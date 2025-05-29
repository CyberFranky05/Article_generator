import os
import glob
from flask import Flask, render_template, request, jsonify, send_from_directory
from search.search import perform_search
from template_generation.template_generation import  generate_template, save_template_to_md
from generate_article.generate_article import generate_articles_from_metadata
import logging
from template_generation.scrape_article import scrape_article
from openai import OpenAI
from dotenv import load_dotenv
from template_generation.parse_article import parse_article


load_dotenv()

app = Flask(__name__)

# --------- Frontend Endpoints ---------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search_page():
    try:
        return render_template('search.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-template')
def generate_template_page():
    return render_template('generate_template.html')

@app.route('/generate-article')
def generate_article_page():
    return render_template('generate_article.html')

@app.route('/generated-articles')
def generated_articles_page():
    return render_template('generated_articles.html')

# --------- API Endpoints ---------

@app.route('/api/search', methods=['POST'])
def api_search():
    print("Received a search request")  # Debug point 1
    data = request.json or request.form
    print(f"Request data: {data}")      # Debug point 2
    query = data.get('query')
    region = data.get('region', 'us')      # Default to 'us' if not provided
    language = data.get('language', 'en')  # Default to 'en' if not provided
    num_results = int(data.get('num_results', 10))  # Default to 10 if not provided
    if not query:
        print("No query provided")      # Debug point 3
        return jsonify({'error': 'Query is required'}), 400
    try:
        print(f"Calling perform_search with query: {query}, region: {region}, language: {language}, num_results: {num_results}")  # Debug point 4
        results = perform_search(query, region=region, language=language, num_results=num_results)
        print(f"Search results: {results}")                   # Debug point 5
        return jsonify({'results': results})
    except Exception as e:
        print(f"Error during search: {e}")                    # Debug point 6
        return jsonify({'error': str(e)}), 500
    


@app.route('/api/generate-template', methods=['POST'])
def api_generate_template():
    data = request.json
    url = data.get('url')
    language = data.get('language', 'en')
    detail_level = data.get('detail_level', 'standard')
    focus = data.get('focus')
    custom_section = data.get('custom_section')
    user_instructions = data.get('user_instructions')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        # 1. Scrape article
        text_path, html_path = scrape_article(url)

        # 2. Clean and parse article (HTML and Markdown)
        import os
        BASE_DIR = os.path.dirname(__file__)
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw_data')
        cleaned_article_path = os.path.join(RAW_DATA_DIR, "article_cleaned.html")
        parsed_article_md_path = os.path.join(DATA_DIR, "parsed_article.md")
        parse_article(html_path, cleaned_article_path, parsed_article_md_path)

        # 3. Read cleaned article text
        with open(cleaned_article_path, 'r', encoding='utf-8') as f:
            article_text = f.read()

        # 4. Generate template
        template = generate_template(
            article_text,
            language=language,
            detail_level=detail_level,
            focus=focus,
            custom_section=custom_section,
            user_instructions=user_instructions
        )
        md_path = save_template_to_md(template)
        return jsonify({
            'template': template,
            'template_path': md_path,
            'message': 'Template generated successfully.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/generate-articles', methods=['POST'])
def api_generate_articles():
    data = request.json or {}
    article_length = data.get('article_length', 'medium')
    tone = data.get('tone', 'neutral')
    custom_instructions = data.get('custom_instructions')
    num_articles = int(data.get('num_articles', 1))

    template_path = os.path.join(os.path.dirname(__file__), 'data', 'templates', 'template.md')
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'search', 'search_results.json')
    parsed_article_path = os.path.join(os.path.dirname(__file__), 'data', 'parsed_article.md')
    output_dir = os.path.join(os.path.dirname(__file__), 'data', 'generated_Article')

    try:
        # Load metadata
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            metadata_list = json.load(f)
        total_meta = len(metadata_list)
        if num_articles > total_meta:
            return jsonify({'error': f'Requested number of articles ({num_articles}) exceeds available metadata entries ({total_meta}).'}), 400
        metadata_list = metadata_list[:num_articles]

        # Save the sliced metadata to a temp file for generation
        temp_json_path = os.path.join(os.path.dirname(__file__), 'data', 'search', 'temp_search_results.json')
        with open(temp_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_list, f, ensure_ascii=False, indent=2)


        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=OPENAI_API_KEY)

        saved_files = generate_articles_from_metadata(
            template_path, temp_json_path, parsed_article_path, client, output_dir,
            article_length=article_length,
            tone=tone,
            custom_instructions=custom_instructions
        )
        return jsonify({'message': 'Articles generated successfully!', 'files': saved_files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generated-articles')
def api_generated_articles():
    articles_dir = os.path.join(os.path.dirname(__file__), 'data', 'generated_Article')
    articles = []
    if os.path.exists(articles_dir):
        for filepath in glob.glob(os.path.join(articles_dir, '*.html')):
            filename = os.path.basename(filepath)
            articles.append({'name': filename, 'url': f'/generated-articles/file/{filename}'})
    return jsonify({'articles': articles})

@app.route('/generated-articles/file/<filename>')
def serve_generated_article(filename):
    articles_dir = os.path.join(os.path.dirname(__file__), 'data', 'generated_Article')
    return send_from_directory(articles_dir, filename)

@app.route('/api/delete-article', methods=['POST'])
def api_delete_article():
    data = request.json
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
    articles_dir = os.path.join(os.path.dirname(__file__), 'data', 'generated_Article')
    filepath = os.path.join(articles_dir, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File does not exist'}), 404
    try:
        os.remove(filepath)
        return jsonify({'message': 'Article deleted successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)