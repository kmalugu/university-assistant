from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser



# Initialize LLM
llm = ChatOllama(
    model='mistral',
    temperature=0
)

# Prompt Template
prompt = ChatPromptTemplate.from_messages([
    ("system" , "You are a helpful university assistant."),
    ("user" , "{input}")
])

# Output parser
parser = StrOutputParser()

# LCEL Chain (RunnableSequence)
chain = prompt | llm | parser