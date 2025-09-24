# import basics
import os
from dotenv import load_dotenv

# import streamlit
import streamlit as st

# import langchain
from langchain_community.callbacks import get_openai_callback
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.tools import tool
from supabase.client import Client, create_client
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

# import supabase db
from supabase.client import Client, create_client

# load environment variables
load_dotenv()

# initiating supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# initiating embeddings model
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# initiating vector store
vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="content_map_documents",
    query_name="match_content_map_documents",
)


# initiating llm
llm = ChatOllama(model="llama3.1:8b", temperature=0)
# llm = ChatOllama(model="gpt-oss:20b", temperature=0)


# Create the tools
@tool(response_format="content_and_artifact")
def retrieve(query: str):

    """Retrieve information related to a query."""

    # retrieval
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.5},
    )

    docs = retriever.invoke(query)

    # Serialize the results to return
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in docs
    )

    return serialized, docs


def simplify_question(user_question: str) -> str:

    """
    Use the LLM to reduce the user question to a concise query suitable for retrieval.
    """

    simplification_prompt = f"""
    Simplify the following user question to a short search query.
    Keep the meaning, remove extra words, and focus on keywords:

    Question: {user_question}

    Short query:
    """

    simplified = llm.predict(simplification_prompt).strip()

    return simplified


initial_prompt = """
You are working as a primary school librarian in England. Please survey your database of books to find the best answer for the teacher asking you.
You should consider all available documents in your database when providing your response, and base your answer on the most relevant documents that match the query.
Be polite, concise, and informative. Only use information from the documents you find.
"""

prompt_template = """
Use the following retrieved documents to answer the user's question.

Retrieved documents:
{retrieved_docs}

Question: {question}

Answer:
"""

prompt = PromptTemplate(
    input_variables=["retrieved_docs", "question"],
    template=prompt_template
)


# --- Build a chain that first retrieves and then calls the LLM ---
def run_chain_with_retrieval(user_question: str, full_history: str):

    # determine if this is a YSSTC prompt - if it is then extract entities
    # use these to do a more targeted retrieval
    # possibly use to filter the retrieved docs
    # this could be done in a separate step before retrieval
    # if it is YSSTC then use content map and curriculum

    # simplify the prompt to get most relevant docs
    short_query = simplify_question(user_question)

    # Call the retrieval tool
    retrieved_docs = retrieve.invoke(short_query)

    # Build input for the LLM
    chain_input = {
        "retrieved_docs": retrieved_docs,
        "question": full_history
    }

    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run(chain_input)

    return response


def run_chatbot(user_query, full_query):

    with get_openai_callback() as cb:

        response = run_chain_with_retrieval(user_query, full_query)
        print(response)

        print("-----------------------------------")
        print(f"Total Tokens: {cb.total_tokens}")
        print(f"Prompt Tokens: {cb.prompt_tokens}")
        print(f"Completion Tokens: {cb.completion_tokens}")
        print(f"Total Cost (USD): ${cb.total_cost}")

    return response

# initiating streamlit app
st.set_page_config(page_title="Agentic RAG Chatbot", page_icon="🦜")
st.title("📚 Bookworm RAG Chatbot 📚")

# initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [SystemMessage(content=initial_prompt)]

# display chat messages from history on app rerun
for message in st.session_state.messages:

    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(message.content)


# create the bar where we can type messages
user_question = st.chat_input("How are you?")

# did the user submit a prompt?
if user_question:

    # add the message from the user (prompt) to the screen with streamlit
    with st.chat_message("user"):
        st.markdown(user_question)

        st.session_state.messages.append(HumanMessage(user_question))

    full_query = "\n".join([f"{msg.content}" for msg in st.session_state.messages])
    ai_message = run_chatbot(user_query=user_question, full_query=full_query)

    # adding the response from the llm to the screen (and chat)
    with st.chat_message("assistant"):
        st.markdown(ai_message)

        st.session_state.messages.append(AIMessage(ai_message))
