import os
from flask import Flask, session, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from supabase import create_client, Client

try:
    from book_functions import create_book_record_using_isbn
except (ImportError, ModuleNotFoundError):
    from api.book_functions import create_book_record_using_isbn

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


def get_all_records(authenticated_supabase_client: Client, table_name: str):

    """Fetch all records from the Supabase database."""

    data = authenticated_supabase_client.table(table_name).select("*").execute()

    return data


def check_book_exists(authenticated_supabase_client: Client, isbn: str):

    """Check if a book with the given ISBN exists in the Supabase database."""

    # Returns True if the book exists, False otherwise

    data = authenticated_supabase_client.table("books").select("book_id").eq("isbn", isbn).execute()

    return len(data.data) > 0


def add_book_record_using_isbn(authenticated_supabase_client: Client,
                               isbn: str):

    """Add a new record to the Supabase database."""

    # Ensure the record is a dictionary with the required fields

    if check_book_exists(authenticated_supabase_client, isbn):
        return {"error": "Book with this ISBN already exists."}

    book_record = create_book_record_using_isbn(isbn)

    # only add the book record if it was created successfully
    if book_record['title'] is None:
        return {"error": "Failed to create book record."}

    authenticated_supabase_client.table("books").insert(book_record).execute()

    return {"success": f"Added new book. {book_record}"}


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


def create_new_user(authenticated_supabase_client: Client, email: str, password: str):

    """Create a new user in the Supabase database."""

    # TODO - Add validation for username, email, and password
    # TODO - Add error handling for user creation

    auth_connection = authenticated_supabase_client.auth.sign_up({"email": email,"password": password,})

    return {"message": "User created successfully."}


def sign_in_user(authenticated_supabase_client: Client, email: str, password: str):

    """Sign in a user to the Supabase database."""

    # TODO - Add validation for username, email, and password
    # TODO - Add error handling for user sign-in

    authenticated_supabase_client.auth.sign_in_with_password({"email": email, "password": password})

    return authenticated_supabase_client


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