import sys
from chatbot import ChatbotHost
host = ChatbotHost()
host.setup_servers()
print("Available tools:", host.available_tools.keys())
for c in host.mcp_clients:
    c.stop()
