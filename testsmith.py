import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

client = Client()
print("Connected to LangSmith project:", os.getenv("LANGCHAIN_PROJECT"))
# Creates a tiny test run in your dashboard
client.create_run(
    name="Test Run",
    run_type="llm",
    inputs={"prompt": "Hello LangSmith"},
    outputs={"response": "World"}
)
print("Test run sent successfully!")