from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

template = """Question: {question}

Answer: Let's think step by step."""

prompt = ChatPromptTemplate.from_template(template)

model = OllamaLLM(model="llama3.1:8b", temperature=0.2)

chain = prompt | model

response = chain.invoke({"question": "What is LangChain?"})

print(response)

# from langchain_ollama import ChatOllama

# llm = ChatOllama(
#     model="llama3.1:8b",
#     temperature=0,
#     # other params...
# )

# messages = [
#     (
#         "system",
#         "You are a helpful assistant that translates English to French. Translate the user sentence.",
#     ),
#     ("human", "I love programming."),
# ]
# ai_msg = llm.invoke(messages)
# print(ai_msg)
