# Nutritional MCP Server & Chatbot Host

Este proyecto implementa un protocolo **MCP (Model Context Protocol)** desde cero utilizando **JSON-RPC 2.0** a través de la entrada/salida estándar (`stdio`). Incluye tanto un **Servidor MCP** especializado en consultas nutricionales para una clínica, como un **Anfitrión (Chatbot)** interactivo de consola que utiliza el LLM de Anthropic (Claude) para coordinar llamadas a múltiples servidores MCP (el servidor nutricional, y los servidores oficiales de filesystem y git).

## 1. Características

1. **Cliente / Chatbot (Host)**: 
   - Conexión a la API de Anthropic, manteniendo contexto de la conversación.
   - Interfaz de consola rica e interactiva utilizando `rich`.
   - Conexión concurrente a múltiples servidores MCP.
   - Sistema de logging interno para auditar interacciones JSON-RPC.

2. **Servidor MCP (Nutricional)**:
   - Implementado desde cero (sin SDKs de MCP).
   - Base de datos simulada abundante (CSV de alimentos, JSON de pacientes e inventario).
   - Expone 3 herramientas principales:
     - `consultar_perfil_paciente`: Obtiene datos de pacientes y alergias.
     - `buscar_equivalencia_macronutrientes`: Algoritmo para buscar sustitutos de alimentos basados en proteínas equivalentes.
     - `verificar_inventario_suplementos`: Verifica disponibilidad de suplementos en distintas sedes.

## 2. Arquitectura (JSON-RPC)

El proyecto utiliza la siguiente arquitectura donde el Chatbot orquesta las peticiones:

```mermaid
graph TD
    User([👤 Usuario]) <--> |Terminal| Chatbot
    
    subgraph "Cliente (Host)"
        Chatbot[🤖 Chatbot Anfitrión]
        Chatbot <--> |Internet| API_Anthropic[(Claude API)]
    End
    
    subgraph "Servidores Locales MCP (JSON-RPC sobre stdio)"
        Chatbot <--> |JSON-RPC| TuServidorMCP[🩺 Servidor Nutricional]
        Chatbot <--> |JSON-RPC| GitMCP[🐙 Git MCP Server]
        Chatbot <--> |JSON-RPC| FSMCP[📁 Filesystem MCP]
    End
```

## 3. Requisitos Previos

- Python 3.8 o superior.
- Node.js / `npx` (para ejecutar los servidores MCP oficiales de Git y Filesystem).
- Una API Key de Anthropic (Claude).

## 4. Instalación y Uso

1. **Configura tu API Key:**
   Debes obtener una API Key de Anthropic (tienen $5 gratuitos para desarrolladores) y exportarla como variable de entorno:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

2. **Inicia el asistente:**
   El proyecto incluye un script `run.sh` que creará un entorno virtual aislado (venv), instalará las dependencias necesarias (`rich`, `anthropic`), e iniciará el cliente:
   ```bash
   ./run.sh
   ```

3. **Uso del Chatbot:**
   - Realiza consultas como: *"Revisa mi perfil (PAC-1092). Quiero sustituir los 150g de salmón de mi dieta, busca una equivalencia que pueda comer. ¿Tienen omega 3 en zona 10?"*
   - Escribe `logs` para ver la traza de llamadas a funciones JSON-RPC en vivo.
   - Escribe `salir` para terminar la sesión.
   - Pide a Claude que utilice Git o el Filesystem para modificar archivos de ser necesario.

## 5. Implementación del Protocolo
Se ha evitado el uso de SDKs como FastMCP. El archivo `src/server/mcp_server.py` implementa un bucle infinito que lee desde `sys.stdin` buscando objetos JSON válidos, y despacha métodos como `initialize`, `tools/list`, y `tools/call`, enviando las respuestas formateadas en JSON-RPC a `sys.stdout`.
