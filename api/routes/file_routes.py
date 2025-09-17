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


@file_bp.route('/upload_isbn_csv', methods=['POST'])
def upload_isbn_csv():

    """
    Upload ISBN CSV
    ---
    tags:
      - File Uploads
    summary: Upload a CSV containing ISBN numbers.
    description: >
      Accepts a CSV file containing ISBN numbers.  
      Each ISBN is processed and added to the database via Supabase.  

      **Requirements:**
      - The CSV must contain a column named `ISBN`.
      - Only `.csv` files are accepted.

      **Notes:**
      - Duplicate or invalid ISBNs may be skipped.
      - Error handling for missing or invalid ISBNs is not yet implemented.
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
                description: CSV file containing a column named `ISBN`.
    responses:
      200:
        description: File processed successfully and books added.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "File uploaded successfully. Books added."
                data:
                  type: string
                  nullable: true
      400:
        description: Invalid request (e.g., no file provided, wrong format, or missing ISBN column).
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "CSV file must contain an 'ISBN' column."
                data:
                  type: string
                  nullable: true
      401:
        description: Unauthorized - user not authenticated.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: string
                  nullable: true
    """

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

            if 'ISBN' not in isbn_df.columns:
                return jsonify({"message": "CSV file must contain an 'ISBN' column.",
                                "data": None}), 400

            # Extract ISBNs and clean them
            isbn_list = isbn_df['ISBN'].tolist()
            isbn_list = [str(isbn).strip() for isbn in isbn_list if pd.notna(isbn)]

            for isbn in tqdm(isbn_list):
                authenticated_supabase_client = get_authenticated_client()
                add_book_record_using_isbn(authenticated_supabase_client, isbn)

            os.remove(upload_filename)

            return jsonify({"message": "File uploaded successfully. Books added.", "data": None}), 200
        else:
            return jsonify({"message": "Invalid file format. Only CSV files are allowed.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@file_bp.route('/upload_image_for_isbn', methods=['POST'])
def upload_image_for_isbn():

    """
    Upload Image for ISBN
    ---
    tags:
      - File Uploads
    summary: Upload an image to detect an ISBN barcode.
    description: >
      Accepts an image file, scans it for barcodes, and extracts a possible ISBN number.  
      If an ISBN is detected, it is used to create a new book record in the database.  

      **Notes:**
      - Currently, only the first detected barcode is used.
      - Only image files are accepted.
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
                description: An image file containing an ISBN barcode.
    responses:
      200:
        description: Book record created successfully from detected ISBN.
        content:
          application/json:
            schema:
              type: object
              properties:
                book_id:
                  type: integer
                  example: 123
                title:
                  type: string
                  example: "The Hobbit"
                isbn:
                  type: string
                  example: "9780547928227"
      400:
        description: No barcode detected or invalid file format.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "No barcode detected in the image."
                data:
                  type: string
                  nullable: true
      401:
        description: Unauthorized - user not authenticated.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: string
                  nullable: true
    """

    if check_session():
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

        try:
            # Use the first detected barcode (assumed ISBN)
            isbn_number = barcodes[0]

            authenticated_supabase_client = get_authenticated_client()
            book_record = add_book_record_using_isbn(authenticated_supabase_client, isbn_number)

            return jsonify(book_record), 200

        except IndexError:
            return jsonify({"message": "No barcode detected in the image.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# add route to accept a pdf file upload and extract text using pdfplumber
@file_bp.route('/upload_pdf/<int:book_id>', methods=['POST'])
def upload_pdf(book_id):

    """
    Upload PDF for a Book and Extract Text
    ---
    tags:
      - File Uploads
    summary: Upload a PDF file for a book and extract text
    description: >
      This endpoint allows users to upload a PDF file for a specific book.  
      It will attempt to extract text using **pdfplumber**.  
      If extraction fails (e.g., scanned PDFs), the system will fall back to OCR using Tesseract.  

      **Notes:**
      - Only PDF files are accepted.
      - A valid `book_id` must be supplied in the URL.
      - Extracted text may require manual cleanup for formatting issues.
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: The ID of the book the PDF should be associated with.
    requestBody:
      required: true
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              file:
                type: string
                format: binary
                description: PDF file to upload and process.
    responses:
      200:
        description: PDF uploaded and text extracted successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "File uploaded and text extracted successfully."
                data:
                  type: string
                  example: "Once upon a time, in a hole in the ground there lived a hobbit..."
      400:
        description: Invalid file format or processing error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Invalid file format. Only PDF files are allowed."
                data:
                  type: string
                  nullable: true
      401:
        description: Unauthorized - user not authenticated.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: string
                  nullable: true
    """

    # TODO - add in user-flag to select between normal text extraction and OCR
    # normal text extraction is faster and more accurate if the PDF is machine readable
    # OCR is needed for scanned documents and images embedded in PDFs
    # But also - machine readable can have formatting issues (missing spaces, line breaks, etc) - which OCR can sometimes handle better
    # Maybe use a hybrid approach - try normal extraction first, if the text is below a certain threshold, then use OCR

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

            if response:
                file_url = authenticated_supabase_client.storage.from_("uploads").get_public_url(f"public/{filename}")

                record = {
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
                        pil_image = page.to_image(resolution=300).original
                        text = pytesseract.image_to_string(pil_image)
                        all_text += text + "\n"

            all_text.replace("  ", " ")

            os.remove(upload_filename)

            return jsonify({
                "message": "File uploaded and text extracted successfully.",
                "data": all_text
            }), 200
        else:
            return jsonify({"message": "Invalid file format. Only PDF files are allowed.", "data": None}), 400
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


@file_bp.route('/add_text_to_book/<int:book_id>', methods=['POST'])
def add_text_to_book(book_id):

    """
    Add Extracted Text to Book Record
    ---
    tags:
      - Book Management
    summary: Add text content to a specific book
    description: >
      This endpoint allows authenticated users to add text to a book record.
      Users can either provide raw text via `extracted_text` form-data or upload a PDF file, which will be processed and extracted.  

      **Notes:**
      - Only PDF files are supported for file uploads.  
      - Extracted text is stored in the `full_text` field of the book record.  
      - Large text inputs may need chunking due to database size limits.
    parameters:
      - in: path
        name: book_id
        required: true
        schema:
          type: integer
        description: The ID of the book to update.
    requestBody:
      required: false
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              extracted_text:
                type: string
                description: Raw text to add to the book record.
              file:
                type: string
                format: binary
                description: PDF file to extract text from.
    responses:
      200:
        description: Text added successfully to the book record.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Text added to book record successfully."
                data:
                  type: string
                  description: The text that was added to the book record.
                  example: "Once upon a time..."
      400:
        description: Invalid input or missing text/file.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "No text or file provided to add to the book."
                data:
                  type: string
                  nullable: true
      401:
        description: Unauthorized - user not authenticated.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "User not authenticated."
                data:
                  type: string
                  nullable: true
    """

    if check_session():

        try:
            extracted_text = request.form.get('extracted_text')
        except AttributeError:
            extracted_text = ""

        # check for PDF file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and werkzeug.utils.secure_filename(file.filename).endswith('.pdf'):
                # extract text from uploaded PDF
                response = upload_pdf(book_id)
                extracted_text = response[0].json['data']
            else:
                if not extracted_text:
                    return jsonify({"message": "No text or file provided to add to the book.", "data": None}), 400

        authenticated_supabase_client = get_authenticated_client()

        # update the book record with the extracted text
        authenticated_supabase_client.table("books").update({"full_text": extracted_text}).eq("book_id", book_id).execute()

        return jsonify({"message": "Text added to book record successfully.", "data": extracted_text}), 200
    else:
        return jsonify({"message": "User not authenticated.", "data": None}), 401


# routes.append(dict(rule='/upload_isbn_csv', view_func=upload_isbn_csv, options=dict(methods=['POST'])))