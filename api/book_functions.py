import json
import textwrap
import urllib.request
from isbnlib import isbn_from_words, meta, cover


def get_isbn_for_book(title, author):

    """Retrieve ISBN number for a book based on its title and author."""

    text = title + ' ' + author
    query = text.replace(" ", "+")

    try:
        isbn = isbn_from_words(query)
    except:
        isbn = 'Unknown'

    print(f'Author: {author} - Book: {title} - ISBN: {isbn}')

    return isbn


def get_google_books_details_using_isbn(isbn, verbose=False):

    base_api_link = "https://www.googleapis.com/books/v1/volumes?q=isbn:"

    with urllib.request.urlopen(base_api_link + isbn) as f:
        text = f.read()

    decoded_text = text.decode("utf-8")
    obj = json.loads(decoded_text)
    volume_info = obj["items"][0]
    authors = obj["items"][0]["volumeInfo"]["authors"]

    title = volume_info["volumeInfo"]["title"]
    summary = textwrap.fill(volume_info["searchInfo"]["textSnippet"], width=65)
    author = " & ".join(authors)
    public_domain = volume_info["accessInfo"]["publicDomain"]
    page_count = volume_info["volumeInfo"]["pageCount"]
    language = volume_info["volumeInfo"]["language"]

    description = volume_info["volumeInfo"]["description"]
    categories = volume_info["volumeInfo"]["categories"]

    # clean summary
    summary = summary.replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    summary = summary.replace("\n", " ").replace("\r", " ").strip()
    summary = summary.replace("&#39;", "'").strip()

    if verbose:
        print("\nTitle:", title)
        print("\nSummary:\n")
        print(summary)
        print("\nAuthor(s):", author)
        print("\nPublic Domain:", public_domain)
        print("\nPage count:", page_count)
        print("\nLanguage:", language)
        print("\n***")

    return title, summary, author, public_domain, page_count, language, description, categories


def clean_isbn(isbn):

    """Clean up ISBN number by removing unwanted characters."""

    isbn = isbn.strip()
    isbn = isbn.replace("-", "").replace(" ", "")
    isbn = isbn.strip()

    return isbn


def get_book_meta_data_from_isbn(isbn, verbose=False):

    """Retrieve book metadata using its ISBN number."""

    title = authors = publisher = year = language = cover_url_thumbnail = cover_url_small_thumbnail = None

    try:
        meta_data = meta(isbn)
    except:
        meta_data = {}

    # TODO
    # check if all keys exist? error message

    try:
        meta_title = meta_data['Title'].strip()
        if meta_title:
            title = meta_title
    except KeyError:
        pass

    try:
        meta_authors = ' & '.join(meta_data['Authors']).strip()
        if meta_authors:
            authors = meta_authors
    except KeyError:
        pass

    try:
        meta_publisher = meta_data['Publisher'].strip()
        if meta_publisher:
            publisher = meta_publisher
    except KeyError:
        pass

    try:
        meta_year = meta_data['Year'].strip()
        if meta_year:
            year = meta_year
    except KeyError:
        pass

    try:
        meta_language = meta_data['Language'].strip()
        if meta_language:
            language = meta_language
    except KeyError:
        pass

    try:
        meta_cover_url_thumbnail = cover(isbn)['thumbnail'].strip()
        if meta_cover_url_thumbnail:
            cover_url_thumbnail = meta_cover_url_thumbnail
    except KeyError:
        pass

    try:
        meta_cover_url_small_thumbnail = cover(isbn)['smallThumbnail'].strip()
        if meta_cover_url_small_thumbnail:
            cover_url_small_thumbnail = meta_cover_url_small_thumbnail
    except KeyError:
        pass

    # retrieve book summary from Google using ISBN
    try:
        title, summary, author, public_domain, page_count, language, description, categories = get_google_books_details_using_isbn(isbn, verbose=False)

        # fill in data if not already set
        # if meta_title == 'Unknown':
        #     meta_title = title
        # if meta_authors == 'Unknown':
        #     meta_authors = author

        categories = ', '.join(categories) if categories else ""

    except:
        summary = 'Summary! Here is the summary.'
        public_domain = None
        page_count = None
        description = 'Description! Here is the description.'
        categories = ""

    if verbose:
        print(f'ISBN: {isbn} - Title: {title} - Author(s): {authors} - Publisher: {publisher} - Year: {year} - Language - {language}  - Cover URL Small Thumbnail: {cover_url_small_thumbnail} - Summary - {summary} - Public Domain: {public_domain} - Page Count: {page_count} - Description: {description} - Categories: {categories}')

    return isbn, title, authors, publisher, year, language, cover_url_thumbnail, cover_url_small_thumbnail, summary, public_domain, page_count, description, categories


def create_book_record_using_isbn(isbn: str):

    """Create a book record in the database."""

    isbn, title, authors, publisher, year, language, cover_url_thumbnail, cover_url_small_thumbnail, summary, public_domain, page_count, description, categories = get_book_meta_data_from_isbn(isbn)

    extended_summary = description
    full_text = "Full text goes here."

    # Populate empty fields with default values
    if title is None:
        title = "Unknown Title"
    if authors is None:
        authors = "Unknown Author"
    if publisher is None:
        publisher = "Unknown Publisher"
    if year is None:
        year = 0000
    if language is None:
        language = "Unknown Language"
    if cover_url_thumbnail is None:
        cover_url_thumbnail = "https://iili.io/FpkDnzg.png"
    if cover_url_small_thumbnail is None:
        cover_url_small_thumbnail = "https://iili.io/FpkDnzg.png"
    if summary is None:
        summary = "No summary available."
    if public_domain is None:
        public_domain = False
    if page_count is None:
        page_count = 0
    if extended_summary is None:
        extended_summary = "No extended summary available."
    if full_text is None:
        full_text = "No full text available."
    if categories is None:
        categories = ""

    book_record = {
        "isbn": isbn,
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "year": year,
        "language": language,
        "cover_url_thumbnail": cover_url_thumbnail,
        "cover_url_small_thumbnail": cover_url_small_thumbnail,
        "summary": summary,
        "extended_summary": extended_summary,
        "full_text": full_text,
        "public_domain": public_domain,
        "page_count": page_count,
        "categories": categories
    }

    return book_record


if __name__ == "__main__":

    # Example usage
    isbn = "9780135166307"
    book_record = create_book_record_using_isbn(isbn)
    print(book_record)
