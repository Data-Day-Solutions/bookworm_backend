import requests
from bs4 import BeautifulSoup
import re

def get_lexile_measure(url: str) -> str:

    """
    Scrapes the Lexile page and extracts the Lexile measure (e.g., '770L').

    Args:
        url (str): The URL of the Lexile book details page.

    Returns:
        str: The Lexile measure if found, otherwise None.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page, status code {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Look for the Lexile measure (contains text like "770L")
    pattern = re.compile(r'\b\d{3,4}L\b')
    # pattern = 'div id="main"'
    lexile_tag = soup.find(string=pattern)

    if lexile_tag:
        return lexile_tag.strip()
    else:
        return None


if __name__ == "__main__":

    # Example usage
    url = "https://hub.lexile.com/find-a-book/details/9781911171195/"
    # url = "https://hub.lexile.com/find-a-book/results?term=9781911171195&sort_by%5Blabel%5D=Relevance&sort_by%5Bvalue%5D=-score"
    print(get_lexile_measure(url))
