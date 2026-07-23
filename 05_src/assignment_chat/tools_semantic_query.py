from pypdf import PdfReader
from IPython.display import display, Markdown
from langchain_text_splitters  import RecursiveCharacterTextSplitter
import os
import torch
from sentence_transformers import SentenceTransformer, util
import chromadb
from openai import OpenAI
from langchain.tools import tool

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".secrets")

USE_GATEWAY = (os.getenv('USE_GATEWAY', 'FALSE').upper() == 'TRUE')

def get_client(use_gateway: bool = USE_GATEWAY) -> OpenAI:
    if use_gateway:
        client = OpenAI(base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
                    api_key='any value',
                    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')})
    else:
        client = OpenAI()
    return client

def read_keeler(filelocation, n_chapters=9):
    """
    Reads a set of pdf files, extract their text into one big string

    The function in this case is written to read the 9 chapters in James Keeler's textbook Understanding NMR Spectroscopy
    """
    keeler = ""
    for i in range(n_chapters):
        chapter = i + 1
        filename = f"{filelocation}/chapter_{chapter}.pdf"
        reader = PdfReader(filename)
        num_pages = len(reader.pages)

        chapter = ""
        for j in range(num_pages):
            page = reader.pages[j]
            text = page.extract_text()

            keeler += "\n" + text
    print("done")
    return keeler


def split_pdf_text(text):
    """
    Splits text using Recursice CharacterTextSplitter
    """
    # split the entire read text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2800, # chunks of roughly 2800 tokens in length
        chunk_overlap=700, # chunks will overlap a bit, will allow you to see things that would have otherwise been split
        # not necessary if youre doing a semantic split, like for abstract / introduction. those are meant to be separate
        separators=["\n\n", "\n"],
        length_function = len, # specify length function to calculate how many tokens there are (just going by characters)
        add_start_index = True
    )
    chunks = text_splitter.split_text(text)
    print(f'Split text length {len(text)} into {len(chunks)} chunks.' )
    return chunks

def create_embeddings(chunks):
    """
    Create embeddings using pre-split chunks of text
    """
    # create embeddings
    client = get_client()
    MODEL = os.getenv('MODEL', 'gpt-4o-mini')
    response = client.embeddings.create(
        input = chunks, 
        model = "text-embedding-3-small"
    )
    return response

def create_chroma_client_and_collection(client_path="../chroma_client_assignment_chat"):
    # instantiate a persistent chromadb client
    chroma_client = chromadb.PersistentClient(path=client_path)

    # create a collection, or if it exists already, then just get it
    try:
        # if the collection doesn't exist, then create it and put in data

        # first try to create the collection
        # if it already exists, then there will be an error, and the except block below will be executed instead
        # which just directly gets the collection
        collection = chroma_client.create_collection(name = "keeler")

        # Now assuming that the collection doesn't exist, we need to create it.
        # first read data. this should read a bunch of pdf files
        # and extract their text into one string
        keeler = read_keeler("../Keeler_Understanding_NMR_Spectroscopy")

        # split text into chunks, to create better embeddings
        chunks = split_pdf_text(keeler)

        # actually create the embeddings, returned in one object
        response = create_embeddings(chunks)

        # create a list for the embeddings for each chunk
        # also create a list of ids. just number the chunks
        embeddings = [item.embedding for item in response.data]
        ids = [f"id{i}" for i in range(len(chunks))]

        # add each chunk to the collection
        # add the chunk itself, the embeddings, and an id
        collection.add(embeddings = embeddings, 
                    documents = chunks, 
                    ids = ids)

    except:
        # if the collection already exists, then just get it
        # for the deploying AI assignment 2, the collection is named "keeler"
        # because we're reading something specific
        collection = chroma_client.get_collection(name="keeler")

    return collection


def get_embedding(text, model="text-embedding-3-small"):
    """
    Gets the embedding for the user query, or any text
    """
    text = text.replace("\n", " ")

    client = get_client()

    return client.embeddings.create(input=[text], model=model).data[0].embedding


def query_chromadb(query:str, collection, top_n:int):
    """
    Performs the semantic search of a user query on a chromadb collection

    First gets embeddings for the user query
    
    Then, tries to get a chromadb collection. see if it already exists in files.
    The client was previously created during test runs, so for further queries, 
    we shouldn't need to recreate the collection, reread data, create embeddings, etc.

    Then gets the results of the query, specifying the top_n results

    Outputs the results in a list of 3-tuples containing the id, similarity score, and text for each fragment
    """
    # get embedding of user query
    query_embedding = get_embedding(query)

    collection = create_chroma_client_and_collection(client_path="../chroma_client_assignment_chat")

    results = collection.query(query_embeddings = [query_embedding], n_results = top_n)
    return [(id, score, text) for id, score, text in zip(results['ids'][0], results['distances'][0], results['documents'][0])]


def generate_prompt(query:str, collection:chromadb.api.models.Collection, top_n:int):
    """
    Queries a chromadb collection for semantic similarity to a user query
    
    Then, embellish the response, turn it into a prompt to give to an llm
    """

    context_data = query_chromadb(query, collection, top_n=top_n)
    prompt = f"Given a query, provide a detailed response using the context from relevant excerpts of James Keeler's book Understanding NMR Spectroscopy.\n\n"
    prompt += f"<query>{query}</query>\n\n"
    prompt += "<context>\n"
    for k, context in enumerate(context_data):
        prompt += f"excerpt id: {context[0]}\n"
        prompt += f"excerpt cosine similarity to query: {context[1]}\n"
        prompt += f"excerpt: {context[2]}\n"
    prompt += "</context>\n\n"
    prompt += "\nBased on the context and nothing else, provide a detailed response to the query."
    return prompt

@tool
def generate_response(query:str, collection:chromadb.api.models.Collection, top_n:int=10):
    """
    Takes a user query then performs semantic search on an NMR textbook, then responds with relevant info

    First, embeds the user query and performs semantic search on a chromadb collection.
    The collection consists of text from Keeler Understanding NMR, which has been split into chunks
    Then converted to embeddings. The collection contains the embeddings, text, and an id.
    If this collection doesn't already exist, then create it by reading the pdfs, splitting text, and creating embeddings.

    The results of the semantic search (text fragments) are organized into a prompt, 
    which is given as context to an LLM to construct a response based on the user query

    By default, only the top 10 similar chunks are used. 
    This is a good baseline but could be increased if context length isn't a problem.

    This function does everything, sequentially calling the functions defined before it.
    """

    print("-------------------------------\n")
    print("Searching through Keeler Understanding NMR...\n")
    print("-------------------------------\n")

    # does everything, see docstring
    prompt = generate_prompt(query, collection, top_n)

    print("-------------------------------\n")
    print("top_n:\n", top_n)
    print("-------------------------------\n")

    # create or get the collection
    collection = create_chroma_client_and_collection(client_path="../chroma_client_assignment_chat")

    # prompt the llm for a response with context from the semantic search
    client = get_client()
    MODEL = os.getenv('MODEL', 'gpt-4o-mini')

    response = client.responses.create(
        model=MODEL,
        instructions="You are a helpful assistant that provides information based on James Keeler's book Understanding NMR Spectroscopy.",
        input=[{"role": "user", "content": prompt}],
        max_output_tokens=500,
        temperature=0.7
    )
    return response.output_text


#response = generate_response("What is an HSQC?", 
#                             collection, 
#                             top_n=1)
