import os
import sys
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from openai import OpenAI
from openai import RateLimitError, InternalServerError, APIStatusError
from dotenv import load_dotenv

load_dotenv()

from mcp_client import MCPClient
from logger import MCPLogger

console = Console()

# TokenRouter: OpenAI-compatible gateway used to reach the Qwen model
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.tokenrouter.com/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen/qwen3.8-max-free")

# Load TokenRouter API key from environment
api_key = os.environ.get("TOKENROUTER_API_KEY")

class ChatbotHost:
    def __init__(self):
        if not api_key:
            console.print("[red]Error: La variable de entorno TOKENROUTER_API_KEY no está configurada.[/red]")
            console.print("Obtén tu clave en: https://tokenrouter.com")
            console.print("Luego ponla en tu archivo .env como: TOKENROUTER_API_KEY='tu-clave-aqui'")
            sys.exit(1)

        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=api_key)
        self.logger = MCPLogger(console)

        # Mapping tool_name -> {client, schema}
        self.available_tools = {}
        self.mcp_clients = []

        # Conversation history as list of message dicts (OpenAI-compatible format)
        self.history = []

        # Base directory of the project (one level up from src)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.system_prompt = (
            "Eres un Asistente Dietético Corporativo especializado para una red de clínicas "
            "de salud y bienestar. Responde en español de forma profesional, clara y empática.\n\n"
            "REGLAS CRÍTICAS SOBRE EL USO DE HERRAMIENTAS:\n"
            "1. SOLO usa 'consultar_perfil_paciente' si el usuario menciona un ID exacto (ej. PAC-1092).\n"
            "2. SOLO usa 'buscar_equivalencia_macronutrientes' si el usuario pide explícitamente SUSTITUIR o REEMPLAZAR un alimento por otro equivalente.\n"
            "3. SOLO usa 'verificar_inventario_suplementos' si el usuario pregunta por disponibilidad en una sucursal específica.\n"
            "4. Si el usuario hace una pregunta general de nutrición o historia, RESPONDE DIRECTAMENTE usando tu conocimiento general SIN invocar herramientas.\n"
            "5. Para las herramientas de Filesystem y Git, usa SIEMPRE esta ruta como directorio del repositorio: {self.base_dir}\n"
            "6. IMPORTANTE PARA GIT: Al usar la herramienta 'git_add', el parámetro 'files' DEBE SER UN ARREGLO (array) de strings, NUNCA un string simple. Ejemplo correcto: {\"files\": [\"archivo.txt\"]}.\n"
            "7. IMPORTANTE PARA FILESYSTEM: NUNCA uses la herramienta 'directory_tree' en la raíz del proyecto porque causará un error de exceso de tokens por las carpetas venv y .git. Usa 'list_directory' en su lugar."
        )

    def setup_servers(self):
        console.print("[yellow]Iniciando servidores MCP...[/yellow]")

        # 1. Nutritional MCP Server — custom server for this project
        nutri_cmd = [sys.executable, os.path.join(self.base_dir, "src", "server", "mcp_server.py")]
        self._start_client(nutri_cmd, "Nutricional-Server")

        # 2. Filesystem MCP Server (official, NPM) — read/write access to this project directory
        fs_cmd = ["npx", "-y", "@modelcontextprotocol/server-filesystem", self.base_dir]
        self._start_client(fs_cmd, "Filesystem-Server")

        # 3. Git MCP Server (official, Python package "mcp-server-git")
        git_cmd = [sys.executable, "-m", "mcp_server_git", "--repository", self.base_dir]
        self._start_client(git_cmd, "Git-Server")

        console.print("[green]✓ Servidores MCP iniciados correctamente.[/green]\n")

    def _start_client(self, cmd, name):
        try:
            client = MCPClient(cmd, name)
            client.start(logger=self.logger)
            self.mcp_clients.append(client)

            mcp_tools = client.get_tools_for_llm()
            for tool in mcp_tools:
                self.available_tools[tool["name"]] = {
                    "client": client,
                    "schema": tool
                }
        except Exception as e:
            console.print(f"[red]Error al iniciar servidor {name}: {str(e)}[/red]")

    def get_llm_tools(self):
        """Convert MCP tool schemas to OpenAI-compatible function calling format."""
        tools = []
        for info in self.available_tools.values():
            schema = info["schema"]
            parameters = schema.get("inputSchema", {})
            if "type" not in parameters:
                parameters["type"] = "object"
            # Remove unsupported JSON Schema keys
            parameters.pop("additionalProperties", None)

            tools.append({
                "type": "function",
                "function": {
                    "name": schema["name"],
                    "description": schema["description"],
                    "parameters": parameters
                }
            })
        return tools if tools else None

    def run(self):
        self.setup_servers()

        console.print(Panel.fit(
            f"[bold cyan]Asistente Dietético Corporativo (Potenciado por Qwen y MCP)[/bold cyan]\n"
            f"Modelo: {LLM_MODEL} (vía TokenRouter)\n"
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

                self._process_llm_response(user_input)

            except KeyboardInterrupt:
                break

        self.cleanup()

    def _call_llm_with_retry(self, messages, tools, max_retries=4):
        """Call the LLM (Qwen via TokenRouter) with automatic retry on rate limit and server errors."""
        kwargs = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(**kwargs)
            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait = 30
                    console.print(f"[yellow]⚠ Límite de velocidad (429). Esperando {wait}s... (intento {attempt+1}/{max_retries-1})[/yellow]")
                    time.sleep(wait)
                else:
                    console.print(f"[red]✗ Límite de tasa agotado: {str(e)[:150]}[/red]")
                    return None
            except InternalServerError as e:
                if attempt < max_retries - 1:
                    wait = 10 * (attempt + 1)
                    console.print(f"[yellow]⚠ Error interno del servidor. Esperando {wait}s... (intento {attempt+1}/{max_retries-1})[/yellow]")
                    time.sleep(wait)
                else:
                    console.print("[red]✗ El servidor de TokenRouter no está disponible. Intenta de nuevo.[/red]")
                    return None
            except APIStatusError as e:
                console.print(f"[red]✗ Error de API ({e.status_code}): {str(e)[:150]}[/red]")
                return None

    def _process_llm_response(self, user_input):
        """Orchestrate a full LLM turn with tool-calling support using Qwen (via TokenRouter).

        self.history  → only clean user/assistant text messages (persistent)
        turn_messages → includes intermediate tool calls (temporary, per-turn)
        """
        llm_tools = self.get_llm_tools()

        # Add user message to persistent history
        self.history.append({"role": "user", "content": user_input})

        # Build the turn message list: system + clean history
        # Tool-calling intermediates will only live in turn_messages
        turn_messages = [{"role": "system", "content": self.system_prompt}] + self.history[:]

        with console.status("[bold blue]Qwen está pensando...", spinner="dots"):
            while True:
                response = self._call_llm_with_retry(turn_messages, llm_tools)

                if response is None:
                    console.print("[red]No se pudo obtener respuesta. Por favor intenta de nuevo.[/red]")
                    self.history.pop()  # Remove user message to keep history clean
                    break

                assistant_message = response.choices[0].message

                if assistant_message.tool_calls:
                    # Add this tool-calling step to turn_messages only (NOT to self.history)
                    turn_messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })

                    # Execute each tool and add results to turn_messages only
                    for tc in assistant_message.tool_calls:
                        tool_name = tc.function.name
                        try:
                            tool_args = json.loads(tc.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}

                        console.print(f"[dim italic]Qwen invocó herramienta: {tool_name}[/dim italic]")

                        if tool_name in self.available_tools:
                            mcp_client = self.available_tools[tool_name]["client"]
                            result = mcp_client.call_tool(tool_name, tool_args)
                        else:
                            result = f"Error: Tool '{tool_name}' not found."

                        turn_messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": str(result)
                        })

                    # Continue — model will now synthesize a final text answer
                    continue

                else:
                    # Final text answer — save only this clean message to persistent history
                    final_text = assistant_message.content or ""
                    self.history.append({"role": "assistant", "content": final_text})

                    if final_text:
                        console.print("\n[bold magenta]Asistente:[/bold magenta]")
                        console.print(Markdown(final_text))
                    break

    def cleanup(self):
        console.print("\n[yellow]Cerrando servidores...[/yellow]")
        for client in self.mcp_clients:
            client.stop()
        console.print("[green]Adiós.[/green]")

if __name__ == "__main__":
    host = ChatbotHost()
    host.run()
