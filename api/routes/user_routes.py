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


@user_bp.route('/change_password', methods=['POST'])
def change_password():

    """
    Change Password
    ---
    tags:
      - User Management
    summary: Change Password
    description: >
      This endpoint will allow the user to change their password.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              new_password:
                type: string
                example: "strongpassword123!"
    responses:
      200:
        description: Password changed.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Password changed."
                data:
                  type: object
                  nullable: true
      401:
        description: Unauthorized - user not authenticated
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: object
                  nullable: true
    """

    if check_session():

        # This checks that the user is logged in.
        # Ofc they won't be properly logged in, but we just need to verify they have a session.
        # This uses the session tokens to authenticate with supabase.
        # They are provided in the password reset email link session.

        # access_token = 'eyJhbGciOiJIUzI1NiIsImtpZCI6Ildwamt2Sm1adlkwRU9zRGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2lmbmJ1d3R5cHJpc29ycnZwd2ZsLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiN2U0YmY2MC03ODZkLTQ5MTktODExNC1jNmY0Y2E5OWQxZjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU4MTI0NDc0LCJpYXQiOjE3NTgxMjA4NzQsImVtYWlsIjoiZGF2aWRzaGF3MTk4NUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZGF2aWRzaGF3MTk4NUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiJiN2U0YmY2MC03ODZkLTQ5MTktODExNC1jNmY0Y2E5OWQxZjAifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJwYXNzd29yZCIsInRpbWVzdGFtcCI6MTc1ODEyMDg3NH1dLCJzZXNzaW9uX2lkIjoiYjBhMmYxNjMtZjk5Mi00ZGQzLWJiMmUtMTFhODNjYTczN2M4IiwiaXNfYW5vbnltb3VzIjpmYWxzZX0.O71n1S6Qkweffrtt3_siYc6wRl2rk5yfJ3QSRexm3LM'
        # access_token = 'eyJhbGciOiJIUzI1NiIsImtpZCI6Ildwamt2Sm1adlkwRU9zRGUiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2lmbmJ1d3R5cHJpc29ycnZwd2ZsLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJiN2U0YmY2MC03ODZkLTQ5MTktODExNC1jNmY0Y2E5OWQxZjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU4MTI0NTAyLCJpYXQiOjE3NTgxMjA5MDIsImVtYWlsIjoiZGF2aWRzaGF3MTk4NUBnbWFpbC5jb20iLCJwaG9uZSI6IiIsImFwcF9tZXRhZGF0YSI6eyJwcm92aWRlciI6ImVtYWlsIiwicHJvdmlkZXJzIjpbImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImVtYWlsIjoiZGF2aWRzaGF3MTk4NUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJzdWIiOiJiN2U0YmY2MC03ODZkLTQ5MTktODExNC1jNmY0Y2E5OWQxZjAifSwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJhYWwiOiJhYWwxIiwiYW1yIjpbeyJtZXRob2QiOiJvdHAiLCJ0aW1lc3RhbXAiOjE3NTgxMjA5MDJ9XSwic2Vzc2lvbl9pZCI6ImEyYjlmMGY2LTQyZWItNGVkMi04YjljLWRkYzdlMzRlNGUzZiIsImlzX2Fub255bW91cyI6ZmFsc2V9.CF4MsfQnmtV5Ac9zE2EXOGsm7mDLx_B44nqjVurc-4A'

        data = request.get_json()
        new_password = data.get('new_password')

        client = get_authenticated_client()
        user = client.auth.get_user()
        email = user.user.email

        supabase.auth.update_user({"id": email, "password": new_password})

        return jsonify({"message": "Password has been reset.", "data": None}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@user_bp.route('/send_password_request', methods=['POST'])
def send_password_request():

    """
    Send Password Reset Request
    ---
    tags:
      - User Management
    summary: Send Password Reset Request
    description: >
      This endpoint will send an email to the user. This can be used by users to change their password if forgotten.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                example: "user@example.com"
    responses:
      200:
        description: Password reset email sent.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Password reset email sent."
                data:
                  type: object
                  nullable: true
    """

    data = request.get_json()
    email = data.get('email')

    _ = supabase.auth.reset_password_for_email(email, {"redirect_to": "https://bookworm-it.co.uk"})

    return jsonify({"message": "Password reset email sent.", "data": None}), 200


@user_bp.route('/sign_up_user', methods=['POST'])
def sign_up_user():

    """
    Sign Up New User
    ---
    tags:
      - User Management
    summary: Sign Up New User
    description: >
      This endpoint will send an email confirmation to the user. This can be used by exisiting users to invite other users to the platform.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                example: "user@example.com"
              password:
                type: string
                example: "StrongPassword123!"
    responses:
      200:
        description: User created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User created successfully."
                data:
                  type: object
                  nullable: true
      401:
        description: User already exists.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User already exists."
                data:
                  type: object
                  nullable: true
    """

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    response = supabase.auth.sign_up(
        {
            "email": email,
            "password": password,
        }
    )

    if response.user.identities:
        return jsonify({"message": "User has been invited via email.", "data": None}), 200
    else:
        return jsonify({"message": "User already exists.", "data": None}), 400


@user_bp.route('/create_new_user', methods=['POST'])
def create_new_user():

    """
    Create New User
    ---
    tags:
      - User Management
    summary: Create a new user account
    description: >
      This endpoint allows authenticated users to create a new Supabase user account by providing an email and password.  
      Response will include a success message and any relevant data from Supabase.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                example: "user@example.com"
              password:
                type: string
                example: "StrongPassword123!"
    responses:
      200:
        description: User created successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User created successfully."
                data:
                  type: object
                  nullable: true
      401:
        description: Unauthorized - user not authenticated
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: object
                  nullable: true
    """

    if check_session():

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        response = create_new_supabase_user(email, password)

        return jsonify(response), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@user_bp.route('/login', methods=['POST'])
def login():

    """
    User Login
    ---
    tags:
      - User Management
    summary: Authenticate a user and create a session
    description: >
      Logs in a user using email and password. On success, stores `access_token` and `refresh_token` in session.
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                example: "user@example.com"
              password:
                type: string
                example: "StrongPassword123!"
    responses:
      200:
        description: Login successful
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Login successful."
                data:
                  type: object
                  nullable: true
    """

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    try:
        res = supabase.auth.sign_in_with_password({'email': email, 'password': password})
    except Exception as e:
        return jsonify({"message": "Login failed.", "data": str(e)}), 400

    session['access_token'] = res.session.access_token
    session['refresh_token'] = res.session.refresh_token

    return jsonify({"message": "Login successful.", "data": None}), 200


@user_bp.route('/dashboard', methods=['GET'])
def dashboard():

    """
    Dashboard Access
    ---
    tags:
      - User Management
    summary: Access the user dashboard
    description: >
      Returns a message indicating successful access to the dashboard for authenticated users.
      If not authenticated, redirects to the login page.
    responses:
      200:
        description: Dashboard accessed successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Dashboard re-direction successful."
                data:
                  type: object
                  nullable: true
      302:
        description: Redirect to login if not authenticated
    """

    client = get_authenticated_client()
    user = client.auth.get_user()

    if not user.user:
        return redirect(url_for('login'))

    return jsonify({"message": "Dashboard re-direction successful.", "data": None}), 200


@user_bp.route('/logout', methods=['GET'])
def logout():

    """
    Logout User
    ---
    tags:
      - User Management
    summary: Logout and clear session tokens
    description: >
      Logs out the authenticated user by clearing their session tokens and signing out from Supabase.
    responses:
      200:
        description: Logout successful
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Logout successful."
                data:
                  type: object
                  nullable: true
      400:
        description: No active session
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "No active session."
                data:
                  type: object
                  nullable: true
    """

    if check_session():

        client = get_authenticated_client()
        client.auth.sign_out()
        session.pop('access_token', None)
        session.pop('refresh_token', None)

        return jsonify({"message": "Logout successful.", "data": None}), 200
    else:
        return jsonify({"message": "No active session.", "data": None}), 400
