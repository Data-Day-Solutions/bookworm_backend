import os
from flask import session
from dotenv import load_dotenv
from supabase import create_client, Client

try:
    from tools.book_functions import create_book_record_using_isbn, clean_isbn
except (ImportError, ModuleNotFoundError):
    from api.tools.book_functions import create_book_record_using_isbn, clean_isbn

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")


def get_authenticated_client() -> Client:

    """Get an authenticated Supabase client using session tokens."""

    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # TODO - add try except block to handle missing session tokens
    try:
        access_token = session['access_token']
        refresh_token = session['refresh_token']

        if access_token:
            supabase_client.auth.set_session(access_token, refresh_token)

    except (KeyError, ValueError, RuntimeError):
        return supabase_client

    return supabase_client


def get_all_records(authenticated_supabase_client: Client, table_name: str, columns: list = None):

    """Fetch all records from the Supabase database."""

    # add in optional columms selection
    if columns:
        data = authenticated_supabase_client.table(table_name).select(",".join(columns)).execute()
    else:
        data = authenticated_supabase_client.table(table_name).select("*").execute()

    return data


def check_book_exists(authenticated_supabase_client: Client, isbn: str):

    """Check if a book with the given ISBN exists in the Supabase database."""

    data = authenticated_supabase_client.table("books").select("book_id").eq("isbn", isbn).execute()

    return len(data.data) > 0


def add_book_record_using_isbn(authenticated_supabase_client: Client,
                               isbn: str):

    """Add a new record to the Supabase database."""

    isbn = clean_isbn(isbn)

    # Ensure the record is a dictionary with the required fields

    if not check_book_exists(authenticated_supabase_client, isbn):

        book_record = create_book_record_using_isbn(isbn)
        if book_record['title'] is None:
            return {"message": "Failed to create book record.", "data": None}

        authenticated_supabase_client.table("books").insert(book_record).execute()

    # use the ISBN to find the corresponding book_id - 1:1 relationship
    book_id = authenticated_supabase_client.table("books").select("book_id").eq("isbn", isbn).execute().data[0]
    book_details = authenticated_supabase_client.table("books").select("*").eq("isbn", isbn).execute().data[0]

    # get user's active library
    user_id = str(authenticated_supabase_client.auth.get_user().user.id)
    user_libraries = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).execute()

    # could be multiple libraries, but for now we assume one
    if user_libraries.data:
        library_id = user_libraries.data[0]['library_id']
    else:
        return {"message": "User does not have an active library. Re-direct to library creation.", "data": None}

    # check if book already exists in user's library
    existing_book = authenticated_supabase_client.table("user_library_books").select("*").eq("book_id", book_id['book_id']).eq("library_id", library_id).execute()
    if existing_book.data:
        # if it exists, increment the number of copies owned
        num_copies = existing_book.data[0]['num_copies_owned'] + 1
        authenticated_supabase_client.table("user_library_books").update({"num_copies_owned": num_copies}).eq("book_id", book_id['book_id']).eq("library_id", library_id).execute()
        book_details = authenticated_supabase_client.table("books").select("*").eq("isbn", isbn).execute().data[0]

        return {"message": "Book already exists in user's library. Incremented number of copies.", "data": book_details}

    else:
        # add book to user's library
        authenticated_supabase_client.table("user_library_books").insert({
            "book_id": book_id['book_id'],
            "num_copies_owned": 1,
            "location_info": "Unknown",
            "library_id": library_id
        }).execute()

        return {"message": f"Added new book to user's library.", "data": book_details}


def add_record(authenticated_supabase_client: Client,
               table_name: str, record: dict):

    """Add a new record to the Supabase database."""

    # Ensure the record is a dictionary with the required fields
    # TODO - Add validation for the record fields - matching table schema
    # TODO - Add error handling for record insertion

    # try:
    #     supabase.table(table_name).insert(record).execute()
    # except APIError:
    #     return {"error": "Failed to add record."}

    authenticated_supabase_client.table(table_name).insert(record).execute()


def update_record(authenticated_supabase_client: Client,
                  table_name: str, id: int, updated_data: dict):

    """Update a record in the Supabase database by its ID."""

    authenticated_supabase_client.table(table_name).update(updated_data).eq("book_id", id).execute()


def delete_record_by_id(authenticated_supabase_client: Client,
                        table_name: str, id: int, id_field: str):

    """Update a record in the Supabase database by its ID."""

    authenticated_supabase_client.table(table_name).delete().eq(f"{id_field}", id).execute()


def create_new_supabase_user(email: str, password: str):

    """Create a new user in the Supabase database."""

    # TODO - Add validation for username, email, and password
    # TODO - Add error handling for user creation

    authenticated_supabase_client = get_authenticated_client()

    try:
        auth_connection = authenticated_supabase_client.auth.sign_up({"email": email,"password": password,})
    except:
        return {"message": "Failed to create user. User may already exist.", "data": None}

    return {"message": "User created successfully.", "data": None}


def sign_in_user(authenticated_supabase_client: Client, email: str, password: str):

    """Sign in a user to the Supabase database."""

    # TODO - Add validation for username, email, and password
    # TODO - Add error handling for user sign-in

    authenticated_supabase_client.auth.sign_in_with_password({"email": email, "password": password})

    return authenticated_supabase_client


def check_session():

    """Check if a user session is active."""

    # check access token validity
    try:
        access_token = session['access_token']
        if access_token:
            return True
    except (KeyError, ValueError, RuntimeError):
        return False


if __name__ == "__main__":

    authenticated_supabase_client = get_authenticated_client()

    # # add record to non-RLS table
    # record = {"some_field": "whoa whoa whoa it's not authenticated!"}
    # authenticated_supabase_client.table('non_rls_table').insert(record).execute()

    # # try to add record to RLS table
    # try:
    #     record = {"test_value": "whoa whoa whoa it's not authenticated! this shouldn't work!"}
    #     authenticated_supabase_client.table('test_table').insert(record).execute()
    # except:
    #     print('Adding to RLS table prior to authentication failed as expected.')

    # authenticated_supabase_client = sign_in_user(authenticated_supabase_client, "davidshaw1985@gmail.com", "password123")

    # add_record(authenticated_supabase_client, "test_table", {"test_value": "whoa whoa whoa it's authenticated!"})