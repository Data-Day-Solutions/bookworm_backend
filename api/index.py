import os
from flask import Flask, session, request, redirect, url_for, jsonify
from supabase import create_client, Client
from flask_cors import CORS

try:
    from supabase_functions import add_book_record_using_isbn, get_authenticated_client
except (ImportError, ModuleNotFoundError):
    from api.supabase_functions import add_book_record_using_isbn, get_authenticated_client

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = 'your-very-secure-secret-key'  # Use an env var in production

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/')
def index():
    return jsonify({"message": "Hello from Flask on Vercel!"})


@app.route('/login', methods=['POST'])
def login():

    """Login route to authenticate users."""

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    res = supabase.auth.sign_in_with_password({'email': email, 'password': password})

    session['access_token'] = res.session.access_token
    session['refresh_token'] = res.session.refresh_token

    # return redirect(url_for('dashboard'))
    # return redirect(url_for('cracked.com'))

    return jsonify({
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
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
    return redirect(url_for('bbc.co.uk'))


@app.route('/add_book_using_isbn/<isbn>')
def add_book_using_isbn(isbn):

    """Add a book using its ISBN."""

    authenticated_supabase_client = get_authenticated_client()
    book_record_response = add_book_record_using_isbn(authenticated_supabase_client, isbn)
    if "error" in book_record_response:
        return jsonify({"error": book_record_response["error"]}), 400

    return book_record_response


if __name__ == '__main__':
    app.run(debug=True)

# TypeError: The view function did not return a valid response. The return type must be a string, dict, list,
#  tuple with headers or status, Response instance, or WSGI callable, but it was a int.
