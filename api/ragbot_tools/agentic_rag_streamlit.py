# import basics
import os
from dotenv import load_dotenv

# import streamlit
import streamlit as st

# import langchain
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain.agents import create_tool_calling_agent
from langchain import hub
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool

# import supabase db
from supabase.client import Client, create_client

# load environment variables
load_dotenv()

# initiating supabase
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# initiating embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# initiating vector store
vector_store = SupabaseVectorStore(
    embedding=embeddings,
    client=supabase,
    table_name="documents",
    query_name="match_documents",
)


# initiating llm
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# pulling prompt from hub
prompt = hub.pull("hwchase17/openai-functions-agent")

# TODO - create own prompt
# Define the manual instructions (context) for the user
manual_prompt = """
You are working as a primary school librarian in England. Please survey your database of books to find the best answer for the teacher asking you.
You should consider all available documents in your database when providing your response, and base your answer on the most relevant documents that match the query.
Be polite, concise, and informative. Only use information from the documents you find.
"""


# Create the tools
@tool(response_format="content_and_artifact")
def retrieve(query: str):

    """Retrieve information related to a query."""

    # Perform similarity search to retrieve top k documents
    # retrieved_docs = vector_store.similarity_search(query, k=5)

    # retrieval
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 5, "score_threshold": 0.2},
    )

    docs = retriever.invoke(query)
    # context = "".join(d.page_content for d in docs)

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


# combining all tools
tools = [retrieve]

# initiating the agent
agent = create_tool_calling_agent(llm, tools, prompt)

# create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# initiating streamlit app
st.set_page_config(page_title="Agentic RAG Chatbot", page_icon="🦜")
st.title("📚 Bookworm RAG Chatbot 📚")

# initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [SystemMessage(content=manual_prompt)]

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

    # invoking the agent
    result = agent_executor.invoke({"input": user_question, "chat_history": st.session_state.messages})

    ai_message = result["output"]

    # adding the response from the llm to the screen (and chat)
    with st.chat_message("assistant"):
        st.markdown(ai_message)

        st.session_state.messages.append(AIMessage(ai_message))
