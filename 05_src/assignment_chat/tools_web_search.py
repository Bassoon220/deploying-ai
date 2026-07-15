from langchain.tools import tool
import os
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".secrets")

@tool
def simple_web_search(user_query):
    """
    Performs a simple web search using the OpenAI Responses API

    First creates an OpenAI client, using private API key

    The performs a simple web search using a defined user query

    Then prints and returns the result

    Based on example code from OpenAI here:
    https://developers.openai.com/api/docs/guides/tools-web-search?lang=python
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.responses.create(
        model="gpt-5.4-mini",
        tools=[{"type": "web_search"}],
        input=user_query
    )

    print("\n--- User Query ---")
    print(user_query)
    print("-------------------------------\n")

    print("\n--- Web Search Result ---")
    print(response.output_text)
    print("-------------------------------\n")

    return (response.output_text)

    