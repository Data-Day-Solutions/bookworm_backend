import os
from dotenv import load_dotenv

from langchain_community.callbacks import get_openai_callback
from langchain_core.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.tools import tool
from supabase.client import Client, create_client
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings

from flask import session

load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

embeddings = OllamaEmbeddings(model="mxbai-embed-large")

vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)

llm = ChatOllama(model="llama3.1:8b", temperature=0)


def serialize_message(msg):
    return {"type": msg.__class__.__name__, "content": msg.content}


def deserialize_message(d):
    if d["type"] == "SystemMessage":
        return SystemMessage(content=d["content"])
    elif d["type"] == "HumanMessage":
        return HumanMessage(content=d["content"])
    elif d["type"] == "AIMessage":
        return AIMessage(content=d["content"])
    else:
        raise ValueError(f"Unknown message type: {d['type']}")


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


@tool(response_format="content_and_artifact")
def retrieve(query: str):

    """Retrieve information related to a query."""

    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.01},
    )

    docs = retriever.invoke(query)
    serialized = "\n\n".join(f"Source: {doc.metadata}\nContent: {doc.page_content}" for doc in docs)

    return serialized, docs


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


def run_chatbot(user_query):

    try:
        _ = session['chat_history']
    except KeyError:
        session['chat_history'] = [serialize_message(SystemMessage(content=initial_prompt))]

    session['chat_history'].append(serialize_message(HumanMessage(content=user_query)))

    chat_history_msgs = [deserialize_message(m) for m in session["chat_history"]]

    full_query = "\n".join([f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"Bot: {msg.content}" for msg in chat_history_msgs])

    with get_openai_callback() as cb:

        response = run_chain_with_retrieval(user_query, full_query)
        print(response)

        print("-----------------------------------")
        print(f"Total Tokens: {cb.total_tokens}")
        print(f"Prompt Tokens: {cb.prompt_tokens}")
        print(f"Completion Tokens: {cb.completion_tokens}")
        print(f"Total Cost (USD): ${cb.total_cost}")

    session['chat_history'].append(serialize_message(AIMessage(content=response)))

    return response

    # Save user's chat history to Supabase? Seems like overkill and will dramatically increase token usage
    # Optionally, you can save this history to a file for logging purposes:
    # with open("chat_history.txt", "a") as f:
    #     f.write(f"User: {user_query}\nBot: {ai_message}\n\n")


if __name__ == "__main__":

    session = {}

    while True:

        user_query = input("You: ")

        if user_query.lower() == 'exit':
            print("Goodbye!")
            break

        response = run_chatbot(user_query)

        print("Bot:", response)
