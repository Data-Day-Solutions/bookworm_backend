from langchain_openai import ChatOpenAI
from langchain_community.callbacks import get_openai_callback

from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(temperature=0)

with get_openai_callback() as cb:
    result = llm.invoke("Tell me a joke about librarians.")
    print(result)
    print("Tokens:", cb.total_tokens, cb.prompt_tokens, cb.completion_tokens, cb.total_cost)