from flask import request, jsonify

try:
    from tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records, check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records, check_session

from flask import Blueprint

book_bp = Blueprint("book", __name__)


@book_bp.route('/add_book_using_isbn/<isbn>', methods=['GET'])
def add_book_using_isbn(isbn):

    """
    Add Book Using ISBN
    ---
    tags:
      - Books
    get:
      description: Add a book using its ISBN.
      parameters:
        - name: isbn
          in: path
          required: true
          schema:
            type: string
          description: The ISBN of the book
      responses:
        200:
          description: Book successfully added
    """

    if check_session():
        authenticated_supabase_client = get_authenticated_client()
        book_record_response = add_book_record_using_isbn(authenticated_supabase_client, isbn)
        return book_record_response, 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/create_new_library', methods=['POST'])
def create_new_library():

    """
    Create New Library
    ---
    tags:
      - Books
    post:
      description: Create new library for a user who is not assigned to one.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                library_name:
                  type: string
                  example: "My Library"
                library_colour:
                  type: string
                  example: "#FF5733"
                library_image_url:
                  type: string
                  example: "https://example.com/library.png"
      responses:
        200:
          description: Library successfully created
    """

    if check_session():
        authenticated_supabase_client = get_authenticated_client()
        user_id = str(authenticated_supabase_client.auth.get_user().user.id)

        user_libraries = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).execute()
        if user_libraries.data:
            return jsonify({"message": "User already has a library.", "data": None}), 403

        data = request.get_json()
        library_name = data.get('library_name')
        library_colour = data.get('library_colour')
        library_image_url = data.get('library_image_url')

        existing_libraries = authenticated_supabase_client.table("library_details").select("*").eq("library_name", library_name).execute()
        if existing_libraries.data:
            return jsonify({"message": "Library name already exists. Please choose an alternative.", "data": None}), 403

        record = {"library_name": library_name, "library_colour": library_colour, "library_image": library_image_url}
        add_record(authenticated_supabase_client, "library_details", record)

        new_library_id = authenticated_supabase_client.table("library_details").select("*").eq("library_name", library_name).execute().data[0]['library_id']
        existing_user_library = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).eq("library_id", new_library_id).execute()
        if not existing_user_library.data:
            authenticated_supabase_client.table("library_users").insert({
                "user_id": user_id,
                "library_id": new_library_id,
                "library_role": "admin"
            }).execute()

        return jsonify({"message": "Library creation successful. User assigned to library.", "data": record}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/get_user_library', methods=['GET'])
def get_user_library():

    """
    Get User Library
    ---
    tags:
      - Books
    get:
      description: Retrieve the current user's library
      responses:
        200:
          description: Successful response with library ID
    """

    if check_session():

        authenticated_supabase_client = get_authenticated_client()
        library_id = 0
        user_id = str(authenticated_supabase_client.auth.get_user().user.id)
        user_libraries = authenticated_supabase_client.table("library_users").select("*").eq("user_id", user_id).execute()

        if user_libraries.data:
            library_id = user_libraries.data[0]['library_id']
        else:
            return {"message": "User does not have an active library. Re-direct to library creation.", "data": None}

        return jsonify({"library_id": library_id, "data": None}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/get_all_user_books', methods=['GET'])
def get_all_user_books():

    """
    Get All User Books
    ---
    tags:
      - Books
    get:
      description: Retrieve all books belonging to the current user
      responses:
        200:
          description: List of user's books
    """

    if check_session():

        authenticated_supabase_client = get_authenticated_client()
        user_library_details = get_user_library()

        try:
            user_library_id = user_library_details[0].json['library_id']
        except KeyError:
            return jsonify({"message": "User does not have an any books in their library. Add now!", "data": None}), 403

        response = authenticated_supabase_client.table("user_library_books").select("* , books (*)").eq("library_id", user_library_id).execute()

        flattened_results = []
        for row in response.data:
            flat_row = row.copy()
            book_data = flat_row.pop("books", {})
            flat_row.update(book_data)
            flattened_results.append(flat_row)

        return jsonify({"books": flattened_results})
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/remove_book_from_library/<int:book_id>', methods=['DELETE'])
def remove_book_from_library(book_id):

    """
    Remove Book From Library
    ---
    tags:
      - Books
    delete:
      description: Remove a specific book from the user's library
      parameters:
        - name: book_id
          in: path
          required: true
          schema:
            type: integer
          description: The ID of the book to remove
      responses:
        200:
          description: Book successfully removed
    """

    if check_session():
        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_user_library()
            user_library_id = user_library_details[0].json['library_id']

            authenticated_supabase_client.table("user_library_books").delete().eq("book_id", book_id).eq("library_id", user_library_id).execute()
            return jsonify({"message": "Book removed from user's library.", "data": None}), 200
        except Exception as e:
            return jsonify({"message": "Error removing book from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/remove_all_books_from_library', methods=['DELETE'])
def remove_all_books_from_library():

    """
    Remove All Books From Library
    ---
    tags:
      - Books
    delete:
      description: Remove all books from the user's library
      responses:
        200:
          description: All books successfully removed
    """

    if check_session():
        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_user_library()
            user_library_id = user_library_details[0].json['library_id']

            authenticated_supabase_client.table("user_library_books").delete().eq("library_id", user_library_id).execute()

            return jsonify({"message": "All books removed from user's library.", "data": None}), 200
        except Exception as e:
            return jsonify({"message": "Error removing all books from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/get_all_books', methods=['GET'])
def get_all_books():

    """
    Get All Books
    ---
    tags:
      - Books
    get:
      description: Retrieve all books in the system
      responses:
        200:
          description: List of all books
    """

    if check_session():

        authenticated_supabase_client = get_authenticated_client()
        response = get_all_records(authenticated_supabase_client, "books")
        return jsonify({"books": response.data})

    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401
