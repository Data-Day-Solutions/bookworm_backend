import os
import cv2
from flask import Flask, session, request, redirect, url_for, jsonify, Response, make_response
from supabase import create_client, Client
from flask_cors import CORS
import werkzeug
from PIL import Image
from io import BytesIO

# from flask_limiter import Limiter  # For rate limiting
# from flask_limiter.util import get_remote_address

try:
    from supabase_functions import add_book_record_using_isbn, get_authenticated_client, get_all_records, add_record
except (ImportError, ModuleNotFoundError):
    from api.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records

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

app.secret_key = 'your-very-secure-secret-key'  # Use an env var in production

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


@app.route('/upload_image_for_isbn', methods=["POST"])
def upload_image_for_isbn():

    """Endpoint to upload an image file."""

    # TODO - check if the user is authenticated before allowing image upload
    # validate inputs - look into pydantic
    if session:

        image_bytes = request.data

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
            book_record = create_book_record_using_isbn(isbn_number)

            return jsonify({
                "code": 200,
                "message": "Image Uploaded Successfully.",
                "data": book_record
            })

        except IndexError:
            return jsonify({"error": "No barcode detected in the image."}), 400
    else:
        return jsonify({"error": "User not authenticated."}), 401


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
        "code": 200,
        "message": "Login successful.",
    })


@app.route('/dashboard')
def dashboard():

    """Dashboard route that requires authentication."""

    client = get_authenticated_client()
    user = client.auth.get_user()

    if not user.user:
        return redirect(url_for('login'))

    return f"Welcome, {user.user.email}"


@app.route('/logout')
def logout():

    """Logout route to clear session tokens."""

    client = get_authenticated_client()
    client.auth.sign_out()

    session.pop('access_token', None)
    session.pop('refresh_token', None)

    # return redirect(url_for('login'))

    return jsonify({
        "code": 200,
        "message": "Logout successful.",
    })


@app.route('/add_book_using_isbn/<isbn>')
def add_book_using_isbn(isbn):

    """Add a book using its ISBN."""

    authenticated_supabase_client = get_authenticated_client()
    book_record_response = add_book_record_using_isbn(authenticated_supabase_client, isbn)
    if "error" in book_record_response:
        return jsonify({"error": book_record_response["error"]}), 400

    return book_record_response


@app.route('/create_new_library', methods=['POST'])
def create_new_library():

    """Create new library for users who are not assigned to one."""

    user = authenticated_supabase_client.auth.get_user()

    data = request.get_json()

    library_name = data.get('library_name')
    library_colour = data.get('library_colour')
    library_image_url = data.get('library_image_url')

    record = {"library_name": library_name,
              "library_colour": library_colour,
              "library_image": library_image_url}

    authenticated_supabase_client = get_authenticated_client()

    # TODO - add error handling for missing fields, ensure library name is unique, etc.

    add_record(authenticated_supabase_client, "library_details", record)

    return jsonify({
        "code": 200,
        "message": "Library creation successful.",
    })


@app.route('/get_library', methods=['GET'])
def get_library():

    """Finds the library for the user."""

    authenticated_supabase_client = get_authenticated_client()

    library_id = 0
    user = authenticated_supabase_client.auth.get_user()

    return jsonify({
        "code": 200,
        "library_id": library_id,
    })

@app.route('/get_all_books')
def get_all_books():

    """Retrieve all books"""

    authenticated_supabase_client = get_authenticated_client()
    response = get_all_records(authenticated_supabase_client, "books")

    # print(response.data)
    # print("got data")

    jsonified_books = jsonify({"books": response.data})

    return jsonified_books


if __name__ == '__main__':

    app.run(debug=True)
