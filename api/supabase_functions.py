import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")


def get_all_records(table_name: str):

    """Fetch all records from the Supabase database."""

    supabase = create_client(url, key)
    data = supabase.table(table_name).select("*").execute()

    return data


def check_book_exists(isbn: str):

    """Check if a book with the given ISBN exists in the Supabase database."""

    # Returns True if the book exists, False otherwise
    supabase = create_client(url, key)
    data = supabase.table("books").select("book_id").eq("isbn", isbn).execute()

    return len(data.data) > 0


def add_record(table_name: str, record: dict):

    """Add a new record to the Supabase database."""

    # Ensure the record is a dictionary with the required fields

    # Check if book is already in the database by using ISBN - probably should do this check at the start before creating the book record.
    # Extra safety check.
    if table_name == "books" and "isbn" in record:
        if check_book_exists(record.get("isbn")):
            return {"error": "Book with this ISBN already exists."}

    supabase = create_client(url, key)
    supabase.table(table_name).insert(record).execute()


def update_record(table_name: str, id: int, updated_data: dict):

    """Update a record in the Supabase database by its ID."""

    supabase = create_client(url, key)
    supabase.table(table_name).update(updated_data).eq("book_id", id).execute()


def delete_record(table_name: str, id: int, id_field: str):

    """Update a record in the Supabase database by its ID."""

    supabase = create_client(url, key)
    supabase.table(table_name).delete().eq("{id_field}", id).execute()


def create_new_user(username: str, email: str, password: str):

    """Create a new user in the Supabase database."""

    supabase = create_client(url, key)
    data = supabase.auth.sign_up(email=email, password=password)

    if data.error:
        return {"error": data.error.message}

    user_data = {
        "username": username,
        "email": email,
        "user_id": data.user.id
    }

    add_record("users", user_data)
    return {"message": "User created successfully."}


def sign_in_user(email: str, password: str):

    """Sign in a user to the Supabase database."""

    supabase = create_client(url, key)
    session = supabase.auth.sign_in(email=email, password=password)

    if session.error:
        return {"error": session.error.message}

    return {"message": "User signed in successfully.", "user_id": session.user.id}

    return session


def sign_out_user():

    """Sign out the current user from the Supabase database."""

    supabase = create_client(url, key)
    supabase.auth.sign_out()

    return {"message": "User signed out successfully."}


# test_record = {'isbn': '123456789',
#                'title': 'TEST TITLE',
#                'publisher': 'TEST PUBLISHER',
#                'year': 2025, 'language': 'EN',
#                'cover_url_thumbnail': 'TEST_SOME_URL',
#                'cover_url_small_thumbnail': 'TEST_SOME_URL',
#                'summary': 'TEST_SUMMARY',
#                'extended_summary': 'TEST EXTENDED SUMMARY',
#                'full_text': 'TEST FULL TEXT'}

# add_book_record(test_record)
# book_exists_flag = check_book_exists('1234567890')
# books = get_books()
# print(books)
