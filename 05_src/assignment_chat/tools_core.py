from langchain.tools import tool
import json
import requests
import os
import numpy as np

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".secrets")

#core_api_key = os.getenv("CORE_API_KEY")
# need to register and get an api key
# https://core.ac.uk/services/api#form
# I put my api key in the .secrets file

@tool
def query_core_api(url_fragment, query, is_scroll=False, limit=5, scrollId=None):
    """
    Queries the CORE API to perform a search of works based on a user query, and returns the result of one paper

    See example code here:
    https://github.com/oacore/apiv3-webinar

    in the current implementation, I set the limit to 5, so the CORE search result returns 5 papers
    then randomly select just one paper to summarize, to try and stay within the context limit of gpt-4o-mini
    I think the limit of 5 papers also helps to stay with CORE API limits?

    Also, it seems like i often run into search limits, maybe from CORE? See error below

    Error code 500, b'{"message":"Azure search failed with status code: 503. Error context: message=Failed to execute request because the request rate has caused your service to exceed the limits of its provisioned capacity. Reduce the rate of requests, or adjust the number of replicas\\/partitions. See http:\\/\\/aka.ms\\/azure-search-throttling for more information., request-id=ccb2f74e-c8ed-41f8-b4ab-afdd54545543"}'

    And also sometimes theres a gateway timeout, idk if from DSI or CORE (error code 504)
    
    """
    headers={"Authorization":"Bearer "+os.getenv("CORE_API_KEY")}
    api_endpoint = "https://api.core.ac.uk/v3/"
    url_fragment = "search/works"
    
    query = {"q":query, "limit":limit}

    print("\n--- Performing CORE Query ---")
    print(query)
    print("-------------------------------\n")

    if not is_scroll:
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query), headers=headers)
    elif not scrollId:
        query["scroll"]="true"
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query),headers=headers)
    else:
        query["scrollId"]=scrollId
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query),headers=headers)
    
    if response.status_code ==200:

        random_paper_index = np.random.randint(limit)
        result = response.json()["results"][random_paper_index]

        print("\n--- Web Search Result ---")
        print(response.output_text)
        print("-------------------------------\n")

        return result, response.elapsed.total_seconds()
        #return response.json(), response.elapsed.total_seconds()
    else:
        print(f"Error code {response.status_code}, {response.content}")



