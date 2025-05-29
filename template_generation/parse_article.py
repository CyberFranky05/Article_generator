from bs4 import BeautifulSoup
import markdownify

def parse_article(html_path, output_path, md_output_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, "html.parser")

    # Remove the most obviously unwanted tags commonly found in web pages
    for tag in soup(['header', 'footer', 'nav', 'aside', 'form', 'script', 'style', 'noscript', 'iframe']):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, type(soup.Comment))):
        comment.extract()

    # Remove common sidebar, widget, and ad containers by class/id patterns
    for selector in [
        '.sidebar', '.widget', '.ad', '.ads', '.advertisement', '.breadcrumb', '.footer', '.header', '.nav', '.popup',
        '#sidebar', '#widget', '#ad', '#ads', '#advertisement', '#breadcrumb', '#footer', '#header', '#nav', '#popup'
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    # Save the cleaned HTML (structure is preserved, only obvious junk is removed)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    print(f"Simply cleaned article saved to: {output_path}")

    # --- Save as Markdown (now mandatory) ---
    md_content = markdownify.markdownify(str(soup), heading_style="ATX")
    with open(md_output_path, 'w', encoding='utf-8') as f_md:
        f_md.write(md_content)
    print(f"Parsed article (Markdown) saved to: {md_output_path}")

if __name__ == "__main__":
    input_html_path = r'd:\automation_zip\data\raw_data\article.html'
    output_html_path = r'd:\automation_zip\data\raw_data\article_cleaned.html'
    md_output_path = r'd:\automation_zip\data\parsed_article.md'
    parse_article(input_html_path, output_html_path, md_output_path)