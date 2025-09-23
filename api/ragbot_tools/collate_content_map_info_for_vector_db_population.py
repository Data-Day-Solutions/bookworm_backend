# import basics
import os
import re
from dotenv import load_dotenv

# import langchain
from langchain_community.document_loaders import PyPDFDirectoryLoader, PyPDFLoader
from langchain_community.document_loaders import TextLoader, UnstructuredWordDocumentLoader
from langchain_community.document_loaders import DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings

# import supabase
from supabase.client import Client, create_client

# load environment variables
load_dotenv()

# initiate supabase db
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# initiate embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

path = os.path.join(os.getcwd(), "api//school_content_maps_docs")

# Create loaders for each file type
txt_loader = DirectoryLoader(path=path, glob="*.txt", loader_cls=lambda path: TextLoader(path, encoding="utf-8", errors="ignore"))
pdf_loader = DirectoryLoader(path=path, glob="*.pdf", loader_cls=PyPDFLoader)
docx_loader = DirectoryLoader(path=path, glob="*.docx", loader_cls=UnstructuredWordDocumentLoader)

docs = []
docs.extend(txt_loader.load())
docs.extend(pdf_loader.load())
docs.extend(docx_loader.load())

print(f"Loaded {len(docs)} documents")

subjects = ['English', 'Maths', 'Science', 'Art' 'Computing',
            'Design & Technology', 'Geography', 'History',
            'Music', 'Physical Education', 'Religious Education', 'PSHE']

year_designations = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5',
                     'Year 6', 'EYFS', 'Y1', 'Y2', 'Y3', 'Y4', 'Y5', 'Y6']

# add more properties to the metadata for each document - year, subject, topic - from the filename
# use filename conventions like 'Year 1 - Maths - Addition and Subtraction.txt'
# to extract the metadata
# could use more sophisticated methods like NLP to extract this information from the content of the document
# but for now, we'll use the filename conventions
for doc in docs:

    filename = os.path.basename(doc.metadata["source"])

    # find year in filename - use year_designations list
    year = None
    for yd in year_designations:
        if re.search(rf"\b{re.escape(yd)}\b", filename, re.IGNORECASE):
            year = yd
            break

    # find subject in filename - use subjects list
    subject = None
    for sub in subjects:
        if re.search(rf"\b{re.escape(sub)}\b", filename, re.IGNORECASE):
            subject = sub
            break

    # use everything else in the filename as the topic
    topic = filename
    if year:
        topic = re.sub(rf"\b{re.escape(year)}\b", "", topic, flags=re.IGNORECASE)
    if subject:
        topic = re.sub(rf"\b{re.escape(subject)}\b", "", topic, flags=re.IGNORECASE)

    topic = re.sub(r"[-_]", " ", topic)  # replace - and _ with space
    topic = re.sub(r"\s+", " ", topic)  # replace multiple spaces with single space
    topic = re.sub(r"\.txt$|\.pdf$|\.docx$", "", topic, flags=re.IGNORECASE)  # remove file extension

    # remove standard terms like 'curriculum', 'content', 'map', 'scheme of work'
    topic = re.sub(r"\b(curriculum|content|map|scheme of work|plan|overview|syllabus|mtp)\b", "", topic, flags=re.IGNORECASE)
    topic = topic.strip()
    if topic == "":
        topic = "Unknown"

    doc.metadata["year"] = year
    doc.metadata["subject"] = subject
    doc.metadata["topic"] = topic

    print(f"Processed document: {filename}, Metadata: {doc.metadata}")

# split the documents in multiple chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = text_splitter.split_documents(docs)

# store chunks in vector store
vector_store = SupabaseVectorStore.from_documents(
    docs,
    embeddings,
    client=supabase,
    table_name="content_map_documents",
    query_name="match_content_map_documents",
    chunk_size=1000,
)
