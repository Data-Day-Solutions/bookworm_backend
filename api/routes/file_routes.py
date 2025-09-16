import os
import cv2
import werkzeug
import pdfplumber

from flask import request, jsonify
from flask import Blueprint

import pandas as pd
from tqdm import tqdm

import pytesseract

pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

try:
    from tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, check_session
except (ImportError, ModuleNotFoundError):
    from api.tools.supabase_functions import add_book_record_using_isbn, get_authenticated_client, add_record, check_session

try:
    from tools.image_recognition import detect_and_decode_barcode
except (ImportError, ModuleNotFoundError):
    from api.tools.image_recognition import detect_and_decode_barcode

file_bp = Blueprint("file", __name__)

# routes = []


# create route to load data from a provided csv file
@file_bp.route('/upload_isbn_csv', methods=['POST'])
def upload_isbn_csv():

    """Endpoint to upload a CSV file."""

    if check_session():

        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request.",
                            "data": None}), 400

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
                return jsonify({"message":
                                "CSV file must contain an 'ISBN' column.",
                                "data": None}), 400

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


@file_bp.route('/upload_image_for_isbn', methods=['POST'])
def upload_image_for_isbn():

    """Endpoint to upload an image file."""

    # TODO - check if the user is authenticated before allowing image upload
    # validate inputs - look into pydantic
    if check_session():

        # data = request.get_json()

        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request.", "data": None}), 400
        file = request.files['file']

        if file.filename == '':
            return jsonify({"message": "No selected file.", "data": None}), 400

        filename = werkzeug.utils.secure_filename(file.filename)
        upload_filename = os.path.join('api', 'uploads', filename)
        file.save(upload_filename)

        image = cv2.imread(upload_filename)
        barcodes = detect_and_decode_barcode(image)
        os.remove(upload_filename)

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


# add route to accept a pdf file upload and extract text using pdfplumber
@file_bp.route('/upload_pdf/<int:book_id>', methods=['POST'])
def upload_pdf():

    """Endpoint to upload a PDF file."""

    # TODO - add in user-flag to select between normal text extraction and OCR
    # normal text extraction is faster and more accurate if the PDF is machine readable
    # OCR is needed for scanned documents and images embedded in PDFs
    # But also - machine readable can have formatting issues (missing spaces, line breaks, etc) - which OCR can sometimes handle better
    # But this would take much longer to process
    # Maybe use a hybrid approach - try normal extraction first, if the text is below a certain threshold, then use OCR
    # How to check if spaces are being missed? - check for very long words?
    # Maybe use a heuristic - if the average word length is above a certain threshold, then use OCR
    # This might not be a common scenario though - most machine readable PDFs should be fine with normal extraction

    if check_session():

        if 'file' not in request.files:
            return jsonify({"message": "No file part in the request.", "data": None}), 400
        file = request.files['file']

        if file.filename == '':
            return jsonify({"message": "No selected file.", "data": None}), 400

        if file and werkzeug.utils.secure_filename(file.filename).endswith('.pdf'):
            filename = werkzeug.utils.secure_filename(file.filename)
            upload_filename = os.path.join('api', 'uploads', filename)
            file.save(upload_filename)

            # save file to table uploads - with user_id, filename, file_url, upload_date
            # TODO - add error handling for file save issues - duplicate filenames, etc.
            # TODO - add file size limit checks - both client side and server side
            # TODO - add file type checks - only allow pdfs
            authenticated_supabase_client = get_authenticated_client()

            with open(upload_filename, "rb") as f:
                response = (
                    authenticated_supabase_client.storage
                    .from_("uploads")
                    .upload(
                        file=f,
                        path=f"public/{filename}",
                        file_options={"cache-control": "3600", "upsert": "false"}
                    )
                )

            # if file is successfully uploaded, get the public url
            if response:
                file_url = authenticated_supabase_client.storage.from_("uploads").get_public_url(f"public/{filename}")

                # get book_id if available from the request
                # TODO - validate book_id exists in books table
                # TODO - handle case where book_id is not provided
                # Should only have one file record per book
                book_id = request.view_args['book_id']

                record = {
                    # "user_id": str(authenticated_supabase_client.auth.get_user().user.id),
                    "book_file": file_url,
                    "book_id": book_id
                }

            add_record(authenticated_supabase_client, "book_files", record)

            all_text = ""
            combined_text = ""

            with pdfplumber.open(upload_filename) as pdf:
                for page in tqdm(pdf.pages):

                    page_text = page.extract_text()
                    combined_text += page_text
                    all_text += page_text + "\n"

            if not combined_text:

                all_text = ""
                with pdfplumber.open(upload_filename) as pdf:

                    for page in tqdm(pdf.pages):

                        # Convert PDF page to an image
                        pil_image = page.to_image(resolution=300).original

                        # Use pytesseract to perform OCR on the image
                        text = pytesseract.image_to_string(pil_image)
                        all_text += text + "\n"

            # all_text = all_text.replace("\n", " ")
            all_text.replace("  ", " ")

            # print(all_text)

            os.remove(upload_filename)

            # TODO - add error handling for empty pdfs, etc.
            # TODO - in frontend, display the extracted text and allow user to confirm before adding to book record
            # TODO - add option to select specific pages to extract text from
            # TODO - Warn user is the accuracy may be low - recommend using a machine readable PDF or high quality scan

            response = jsonify({"message": "File uploaded and text extracted successfully.", "data": all_text}), 200
            return response
        else:
            return jsonify({"message": "Invalid file format. Only PDF files are allowed.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@file_bp.route('/add_text_to_book/<int:book_id>', methods=['POST'])
def add_text_to_book(book_id):

    """Add extracted text to a book record."""

    # TODO - give user option to provide text or pdf upload

    if check_session():

        # sending data from postman as form-data with key extracted_text and text value
        try:
            extracted_text = request.form.get('extracted_text')
        except AttributeError:
            extracted_text = ""

        # TODO - validate book_id exists
        # TODO - validate extracted_text is not empty
        # TODO - handle large text inputs - supabase has a limit of 1MB per field
        # TODO - consider storing large texts in a separate table or using a file storage service
        # TODO - provide feedback to user if text is too large to be added
        # TODO - consider text chunking for very large texts - Chapter-wise or section-wise storage
        # TODO - consider text summarization for very large texts to store a concise version
        # TODO - consider indexing the text for search functionality

        # check for pdf file upload
        if 'file' in request.files:

            file = request.files['file']
            if file and werkzeug.utils.secure_filename(file.filename).endswith('.pdf'):
                # get the extracted text from the pdf upload function                
                response = upload_pdf()
                extracted_text = response[0].json['data']
            else:
                if not extracted_text:
                    return jsonify({"message": "No text or file provided to add to the book.", "data": None}), 400

        # check byte size of extracted_text - must be less than 1MB
        # if len(extracted_text.encode('utf-8')) > 1_000_000:
        #     return jsonify({"message": "Extracted text is too large to be added to the book. Please provide text under 1MB.", "data": None}), 400

        authenticated_supabase_client = get_authenticated_client()

        # update the book record with the extracted text
        authenticated_supabase_client.table("books").update({"full_text": extracted_text}).eq("book_id", book_id).execute()

        # TODO - consider if text needs to be returned to user - this takes up bandwidth
        return jsonify({"message": "Text added to book record successfully.", "data": extracted_text}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# routes.append(dict(rule='/upload_isbn_csv', view_func=upload_isbn_csv, options=dict(methods=['POST'])))
# routes.append(dict(rule='/upload_image_for_isbn', view_func=upload_image_for_isbn, options=dict(methods=['POST'])))
# routes.append(dict(rule='/upload_pdf', view_func=upload_pdf, options=dict(methods=['POST'])))
# routes.append(dict(rule='/add_text_to_book/<int:book_id>', view_func=add_text_to_book, options=dict(methods=['POST'])))