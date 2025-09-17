# Import necessary libraries
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain import hub
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from supabase.client import Client, create_client
from langchain_core.tools import tool

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

# Initialize large language model (temperature = 0)
llm = ChatOpenAI(temperature=0)

# Fetch the prompt from the prompt hub
prompt = hub.pull("hwchase17/openai-functions-agent")

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


# Combine the tools and provide them to the LLM
tools = [retrieve]
agent = create_tool_calling_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Initialize chat history
chat_history = [SystemMessage(content=manual_prompt)]

# Start the chat session
print('Welcome to your Agentic RAG Chatbot!')

while True:

    # Take user query as input
    user_query = input("You: ")

    if user_query.lower() == 'exit':
        print("Goodbye!")
        break

    # Append user query to chat history
    chat_history.append(HumanMessage(content=user_query))

    # Construct the chat history part of the query
    chat_history_str = "\n".join([f"User: {msg.content}" if isinstance(msg, HumanMessage) else f"Bot: {msg.content}" for msg in chat_history])

    # Build the full query by combining manual prompt, chat history, and user query
    full_query = f"{chat_history_str}\nUser: {user_query}"

    # Invoke the agent with the full query including instructions and chat history
    response = agent_executor.invoke({"input": full_query})

    # Get AI response from the agent
    ai_message = response["output"]

    # Print AI's response
    print(f"Bot: 📚 {ai_message} 📚")

    # Append AI response to chat history
    chat_history.append(AIMessage(content=ai_message))

    # Optionally, you can save this history to a file for logging purposes:
    # with open("chat_history.txt", "a") as f:
    #     f.write(f"User: {user_query}\nBot: {ai_message}\n\n")
