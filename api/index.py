from flask import Flask, jsonify
from supabase import create_client, Client

try:
    from functions import square
except (ImportError, ModuleNotFoundError):
    from api.functions import square

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


@app.route('/square_endpoint/<int:n>')
def square_endpoint(n):
    value = str(square(n))
    return value


if __name__ == '__main__':
    app.run(debug=True)

# TypeError: The view function did not return a valid response. The return type must be a string, dict, list,
#  tuple with headers or status, Response instance, or WSGI callable, but it was a int.
