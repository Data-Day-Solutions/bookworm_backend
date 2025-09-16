import os
from supabase import create_client, Client

try:
    from tools.supabase_functions import get_authenticated_client, create_new_supabase_user, check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import get_authenticated_client, create_new_supabase_user, check_session

from flask import request, jsonify, session, redirect, url_for
from flask import Blueprint

user_bp = Blueprint("user", __name__)

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# routes = []


@user_bp.route('/create_new_user', methods=['POST'])
def create_new_user():

    """Route to create users."""

    if check_session():

        data = request.get_json()

        email = data.get('email')
        password = data.get('password')

        # handle errors

        response = create_new_supabase_user(email, password)

        # TODO - Ensure that response is in standard format

        return jsonify(response), 200

    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@user_bp.route('/login', methods=['POST'])
def login():

    """Login route to authenticate users."""

    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    # handle errors
    res = supabase.auth.sign_in_with_password({'email': email, 'password': password})

    session['access_token'] = res.session.access_token
    session['refresh_token'] = res.session.refresh_token

    return jsonify({
        "message": "Login successful.",
        "data": None
    }), 200


@user_bp.route('/dashboard', methods=['GET'])
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


@user_bp.route('/logout', methods=['GET'])
def logout():

    """Logout route to clear session tokens."""

    if check_session():

        client = get_authenticated_client()
        client.auth.sign_out()

        session.pop('access_token', None)
        session.pop('refresh_token', None)

        return jsonify({
            "message": "Logout successful.",
            "data": None
        }), 200

    else:
        return jsonify({"message": "No active session.", "data": None}), 400


# routes.append(dict(rule='/create_new_user', view_func=create_new_user, options=dict(methods=['POST'])))
# routes.append(dict(rule='/login', view_func=login, options=dict(methods=['POST'])))
# routes.append(dict(rule='/dashboard', view_func=dashboard, options=dict(methods=['GET'])))
# routes.append(dict(rule='/logout', view_func=logout, options=dict(methods=['GET'])))
