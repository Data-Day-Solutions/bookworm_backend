import base64
import os
import cv2
from flask import Flask, session, request, redirect, url_for, jsonify, Response, make_response
from supabase import create_client, Client
from flask_cors import CORS
import werkzeug
from PIL import Image
from io import BytesIO
from datetime import timedelta

import pandas as pd
from tqdm import tqdm

# from flask_limiter import Limiter  # For rate limiting
# from flask_limiter.util import get_remote_address

try:
    from supabase_functions import add_book_record_using_isbn, get_authenticated_client, get_all_records, add_record, create_new_supabase_user
except (ImportError, ModuleNotFoundError):
    from api.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records, create_new_supabase_user
try:
    from image_recognition import detect_and_decode_barcode
except (ImportError, ModuleNotFoundError):
    from api.image_recognition import detect_and_decode_barcode

try:
    from book_functions import create_book_record_using_isbn
except (ImportError, ModuleNotFoundError):
    from api.book_functions import create_book_record_using_isbn

app = Flask(__name__)

CORS(app, 
    supports_credentials=True,
    origins=["http://localhost:19260"]
)

app.config.update(
    SESSION_COOKIE_SAMESITE='None',
    SESSION_COOKIE_SECURE=True,
)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)
app.secret_key = 'your-very-secure-secret-key'  # Use an env var in production

# session.clear()  # Clear session at startup for fresh state

# Configure rate limiter
# limiter = Limiter(
#     get_remote_address,  # Use IP address for rate limiting
#     app=app,
#     default_limits=["200 per day", "50 per hour"],  # Default limits for all routes
#     storage_uri="memory://"  # Store rate limiting data in memory
# )

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/')
def index():
    return jsonify({"message": "Hello from Flask on Vercel!"})


@app.route('/dashboard')
def dashboard():

    """Dashboard route that requires authentication."""

    client = get_authenticated_client()
    user = client.auth.get_user()

    if not user.user:
        return redirect(url_for('login'))

    return jsonify({
        "message": "Dasboard re-direction successful.",
        "data": None
    }), 200


# create route to load data from a provided csv file
@app.route('/upload_isbn_csv', methods=['POST'])
def upload_isbn_csv():

    """Endpoint to upload a CSV file."""

    if session:

        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request.", "data": None}), 400
        file = request.files['file']

        if file.filename == '':
            return jsonify({"message": "No selected file.", "data": None}), 400

        if file and werkzeug.utils.secure_filename(file.filename).endswith('.csv'):
            filename = werkzeug.utils.secure_filename(file.filename)
            upload_filename = os.path.join('api', 'uploads', filename)
            file.save(upload_filename)

            # Process the CSV file here
            isbn_df = pd.read_csv(upload_filename)

            # Process df and add records to the database
            # Ensure the 'ISBN' column exists in the DataFrame
            if 'ISBN' not in isbn_df.columns:
                return jsonify({"message": "CSV file must contain an 'ISBN' column.", "data": None}), 400

            # Extract ISBNs from the DataFrame
            isbn_list = isbn_df['ISBN'].tolist()
            isbn_list = [str(isbn).strip() for isbn in isbn_list if pd.notna(isbn)]  # Ensure ISBNs are strings and not NaN
            for isbn in tqdm(isbn_list):

                # Create book record using the ISBN
                authenticated_supabase_client = get_authenticated_client()
                message = add_book_record_using_isbn(authenticated_supabase_client, isbn)

            os.remove(upload_filename)

            # TODO - add error handling for missing ISBNs, invalid ISBNs, etc. Inform user about the number of books added.
            # TODO - also provide user information about the books that were not added due to errors
            # TODO - return the list of added books or a summary of the operation
            # TODO - mention duplicate ISBNs and how they were handled

            return jsonify({"message": "File uploaded successfully. Books added.", "data": None}), 200
        else:
            return jsonify({"message": "Invalid file format. Only CSV files are allowed.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/upload_image_for_isbn', methods=["POST"])
def upload_image_for_isbn():

    """Endpoint to upload an image file."""

    # TODO - check if the user is authenticated before allowing image upload
    # validate inputs - look into pydantic
    if session:
        data = request.get_json()

        image_base64 = data['base64_image']
        image_bytes = base64.b64decode(image_base64)

        file_id = "000001"  # This should be generated dynamically, e.g., using a UUID or database ID
        filename = "api/images/temp_filename_" + file_id

        im = Image.open(BytesIO(image_bytes))
        im_format = im.format
        im.save(f'{filename}.{im_format}')

        filename = filename + f'.{im_format}'
        image = cv2.imread(filename)
        barcodes = detect_and_decode_barcode(image)
        os.remove(filename)

        # get the possible ISBNs from the barcodes
        try:

            # TODO - If multiple barcodes are detected, use the first one - needs to be improved
            isbn_number = barcodes[0]

            authenticated_supabase_client = get_authenticated_client()

            # adds book to main library and returns the book record - for user to confirm to add to their library
            book_record = add_book_record_using_isbn(authenticated_supabase_client, isbn_number)

            return jsonify(book_record), 200

        except IndexError:
            return jsonify({"message": "No barcode detected in the image.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/create_new_user', methods=['POST'])
def create_new_user():

    """Route to create users."""

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    # handle errors

    response = create_new_supabase_user(email, password)

    # TODO - Ensure that response is in standard format

    return jsonify(response), 200


@app.route('/login', methods=['POST'])
def login():

    """Login route to authenticate users."""

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    # handle errors

    res = supabase.auth.sign_in_with_password({'email': email, 'password': password})

    session['access_token'] = res.session.access_token
    session['refresh_token'] = res.session.refresh_token

    # return redirect(url_for('dashboard'))
    # return redirect(url_for('cracked.com'))

    return jsonify({
        "message": "Login successful.",
        "data": None
    }), 200


@app.route('/logout', methods=['GET'])
def logout():

    """Logout route to clear session tokens."""

    client = get_authenticated_client()
    client.auth.sign_out()

    session.pop('access_token', None)
    session.pop('refresh_token', None)

    # return redirect(url_for('login'))

    return jsonify({
        "message": "Logout successful.",
        "data": None
    }), 200


@app.route('/add_book_using_isbn/<isbn>')
def add_book_using_isbn(isbn):

    """Add a book using its ISBN."""

    authenticated_supabase_client = get_authenticated_client()

    if session:

        book_record_response = add_book_record_using_isbn(authenticated_supabase_client, isbn)

        return book_record_response, 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/create_new_library', methods=['POST'])
def create_new_library():

    """Create new library for users who are not assigned to one."""

    if session:

        authenticated_supabase_client = get_authenticated_client()
        user_id = str(authenticated_supabase_client.auth.get_user().user.id)

        # check if user already has a library - one per user initially
        user_libraries = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).execute()
        if user_libraries.data:
            return jsonify({"message": "User already has a library.", "data": None}), 403
        else:
            data = request.get_json()

            library_name = data.get('library_name')
            library_colour = data.get('library_colour')
            library_image_url = data.get('library_image_url')

            # check that library/-name does not coincide with existing libraries
            existing_libraries = authenticated_supabase_client.table("library_details").select("*").eq("library_name", library_name).execute()
            if existing_libraries.data:
                return jsonify({"message": "Library name already exists. Please choose an alternative.", "data": None}), 403

            record = {"library_name": library_name,
                      "library_colour": library_colour,
                      "library_image": library_image_url}

            # TODO - add error handling for missing fields, ensure library name is unique, etc.
            add_record(authenticated_supabase_client, "library_details", record)

            # associate user with newly created library by adding user to library_users table
            new_library_id = authenticated_supabase_client.table("library_details").select("*").eq("library_name", library_name).execute().data[0]['library_id']

            # do not add a record if there is a matching one on both user_id and library_id
            existing_user_library = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).eq("library_id", new_library_id).execute()
            if not existing_user_library.data:
                authenticated_supabase_client.table("library_users").insert({
                    "user_id": user_id,
                    "library_id": new_library_id,
                    "library_role": "admin"  # Default role for the user creating the library
                     # - ensures that only they can invite new users to library and remove user
                }).execute()

            return jsonify({
                "message": "Library creation successful. User assigned to library.",
                "data": record}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/get_user_library', methods=['GET'])
def get_library():

    """Finds the library for the user."""

    authenticated_supabase_client = get_authenticated_client()

    library_id = 0
    user_id = str(authenticated_supabase_client.auth.get_user().user.id)
    user_libraries = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).execute()

    # could be multiple libraries, but for now we assume one
    if user_libraries.data:
        library_id = user_libraries.data[0]['library_id']
    else:
        return {"message": "User does not have an active library. Re-direct to library creation.", "data": None}

    return jsonify({
        "library_id": library_id,
        "data": None
    }), 200


@app.route('/get_all_user_books')
def get_all_user_books():

    """Retrieve all books for the authenticated user."""

    if session:

        authenticated_supabase_client = get_authenticated_client()

        user_library_details = get_library()
        user_library_id = user_library_details[0].json['library_id']

        response = authenticated_supabase_client.table("user_library_books").select(
            """
            *,
            books (*)
            """
        ).eq("library_id", user_library_id).execute()

        # Flatten the response - each row contains a 'books' field with book details
        flattened_results = []
        for row in response.data:
            flat_row = row.copy()
            book_data = flat_row.pop("books", {})
            flat_row.update(book_data)
            flattened_results.append(flat_row)

        jsonified_books = jsonify({"books": flattened_results})

        return jsonified_books

    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/remove_book_from_library/<int:book_id>', methods=['DELETE'])
def remove_book_from_library(book_id):

    """Remove a book from the user's library."""

    if session:

        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_library()
            user_library_id = user_library_details[0].json['library_id']

            # delete the book from the user's library
            authenticated_supabase_client.table("user_library_books").delete().eq("book_id", book_id).eq("library_id", user_library_id).execute()
            return jsonify({"message": "Book removed from user's library.", "data": None}), 200

        except Exception as e:
            return jsonify({"message": "Error removing book from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# fucntion to remove all books from the user's library
@app.route('/remove_all_books_from_library', methods=['DELETE'])
def remove_all_books_from_library():

    """Remove all books from the user's library."""

    if session:
        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_library()
            user_library_id = user_library_details[0].json['library_id']

            # delete all books from the user's library
            authenticated_supabase_client.table("user_library_books").delete().eq("library_id", user_library_id).execute()
            return jsonify({"message": "All books removed from user's library.", "data": None}), 200

        except Exception as e:
            return jsonify({"message": "Error removing all books from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@app.route('/get_all_books')
def get_all_books():

    """Retrieve all books."""

    if session:

        authenticated_supabase_client = get_authenticated_client()
        response = get_all_records(authenticated_supabase_client, "books")

        jsonified_books = jsonify({"books": response.data})

        return jsonified_books
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# TODO - add a route to invite another user to an existing library
# check that the user is authenticated
# check that the user is an admin of the library
# send an email to the invited user with a link to accept the invitation
# or just add the user to the library_users table - they do need to have an account already
# check and inform admin if the user has not fully registered yet
# add the invited user to the library_users table


if __name__ == '__main__':

    app.run(debug=True)
