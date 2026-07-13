# Assignment 2: Some Research Tools

The code in this folder initializes a chatbot which has some tools to help with research.

The code found in this folder was originally written as an assignment for the UofT DSI doctoral certificate program.

## Services

There are 3 services. The implementation is based on LangGraph's tools. 

The file main.py contains the llm model calls that controls the chat. Tools are in the files tools_*.py.

### Service 1: Look up a random paper (API Calls)

+ Can ask the chatbot to look a random paper on a topic from the [CORE dataset](https://core.ac.uk/services/dataset), a collection of scientific papers.
+ Performs a simple search on a topic using the [CORE API](https://api.core.ac.uk/docs/v3)
+ The basic implementation returns one random paper from the top 5 search results

### Service 2: Semantic Query

+ Not implemented yet

### Service 3: Query my personal Zotero collection (MCP server connection)

+ Set up a local Zotero MCP server based on docs [here](https://glama.ai/mcp/servers/awsl5714/zotero-mcp-server)
+ Uses a tunnel to connect to a local server
+ Makes queries about my personal Zotero collection
+ Unfortunately requires installation of a python package not in the original deploying-ai-env

`uv pip install pyzotero`

## User Interface

+ Added conversational style.
+ Implemented in Gradio

---

## Guardrails and Other Limitations

* Include guardrails that prevent users from:

  * Accessing or revealing the system prompt.
  * Modifying the system prompt directly.

* The model must not respond to questions on certain restricted topics:

  * Cats or dogs
  * Horoscopes or Zodiac Signs
  * Taylor Swift

## Implementation

+ Implement your code in the folder `./05_src/assignment_chat`.
+ Add a `readme.md` where you explain the nature of your chat client, the serivices that it provides, and any decisions that you made related to the implementation.
+ We will not be able to install more libraries to assess your work. Please use the standard setup of the course.

# Submission Information

**Please review our [Assignment Submission Guide](https://github.com/UofT-DSI/onboarding/blob/main/onboarding_documents/submissions.md)** for detailed instructions on how to format, branch, and submit your work. Following these guidelines is crucial for your submissions to be evaluated correctly.

## Submission Parameters

- The Submission Due Date is indicated in the [readme](../README.md#schedule) file.
- The branch name for your repo should be: assignment-1
- What to submit for this assignment:
    + This Jupyter Notebook (assignment_1.ipynb) should be populated and should be the only change in your pull request.
- What the pull request link should look like for this assignment: `https://github.com/<your_github_username>/deploying-ai/pull/<pr_id>`
    + Open a private window in your browser. Copy and paste the link to your pull request into the address bar. Make sure you can see your pull request properly. This helps the technical facilitator and learning support staff review your submission easily.

## Checklist

+ Created a branch with the correct naming convention.
+ Ensured that the repository is public.
+ Reviewed the PR description guidelines and adhered to them.
+ Verify that the link is accessible in a private browser window.

If you encounter any difficulties or have questions, please don't hesitate to reach out to our team via our Slack. Our Technical Facilitators and Learning Support staff are here to help you navigate any challenges.
