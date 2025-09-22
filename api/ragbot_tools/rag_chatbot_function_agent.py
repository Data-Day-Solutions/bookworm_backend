# Import necessary libraries
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain import hub
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from supabase.client import Client, create_client
from langchain_core.tools import tool
from langchain_community.callbacks import get_openai_callback

from flask import session

# Load environment variables
load_dotenv()

# Initialize Supabase database
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Initialize vector store
vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)

llm = ChatOpenAI(temperature=0, streaming=False)

prompt = hub.pull("hwchase17/openai-functions-agent")

manual_prompt = """
You are working as a primary school librarian in England. Please survey your database of books to find the best answer for the teacher asking you.
You should consider all available documents in your database when providing your response, and base your answer on the most relevant documents that match the query.
Be polite, concise, and informative. Only use information from the documents you find.
"""


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


# Create the tools
@tool(response_format="content_and_artifact")
def retrieve(query: str):

    """Retrieve information related to a query."""

    # retrieval
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.2},
    )

    docs = retriever.invoke(query)

    # will look into passing filters based on user selection
    # Optionally filter based on metadata (e.g., only documents from recent years)
    # filtered_docs = [
    #     doc for doc in filtered_docs if doc.metadata.get("year", 0) > 2020
    # ]

    # Serialize the results to return
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\n" f"Content: {doc.page_content}")
        for doc in docs
    )

    return serialized, docs


# Combine the tools and provide them to the LLM
tools = [retrieve]
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def run_chatbot(user_query, testing_flag=False):

    try:
        _ = session['chat_history']
    except KeyError:
        session['chat_history'] = [serialize_message(SystemMessage(content=manual_prompt))]

    session['chat_history'].append(serialize_message(HumanMessage(content=user_query)))

    chat_history_msgs = [deserialize_message(m) for m in session["chat_history"]]

    full_query = "\n".join([f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"Bot: {msg.content}" for msg in chat_history_msgs])

    if testing_flag:
        with get_openai_callback() as cb:

            response = agent_executor.invoke({"input": full_query})
            print(cb)
    else:
        response = agent_executor.invoke({"input": full_query})

    ai_message = response["output"]

    session['chat_history'].append(serialize_message(AIMessage(content=ai_message)))

    return ai_message

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

        response = run_chatbot(user_query, testing_flag=True)

        print("AI Response:", response)
