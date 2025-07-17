from flask import Flask, jsonify

try:
    from supabase_functions import add_book_record_using_isbn
except (ImportError, ModuleNotFoundError):
    from api.supabase_functions import add_book_record_using_isbn

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"message": "Hello from Flask on Vercel!"})


@app.route('/profile/<string:username>')
def profile(username):
    return f"{username}'s Page."


@app.route('/test')
def test():
    return "Test Page."


@app.route('/add_book_using_isbn/<isbn>')
def add_book_using_isbn(isbn):

    """Add a book using its ISBN."""

    book_record_response = add_book_record_using_isbn(isbn)
    if "error" in book_record_response:
        return jsonify({"error": book_record_response["error"]}), 400

    return book_record_response


if __name__ == '__main__':
    app.run(debug=True)

# TypeError: The view function did not return a valid response. The return type must be a string, dict, list,
#  tuple with headers or status, Response instance, or WSGI callable, but it was a int.
