import os
import sys
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from anthropic import Anthropic

from mcp_client import MCPClient
from logger import MCPLogger

console = Console()

# Asegurar que el API key esté configurado
api_key = os.environ.get("ANTHROPIC_API_KEY")

class ChatbotHost:
    def __init__(self):
        if not api_key:
            console.print("[red]Error: La variable de entorno ANTHROPIC_API_KEY no está configurada.[/red]")
            console.print("Por favor, obtén tu clave de Anthropic (tienen créditos gratuitos) y ejecuta:")
            console.print("export ANTHROPIC_API_KEY='tu-clave-aqui'")
            sys.exit(1)
            
        self.llm = Anthropic(api_key=api_key)
        self.logger = MCPLogger(console)
        self.messages = []
        
        # Mapeo de nombre de herramienta -> (instancia del cliente MCP, schema)
        self.available_tools = {}
        self.mcp_clients = []
        
        # Directorio base del proyecto
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def setup_servers(self):
        console.print("[yellow]Iniciando servidores MCP...[/yellow]")
        
        # 1. Servidor Nutricional (Local)
        nutri_cmd = [sys.executable, os.path.join(self.base_dir, "server", "mcp_server.py")]
        self._start_client(nutri_cmd, "Nutricional-Server")
        
        # 2. Servidor Filesystem (NPM) - Permite leer/escribir en este directorio
        fs_cmd = ["npx", "-y", "@modelcontextprotocol/server-filesystem", self.base_dir]
        self._start_client(fs_cmd, "Filesystem-Server")
        
        # 3. Servidor Git (NPM)
        git_cmd = ["npx", "-y", "@modelcontextprotocol/server-git"]
        self._start_client(git_cmd, "Git-Server")
        
        console.print("[green]✓ Servidores MCP iniciados correctamente.[/green]\n")

    def _start_client(self, cmd, name):
        try:
            client = MCPClient(cmd, name)
            client.start(logger=self.logger)
            self.mcp_clients.append(client)
            
            # Registrar herramientas
            anthropic_tools = client.get_tools_for_llm()
            for tool in anthropic_tools:
                self.available_tools[tool["name"]] = {
                    "client": client,
                    "schema": tool
                }
        except Exception as e:
            console.print(f"[red]Error al iniciar servidor {name}: {str(e)}[/red]")

    def get_anthropic_tools_schema(self):
        return [info["schema"] for info in self.available_tools.values()]

    def run(self):
        self.setup_servers()
        
        console.print(Panel.fit(
            "[bold cyan]Asistente Dietético Corporativo (con soporte Git/FS)[/bold cyan]\n"
            "Escribe tu mensaje o 'salir' para terminar.\n"
            "Escribe 'logs' para ver el historial de interacciones MCP.",
            border_style="cyan"
        ))
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold green]Tú[/bold green]")
                if user_input.lower() in ['salir', 'exit', 'quit']:
                    break
                if user_input.lower() == 'logs':
                    self.logger.show_logs()
                    continue
                    
                self.messages.append({"role": "user", "content": user_input})
                self._process_llm_response()
                
            except KeyboardInterrupt:
                break
                
        self.cleanup()

    def _process_llm_response(self):
        tools = self.get_anthropic_tools_schema()
        
        with console.status("[bold blue]Claude está pensando...", spinner="dots"):
            while True:
                response = self.llm.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2048,
                    messages=self.messages,
                    tools=tools
                )
                
                # Append Claude's message to conversation
                self.messages.append({"role": "assistant", "content": response.content})
                
                # Procesar paradas por invocación de herramienta
                if response.stop_reason == "tool_use":
                    # Buscar la(s) herramienta(s) invocada(s)
                    for content_block in response.content:
                        if content_block.type == "tool_use":
                            tool_name = content_block.name
                            tool_args = content_block.input
                            tool_use_id = content_block.id
                            
                            console.print(f"[dim italic]Claude invocó herramienta: {tool_name}[/dim italic]")
                            
                            # Ejecutar la herramienta en el servidor correcto
                            if tool_name in self.available_tools:
                                client = self.available_tools[tool_name]["client"]
                                result = client.call_tool(tool_name, tool_args)
                            else:
                                result = f"Error: Tool '{tool_name}' not found."
                                
                            # Agregar resultado al historial para que Claude lo lea
                            self.messages.append({
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": str(result)
                                    }
                                ]
                            })
                    # Continuar el bucle para que Claude responda con el resultado
                    continue
                else:
                    # Respuesta final de texto
                    for content_block in response.content:
                        if content_block.type == "text":
                            console.print("\n[bold magenta]Asistente:[/bold magenta]")
                            console.print(Markdown(content_block.text))
                    break

    def cleanup(self):
        console.print("\n[yellow]Cerrando servidores...[/yellow]")
        for client in self.mcp_clients:
            client.stop()
        console.print("[green]Adiós.[/green]")

if __name__ == "__main__":
    host = ChatbotHost()
    host.run()
