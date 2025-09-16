from flask import request, jsonify

try:
    from tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records, check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, get_all_records, check_session

from flask import Blueprint

book_bp = Blueprint("book", __name__)

# routes = []


@book_bp.route('/add_book_using_isbn/<isbn>', methods=['GET'])
def add_book_using_isbn(isbn):

    # """
    # Add Book Using ISBN Endpoint
    # ---
    # get:
    # description: Add a book using its ISBN.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

        authenticated_supabase_client = get_authenticated_client()

        book_record_response = add_book_record_using_isbn(authenticated_supabase_client, isbn)

        return book_record_response, 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/create_new_library', methods=['POST'])
def create_new_library():

    # """
    # Create New Library Endpoint
    # ---
    # post:
    # description: Create new library for users who are not assigned to one.
    # requestBody:
    #     required: true
    #     content:
    #     application/json:
    #         schema:
    #         type: object
    #         properties:
    #             example_field:
    #             type: string
    #             example: "example value"
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

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


@book_bp.route('/get_user_library', methods=['GET'])
def get_user_library():

    # """
    # Get User Library Endpoint
    # ---
    # get:
    # description: Finds the library for the user.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

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


@book_bp.route('/get_all_user_books', methods=['GET'])
def get_all_user_books():

    # """
    # Get All User Books Endpoint
    # ---
    # get:
    # description: Retrieve all books for the authenticated user.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

        authenticated_supabase_client = get_authenticated_client()

        user_library_details = get_user_library()
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


@book_bp.route('/remove_book_from_library/<int:book_id>', methods=['GET', 'DELETE'])
def remove_book_from_library(book_id):

    # """
    # Remove Book Endpoint
    # ---
    # get:
    # description: Remove a book from the user's library.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_user_library()
            user_library_id = user_library_details[0].json['library_id']

            # delete the book from the user's library
            authenticated_supabase_client.table("user_library_books").delete().eq("book_id", book_id).eq("library_id", user_library_id).execute()
            return jsonify({"message": "Book removed from user's library.", "data": None}), 200

        except Exception as e:
            return jsonify({"message": "Error removing book from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/remove_all_books_from_library', methods=['GET', 'DELETE'])
def remove_all_books_from_library():

    # """
    # Remove All Books Endpoint
    # ---
    # get:
    # description: Remove all books from the user's library.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response

    put:
    description: Placeholder PUT endpoint
    responses:
        200:
        description: Successful PUT response

    delete:
    description: Placeholder DELETE endpoint
    responses:
        204:
        description: Successful DELETE response
    """

    if check_session():

        try:
            authenticated_supabase_client = get_authenticated_client()
            user_library_details = get_user_library()
            user_library_id = user_library_details[0].json['library_id']

            # delete all books from the user's library
            authenticated_supabase_client.table("user_library_books").delete().eq("library_id", user_library_id).execute()
            return jsonify({"message": "All books removed from user's library.", "data": None}), 200

        except Exception as e:
            return jsonify({"message": "Error removing all books from library.", "error": str(e), "data": None}), 500
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@book_bp.route('/get_all_books', methods=['GET'])
def get_all_books():

    # """
    # Get All Books Endpoint
    # ---
    # get:
    # description: Retrieve all books.
    # responses:
    #     200:
    #     description: Successful response
    # """

    """
    Placeholder endpoint
    ---
    get:
    description: Placeholder GET endpoint
    responses:
        200:
        description: Successful GET response

    post:
    description: Placeholder POST endpoint
    requestBody:
        required: false
        content:
        application/json:
            schema:
            type: object
            properties:
                example_field:
                type: string
                example: "test value"
    responses:
        200:
        description: Successful POST response
    """


    if check_session():

        authenticated_supabase_client = get_authenticated_client()
        response = get_all_records(authenticated_supabase_client, "books")

        jsonified_books = jsonify({"books": response.data})

        return jsonified_books
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# routes.append(dict(rule='/add_book_using_isbn/<isbn>',
#                    view_func=add_book_using_isbn,
#                    options=dict(methods=['GET'])))
# routes.append(dict(rule='/create_new_library',
#                    view_func=create_new_library,
#                    options=dict(methods=['POST'])))
# routes.append(dict(rule='/get_user_library',
#                    view_func=get_user_library, options=dict(methods=['GET'])))
# routes.append(dict(rule='/get_all_user_books',
#                    view_func=get_all_user_books,
#                    options=dict(methods=['GET'])))
# routes.append(dict(rule='/remove_book_from_library/<int:book_id>',
#                    view_func=remove_book_from_library,
#                    options=dict(methods=['GET', 'DELETE'])))
# routes.append(dict(rule='/remove_all_books_from_library',
#                    view_func=remove_all_books_from_library,
#                    options=dict(methods=['GET', 'DELETE'])))
# routes.append(dict(rule='/get_all_books', view_func=get_all_books,
#                    options=dict(methods=['GET'])))

# TODO - add a route to invite another user to an existing library
# check that the user is authenticated
# check that the user is an admin of the library
# send an email to the invited user with a link to accept the invitation
# or just add the user to the library_users table - they do need to have an account already
# check and inform admin if the user has not fully registered yet
# add the invited user to the library_users table

# Ensure that no profanity or inappropriate library names are used - use a profanity filter
# This also applies to book reviews and comments in the future
# This also applies to book text which has been extracted using OCR or other means