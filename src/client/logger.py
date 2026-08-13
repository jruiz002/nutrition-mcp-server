import json
from datetime import datetime
from rich.console import Console
from rich.table import Table

class MCPLogger:
    def __init__(self, console: Console):
        self.console = console
        self.logs = []
        
    def log_interaction(self, server_name, action, status, details):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            "time": timestamp,
            "server": server_name,
            "action": action,
            "status": status,
            "details": details
        }
        self.logs.append(log_entry)
        
        # Log to file
        with open("mcp_interactions.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Optional debug output to console
        # self.console.print(f"[dim]{timestamp} [{server_name}] {action} - {status}[/dim]")

    def show_logs(self):
        table = Table(title="Registro de Interacciones MCP")
        table.add_column("Hora", style="cyan", no_wrap=True)
        table.add_column("Servidor", style="magenta")
        table.add_column("Acción", style="green")
        table.add_column("Estado", style="yellow")
        
        for log in self.logs[-10:]: # Show last 10
            table.add_row(log["time"], log["server"], log["action"], log["status"])
            
        self.console.print(table)
