# should add  in more tests - CI/CD - PRs - GitHub Build
import pytest

from book_functions import get_isbn_for_book, get_google_books_details_using_isbn, get_book_meta_data_from_isbn, create_book_record

# title = "The Hitchhiker's Guide to the Galaxy"
# author = "Douglas Adams"
# isbn = "9780345391803"

# title = "A Brief History of Time"
# author = "Stephen Hawking"
isbn = "9780553380163"
isbn = "978-0718178444"

# test_isbn = get_isbn_for_book(title, author)
# title, summary, author, public_domain, page_count, language = get_google_books_details_using_isbn(test_isbn, verbose=True)
# title, authors, publisher, year, language, cover_url_thumbnail, cover_url_small_thumbnail, summary, public_domain, page_count = get_book_meta_data_from_isbn(isbn, verbose=True)

book_record = create_book_record(isbn)
print(book_record)
