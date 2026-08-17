import sys
from src.client.mcp_client import MCPClient
client = MCPClient([sys.executable, "-m", "mcp_server_git", "--repository", "/Users/joseruiz_002/Documents/UVG/8to Semestre/Redes/nutrition-mcp-server"], "Git-Server")
try:
    client.start()
    print("Success:", [t['name'] for t in client.tools])
except Exception as e:
    print("Error:", str(e))
client.stop()
