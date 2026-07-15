import os
import re
import subprocess
import sys
import time
from openai import OpenAI
from langchain.tools import tool

# ==========================================
# CONFIGURATION
# ==========================================
# The exact directory where 'python -m zotero_mcp.server' runs successfully
REPO_SRC_DIR = "/Users/robertlu/Documents/Biochemistry/DSI/deploying-ai/05_src/zotero-mcp-server/src"
LOCAL_PORT = "8085"  # Shifted away from 8080 to avoid potential collisions

USE_GATEWAY = (os.getenv('USE_GATEWAY', 'FALSE').upper() == 'TRUE')
MODEL = os.getenv('MODEL', 'gpt-4o-mini')

def get_client(use_gateway: bool = USE_GATEWAY) -> OpenAI:
    """
    Gets the llm client 
    Normally the DSI gateway is used

    """
    if use_gateway:
        client = OpenAI(base_url='https://k7uffyg03f.execute-api.us-east-1.amazonaws.com/prod/openai/v1',
                    api_key='any value',
                    default_headers={"x-api-key": os.getenv('API_GATEWAY_KEY')})
    else:
        client = OpenAI()
    return client

@tool
def launch_mcp_and_query(user_query):
    """
    Launches a local MCP server, then queries a local zotero collection

    Most of this code was written by gemini, but i worked through (with the help of gemini) 
    to get a section 4 working on in a jupyter notebook first, so I think i have a decent understanding of what's going on here?
    This is the core component which connects to the mcp server

    However currently the user queries arent defined that well. I think the chat needs to be really clear
    Update: i made it better by specifying example queries in the system prompt. 
    Examples from the mcp server page here: https://glama.ai/mcp/servers/awsl5714/zotero-mcp-server

    """
    client = get_client()
    
    # 1. Build the shell command exactly as you ran it manually
    cmd = [
        "npx", "mcp-proxy", 
        "--port", LOCAL_PORT, 
        "--tunnel", 
        "--", "python", "-m", "zotero_mcp.server"
    ]
    
    print("⏳ Starting local Zotero MCP server & establishing Glama tunnel...")
    
    # 2. Launch the server as a background subprocess
    # stderr=subprocess.STDOUT merges errors into stdout so we catch everything
    server_process = subprocess.Popen(
        cmd,
        cwd=REPO_SRC_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1 # Line-buffered for real-time streaming
    )
    print("⏳ Waiting...")
    tunnel_url = None
    
    try:
        # 3. Read the background terminal logs line-by-line to extract the URL
        for line in iter(server_process.stdout.readline, ""):
            # Optional: Uncomment the line below to watch the server boot logs in real-time
            # print(f"[Server] {line.strip()}")
            
            if "tunnel.gla.ma" in line:
                # Extract the raw HTTPS link using Regex
                match = re.search(r'https://[^\s]+', line)
                if match:
                    raw_url = match.group(0).strip()
                    # Ensure it handles clean formatting and has the /sse suffix
                    tunnel_url = raw_url.rstrip("/") if raw_url.endswith("/") else raw_url
                    if not tunnel_url.endswith("/sse"):
                        tunnel_url += "/sse"
                    break
        
        if not tunnel_url:
            print("❌ Failed to discover tunnel URL. Check if server crashed on startup.")
            return

        print(f"🚀 Tunnel Established Successfully: {tunnel_url}")
        print("🤖 Firing Agent Request via OpenAI Client...")
        
        # 4. Pass the dynamically extracted URL directly into your OpenAI Agent call
        response = client.responses.create(
            model="gpt-4o-mini", # Your university gateway model
            tools=[
                {
                    "type": "mcp",
                    "server_label": f"zotero-agent-{int(time.time())}", # Unique label busts OpenAI tool cache
                    "server_description": "Fetches reference documents or collections from the user's Zotero desktop application to answer user queries.",
                    "server_url": tunnel_url,
                    "require_approval": "never"
                }
            ],
            input=user_query
        )
        print("\n--- User Query ---")
        print(user_query)
        print("-------------------------------\n")

        print("\n--- Agent Execution Result ---")
        print(response.output_text)
        print("-------------------------------\n")

    except Exception as e:
        print(f"❌ Execution Error: {e}")
        
    finally:
        # 5. CRITICAL: Safely kill the background process when the query finishes or fails
        print("🧼 Cleaning up: Shutting down local MCP server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✅ Server process stopped cleanly. Port released.")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("⚠️ Server process forced to quit.")

    return response.output_text