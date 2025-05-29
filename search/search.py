import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv()

API_KEY = os.getenv("SEARCH_API_KEY")

def perform_search(query, language='en', region='US', num_results=10):
    """
    Perform a search using SearchAPI.io's Google Search API.
    Returns simplified search results.
    """
    url = "https://www.searchapi.io/api/v1/search"
    
    params = {
        'engine': 'google',
        'api_key': API_KEY,
        'q': query,
        'google_domain': 'google.com',
        'gl': region,
        'hl': language,
        'num': num_results
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json().get('organic_results', [])
        
        # Print all available fields for each result
        print("=== Raw search result fields ===")
        for idx, result in enumerate(search_results, 1):
            print(f"\nResult {idx}:")
            for key, value in result.items():
                print(f"  {key}: {repr(value)}")
        print("=== End of results ===\n")
        
        # Extract only required fields (as before)
        simplified_results = []
        for result in search_results:
            simplified_result = {
                "title": result.get("title"),
                "snippet": result.get("snippet"),
                "highlighted_words": result.get("snippet_highlighted_words", [])
            }
            simplified_results.append(simplified_result)
            
        return simplified_results
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return []

def save_results_to_json(data):
    """
    Save search results to a fixed JSON file, overwriting existing content.
    """
    try:
        # Create the 'data/search' directory
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'search')
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, 'search_results.json')
        
        # Save and overwrite existing file
        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            
        return filepath
        
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

if __name__ == "__main__":
    query = input("Enter search query: ").strip()
    if not query:
        print("Search query cannot be empty.")
    else:
        language = input("Enter language (press Enter for 'en'): ").strip() or "en"
        region = input("Enter region (press Enter for 'US'): ").strip() or "US"
        
        results = perform_search(query, language, region)
        if results:
            if filepath := save_results_to_json(results):
                print(f"Search results saved to: {filepath}")
        else:
            print("No results found or an error occurred.")
