from langchain.tools import tool
import json
import requests
import os

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".secrets")

#core_api_key = os.getenv("CORE_API_KEY")
# need to register and get an api key
# https://core.ac.uk/services/api#form
# I put my api key in the .secrets file

@tool
def query_core_api(url_fragment, query, is_scroll=False, limit=1, scrollId=None):
    """
    Queries the CORE API to perform a search of works

    See example code here:
    https://github.com/oacore/apiv3-webinar
    """
    headers={"Authorization":"Bearer "+os.getenv("CORE_API_KEY")}
    api_endpoint = "https://api.core.ac.uk/v3/"
    url_fragment = "search/works"
    
    query = {"q":query, "limit":limit}
    if not is_scroll:
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query), headers=headers)
    elif not scrollId:
        query["scroll"]="true"
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query),headers=headers)
    else:
        query["scrollId"]=scrollId
        response = requests.post(f"{api_endpoint}{url_fragment}",data = json.dumps(query),headers=headers)
    
    if response.status_code ==200:
        return response.json(), response.elapsed.total_seconds()
    else:
        print(f"Error code {response.status_code}, {response.content}")


@tool
def get_cat_facts(n:int=1):
    """
    Returns n cat facts from the Meowfacts API.
    """
    url = "https://meowfacts.herokuapp.com/"
    params = {
        "count": n
    }
    response = requests.get(url, params=params)
    resp_dict = json.loads(response.text)
    facts_list = resp_dict.get("data", [])
    facts = "\n".join([f"{i+1}. {fact}\n" for i, fact in enumerate(facts_list)])
    return facts

@tool
def get_dog_facts(n:int=1):
    """
    Returns n dog facts from the Dog API.
    """
    url = "http://dogapi.dog/api/v2/facts"
    params = {
        "limit": n
    }
    response = requests.get(url, params=params)
    resp_dict = json.loads(response.text)
    facts_list = resp_dict.get("data", [])
    facts = "\n".join([f"{i+1}. {fact['attributes']['body']}\n" for i, fact in enumerate(facts_list)])
    return facts
