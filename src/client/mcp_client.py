import subprocess
import json
import threading
import time

class MCPClient:
    """Cliente que implementa JSON-RPC para comunicarse con un servidor MCP por stdio."""
    
    def __init__(self, command, name):
        self.command = command
        self.name = name
        self.process = None
        self.message_id = 1
        self.responses = {}
        self.tools = []
        self.lock = threading.Lock()
        self.is_connected = False

    def start(self, logger=None):
        """Inicia el subproceso del servidor."""
        self.logger = logger
        self.process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Ignore stderr for simplicity or log it
            text=True,
            bufsize=1
        )
        
        # Iniciar thread para leer respuestas asíncronamente
        self.reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader_thread.start()
        
        # Enviar petición de inicialización
        response = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "nutritional-mcp-client",
                "version": "1.0.0"
            }
        })
        
        if response and not "error" in response:
            # Enviar notificación de initialized
            self.send_notification("notifications/initialized", {})
            self.is_connected = True
            if self.logger:
                self.logger.log_interaction(self.name, "initialize", "SUCCESS", response)
            
            # Obtener lista de herramientas
            tools_response = self.send_request("tools/list", {})
            if tools_response and "result" in tools_response:
                self.tools = tools_response["result"]["tools"]
                if self.logger:
                    self.logger.log_interaction(self.name, "tools/list", "SUCCESS", tools_response)
        else:
            if self.logger:
                self.logger.log_interaction(self.name, "initialize", "ERROR", response)
            raise Exception(f"Fallo al inicializar servidor {self.name}")

    def _read_stdout(self):
        """Lee líneas de stdout del servidor y las guarda en el diccionario de respuestas."""
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            
            try:
                response = json.loads(line)
                if "id" in response:
                    with self.lock:
                        self.responses[response["id"]] = response
            except json.JSONDecodeError:
                pass # Ignorar líneas que no sean JSON

    def send_notification(self, method, params):
        """Envía una notificación (no espera respuesta)."""
        msg = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        self.process.stdin.write(json.dumps(msg) + "\n")
        self.process.stdin.flush()

    def send_request(self, method, params, timeout=5.0):
        """Envía una petición y espera la respuesta."""
        with self.lock:
            req_id = self.message_id
            self.message_id += 1
            
        msg = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        
        self.process.stdin.write(json.dumps(msg) + "\n")
        self.process.stdin.flush()
        
        # Esperar respuesta
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.lock:
                if req_id in self.responses:
                    return self.responses.pop(req_id)
            time.sleep(0.05)
            
        return {"error": {"message": "Timeout esperando respuesta"}}

    def call_tool(self, tool_name, arguments):
        """Ejecuta una herramienta y registra en el log."""
        request_params = {
            "name": tool_name,
            "arguments": arguments
        }
        
        if self.logger:
            self.logger.log_interaction(self.name, f"tools/call: {tool_name}", "PENDING", request_params)
            
        response = self.send_request("tools/call", request_params)
        
        if self.logger:
            status = "ERROR" if "error" in response or (response.get("result", {}).get("isError")) else "SUCCESS"
            self.logger.log_interaction(self.name, f"tools/call: {tool_name}", status, response)
            
        if "error" in response:
            return f"Error: {response['error']}"
            
        result = response.get("result", {})
        if result.get("isError"):
            return f"Tool Error: {result.get('content', [{}])[0].get('text')}"
            
        return result.get("content", [{}])[0].get("text", "Sin respuesta")

    def get_tools_for_llm(self):
        """Convierte las herramientas MCP al formato esperado por la API de Anthropic."""
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["inputSchema"]
            })
        return anthropic_tools

    def stop(self):
        """Detiene el proceso."""
        if self.process:
            self.process.terminate()
            self.is_connected = False
