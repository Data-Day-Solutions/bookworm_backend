# import basics
import os
import json
from tqdm import tqdm
from dotenv import load_dotenv

# import langchain
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

# import supabase
from supabase.client import Client, create_client
from supabase_functions import get_all_records

# load environment variables
load_dotenv()

# initiate supabase db
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

# initiate embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize Supabase client
supabase: Client = create_client(supabase_url=supabase_url,
                                 supabase_key=supabase_key)

# 1. Sign in user
email = "davidshaw1985@gmail.com"
password = "password123"

auth_response = supabase.auth.sign_in_with_password({
    "email": email,
    "password": password
})

# Check login success
if not auth_response.user:
    raise Exception("Authentication failed")

print("Logged in as:", auth_response.user.email)

columns = ["isbn", "title", "publisher", "year", "summary",
           "extended_summary", "full_text", "authors",
           "categories", "lexile_measure", "age_range"]

# Document(metadata={'producer': 'OpenOffice 4.1.13', 'creator': 'Writer', 'creationdate': '2025-08-31T15:05:10+01:00', 'author': 'Dave Shaw', 'source': 'C:\\Users\\david\\repos\\bookworm_backend\\api\\documents\\syfy.pdf', 'total_pages': 3, 'page': 0, 'page_label': '1'}, page_content='The Chrono-Confection Catastrophe - A Sci-fi Extravaganza by Dave Why-So-Shawrious\nProfessor Keyboard-Face was, by his own account, the cockiest man alive. With chiseled \ncheekbones, a jawline sharp enough to slice a lemon, and a forehead that glistened perpetually \nunder laboratory lights, he believed himself destiny’s favourite child. He also, inconveniently, had a \nkeyboard permanently fused into his face from a teleportation accident in the late 2030s. To him, \nthis was not a disfigurement, but an aesthetic improvement. “Makes me look avant-garde,” he \nwould say, striking a pose whenever a reflective surface came near.\nHis colleagues disagreed, though mostly in whispers. Chief among them were Remy LaLaptop, a \nwiry technician who had solder burns in the shape of continents across his hands, and Sarah \nCaruthers Of The Washington-MarsBar Caruthers’, whose aristocratic lineage stretched back to the \nfounders of the great Confectionery Dynasties that once ruled Earth’s sweet economy.\nThe three of them were stationed in Chrono-Bay 14, an unmarked facility beneath the Swiss Alps. \nTheir mission was simple: guard the prototype Chrono-Pod, a time-traveling capsule powered by \nmelted sherbet fountains and the occasional lightning storm.\nOn a Tuesday—time travel stories always begin on Tuesdays—Professor Keyboard-Face strode into\nthe control chamber in his shimmering silver coat.\n“Remy! Sarah! Prepare yourselves for history. Today, I travel to the twenty-seventh century to \nretrieve mankind’s greatest secret.”\nRemy groaned. “Which one? Fire? Gravity? The art of not monologuing every three minutes?”\nSarah arched an elegant eyebrow, a move she had perfected at finishing school. “Do tell us, \nProfessor. Which knowledge could possibly justify risking another reality fracture? The last one \ngave us the Eiffel Pyramid.”\n“Ah, but it’s beautiful!” Keyboard-Face countered. “Besides, the twenty-seventh century is home to \nthe Great Marshmallow Meringue Conclave. Legends say they hold the secret to eternal fluffiness.”\nRemy blinked. “Fluffiness?”\n“Yes, Remy,” the Professor said with exaggerated patience, “the eternal balance between density \nand buoyancy. Imagine soufflés that never collapse! Pillows that never flatten! Hair that never—” \nhe flicked his own gelled quiff— “goes limp.”\nBefore his companions could protest, he slammed a caramel-coated lever. The Chrono-Pod \nhummed, hissed, and swallowed him in a blaze of sherbet steam.\nWhen Keyboard-Face emerged, he was standing on a planet not unlike Earth—except it smelled \nperpetually of toasted sugar, and the sky shimmered pink. Towering before him were beings of \nunimaginable size: aliens shaped like colossal meringues, their glossy peaks stretching into the \nclouds. Their bodies were marshmallow white, soft yet imposing, and their voices rumbled like \nrolling thunder.\n“WHO APPROACHES THE MERINGUE COUNCIL?” boomed the largest of them, who wore a \ncrown of crystallized sugar.\n“I am Professor Keyboard-Face!” the Professor announced, puffing his chest. “Cocky, handsome, \nand very slightly sticky from the journey. I come to learn your secrets of eternal fluff.”\nThe aliens exchanged glances—or what passed for glances, as their eyes were small blueberries \nembedded in pillowy faces. Finally, one spoke.\n“YOUR KIND ARE IMPATIENT. TIME IS OUR INGREDIENT. WE BAKE IN CENTURIES.”\nKeyboard-Face winked. “Darling, centuries are my playground. I invented impatience.”')
book_data = get_all_records(supabase, "books", columns=columns)

# combine summaries and extended summaries into summary
for book in book_data.data:
    if book['extended_summary']:
        book['summary'] = (book['summary'] or '') + "\n\n" + book['extended_summary']

columns.remove('extended_summary')
columns.remove('full_text')
# columns.remove('summary')

# consider having a single record which contains all book summaries?
# or just each book's summary as full text
# rather than repeating the summary in each chunk
# doesn't help with retrieval if the summary is in every chunk?

documents = []

# TODO - create map to hold metadata based on columns

# do for each book in book_data
for book in book_data.data:

    # create artificial pages based on full_text length
    book['page'] = 1

    if book['full_text'] == "Full text goes here.":
        book['full_text'] = book['summary']
    else:
        book['full_text'] = book['full_text'] + '\n' + book['summary']

    # split book into chunks of 2000 characters - based on full_text
    for i in range(0, len(book['full_text']), 2000):

        chunk = book['full_text'][i:i + 2000]

        # create metadata dictionary based on columns
        metadata = {col: book[col] for col in columns if col in book}
        metadata['page'] = book['page']

        # include metadata in each chunk
        # convert metadata to string - is there value to adding metadata into chunks?
        # it is retrieved by similarity doc retreival and inserted into prompt
        # also - can add in manual metadata filtering at search time - based on user input
        # chunk = json.dumps(metadata) + '\n\nText:\n' + chunk

        doc = Document(page_content=chunk, metadata=metadata)
        documents.append(doc)
        book['page'] += 1

    # print(f"Processing book: {book['title']}")

# TODO - only add new books

# test_documents = documents[:200]  # limit to first 5 for testing

# # add document which corresponds to book['title'] == 'Romeo and Juliet'
# for doc in documents:
#     if doc.metadata['title'] == 'Romeo and Juliet':
#         test_documents.append(doc)

# documents = test_documents
# docs = test_documents
print(f"Total documents to process: {len(documents)}")

# text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
# docs = text_splitter.split_documents(documents)


# split up documents list to add
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


doc_chunks = chunks(documents, 10)

for doc_chunk in tqdm(doc_chunks):

    # store chunks in vector store
    # verbose output to see progress
    vector_store = SupabaseVectorStore.from_documents(
        doc_chunk,
        embeddings,
        client=supabase,
        table_name="documents",
        query_name="match_documents",
        chunk_size=2000,
    )
