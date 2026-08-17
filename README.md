# Nutritional MCP Server — Asistente Dietético Corporativo

> **Course:** CC3067 Redes — Universidad del Valle de Guatemala  
> **Student:** José Gerardo Ruiz García — 23719  
> **Project:** Implementation of the Model Context Protocol (MCP) applied to a corporate nutritional assistant for a network of health and wellness clinics.

---

## Table of Contents

1. [What is this project?](#1-what-is-this-project)
2. [What is MCP?](#2-what-is-mcp-model-context-protocol)
3. [Architecture](#3-architecture)
4. [MCP Server Specification](#4-mcp-server-specification-tools)
5. [Prerequisites](#5-prerequisites)
6. [Installation & Usage (Step-by-Step)](#6-installation--usage-step-by-step)
7. [Usage Examples](#7-usage-examples)
8. [Database](#8-database)
9. [Project Structure](#9-project-structure)

---

## 1. What is this project?

Large Language Models (LLMs) are powerful, but they are isolated from the real world. They cannot access private databases, patient medical records, or real-time inventory systems. The **Model Context Protocol (MCP)** solves this by providing a standardized way to connect LLMs to external tools securely.

This project implements a fully functional **Corporate Dietetic Assistant Chatbot** for a fictional network of health and wellness clinics. It uses Qwen3.8 Max (via [TokenRouter](https://tokenrouter.com), an OpenAI-compatible gateway) as the LLM and connects to a custom-built **Nutritional MCP Server**, plus the official **Filesystem** and **Git** MCP servers, that act as a secure gateway to private clinical data and local tooling.

**The core value proposition:** The LLM (running in the public cloud) never has direct access to the patient database. The MCP Server acts as a controlled security barrier, exposing only specific, audited RPC functions necessary to answer the query — protecting patient confidentiality.

---

## 2. What is MCP? (Model Context Protocol)

MCP is an open standard proposed by Anthropic in November 2024. It defines a universal way for AI agents (Hosts) to communicate with external tools (Servers) using **JSON-RPC 2.0** over a transport layer (local: `stdio`; remote: HTTP/SSE).

### Three Key Actors

| Actor | Role | Implementation in this project |
|---|---|---|
| **Host** | The AI application orchestrating everything | `src/client/chatbot.py` — uses the Qwen model via TokenRouter's OpenAI-compatible API |
| **Client** | Manages the connection to a single server | `src/client/mcp_client.py` — manual JSON-RPC over stdio |
| **Server** | Exposes tools and executes actions | `src/server/mcp_server.py` — custom nutritional server |

> **Important:** The entire JSON-RPC 2.0 protocol — including message framing, lifecycle management (`initialize`, `notifications/initialized`), capability discovery (`tools/list`), and tool execution (`tools/call`) — was implemented **manually from scratch** without any MCP SDK (no FastMCP or similar libraries).

---

## 3. Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                       HOST (chatbot.py)                            │
│                                                                     │
│  User ──► Prompt ──► TokenRouter API (qwen/qwen3.8-max-free)       │
│                           │                                        │
│             ┌─────────────┼───────────────┐                       │
│             ▼             ▼               ▼                       │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│    │  MCP Client  │  │  MCP Client  │  │  MCP Client  │           │
│    │ (Nutricional)│  │ (Filesystem) │  │    (Git)     │           │
│    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
└───────────┼─────────────────┼─────────────────┼───────────────────┘
            │ JSON-RPC 2.0    │ JSON-RPC 2.0    │ JSON-RPC 2.0
            │ (stdio)         │ (npx/stdio)     │ (npx/stdio)
            ▼                 ▼                 ▼
   ┌──────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
   │  mcp_server.py   │  │ @modelcontextprotocol │  │ @modelcontext     │
   │  (Custom Server) │  │  /server-filesystem   │  │ protocol/server-  │
   │                  │  │  (Official NPM pkg)   │  │ git (Official)    │
   │  ├─ alimentos.csv│  └──────────────────────┘  └──────────────────┘
   │  ├─ pacientes.json│
   │  └─ inventario.json│
   └──────────────────┘
```

### JSON-RPC 2.0 Message Flow

```
Client ──► {"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}
Server ◄── {"jsonrpc":"2.0","id":1,"result":{"capabilities":{...}}}
Client ──► {"jsonrpc":"2.0","method":"notifications/initialized","params":{}}
Client ──► {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
Server ◄── {"jsonrpc":"2.0","id":2,"result":{"tools":[...]}}
Client ──► {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"consultar_perfil_paciente","arguments":{"paciente_id":"PAC-1092"}}}
Server ◄── {"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"..."}]}}
```

---

## 4. MCP Server Specification (Tools)

The custom Nutritional MCP Server exposes **3 tools** to the LLM:

### `consultar_perfil_paciente`

Returns a patient's clinical profile from the private medical records database.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `paciente_id` | `string` | ✅ | Patient ID (format: `PAC-XXXX`) |

**Example call:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "consultar_perfil_paciente",
    "arguments": { "paciente_id": "PAC-1092" }
  }
}
```

**Example response:**
```json
{
  "result": {
    "content": [{
      "type": "text",
      "text": "Patient PAC-1092 — Juan Pérez (35 yo, BMI 27.8). Conditions: insulin_resistance. Allergies: shellfish, dairy. Goal: Fat reduction. Daily caloric plan: 1800 kcal."
    }]
  }
}
```

---

### `buscar_equivalencia_macronutrientes`

Queries the nutritional database (120+ foods based on USDA FoodData Central) to find foods with equivalent macronutrient content to a reference food, scaled by grams.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `alimento_origen` | `string` | ✅ | Name of the reference food (e.g., `"salmón"`) |
| `gramos` | `number` | ✅ | Amount in grams of the reference food |

**Example call:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "buscar_equivalencia_macronutrientes",
    "arguments": { "alimento_origen": "Salmón Atlántico", "gramos": 150 }
  }
}
```

**Example response:**
```
Reference (150g Salmón Atlántico): Protein 30.6g | Carbs 0.0g | Fat 20.1g | 312 kcal

Top 5 equivalents by protein content:
1. Pechuga de Pollo (148g) — Protein 30.6g | Fat 5.3g | 244 kcal  [Allergens: none]
2. Pavo Magro (158g) — Protein 30.6g | Fat 3.2g | 213 kcal  [Allergens: none]
3. Tilapia (152g) — Protein 30.6g | Fat 4.1g | 164 kcal  [Allergens: fish]
...
```

---

### `verificar_inventario_suplementos`

Checks supplement stock at a specific clinic branch from the simulated ERP inventory system.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `categoria` | `string` | ✅ | Supplement category (e.g., `"omega_3"`, `"proteina_suero"`, `"creatina"`) |
| `sucursal` | `string` | ✅ | Branch name: `zona_1`, `zona_10`, `zona_14`, `mixco`, `antigua_guatemala` |

**Example call:**
```json
{
  "method": "tools/call",
  "params": {
    "name": "verificar_inventario_suplementos",
    "arguments": { "categoria": "omega_3", "sucursal": "zona_10" }
  }
}
```

**Example response:**
```
Branch: zona_10 | Product: omega_3
Stock: 12 units | Price: Q150.00 / frasco 60 caps | Status: AVAILABLE ✓
```

---

## 5. Prerequisites

Before running this project, ensure you have:

| Requirement | Version | Purpose |
|---|---|---|
| **Python** | 3.8 or higher | Running the server and client |
| **Node.js (npx)** | Any LTS | Running the official Filesystem MCP server (downloaded on first run) |
| **TokenRouter API Key** | Free tier (unlimited quota on `qwen/qwen3.8-max-free`) | Connecting the chatbot to the Qwen model via TokenRouter |
| **Git** | Any | Version control, and required by the Git MCP server (`mcp-server-git`, installed automatically via `requirements.txt`) |

---

## 6. Installation & Usage (Step-by-Step)

### Step 1 — Clone the repository

```bash
git clone https://github.com/jruiz002/nutrition-mcp-server.git
cd nutrition-mcp-server
```

### Step 2 — Configure your TokenRouter API Key

Get your **free** API key at [tokenrouter.com](https://tokenrouter.com) (the free tier includes unlimited quota for `qwen/qwen3.8-max-free`).

Create a `.env` file in the project root:

```env
TOKENROUTER_API_KEY=sk-...your-key-here
LLM_BASE_URL=https://api.tokenrouter.com/v1
LLM_MODEL=qwen/qwen3.8-max-free
```

`LLM_BASE_URL` and `LLM_MODEL` are optional — the values above are already the defaults baked into `chatbot.py`, but keeping them explicit in `.env` makes it easy to point the chatbot at a different OpenAI-compatible provider or model later without touching code.

### Step 3 — Generate the simulated database

This creates the nutritional CSV and JSON files used by the MCP server:

```bash
python3 setup_data.py
```

You should see:
```
✓ Generado alimentos.csv (120 registros reales basados en USDA/Open Food Facts)
✓ Generado pacientes.json (7 pacientes)
✓ Generado inventario.json (5 sucursales, múltiples suplementos)
✅ Base de datos clínica simulada creada exitosamente.
```

### Step 4 — Run the chatbot (Local or Cloud)

This project supports running the Nutritional MCP Server either locally (as a subprocess) or remotely in the cloud (via TCP Sockets) for Wireshark analysis.

#### Option A: Run Locally (Default)
```bash
./run.sh
```
The script automatically:
1. Creates a Python virtual environment (`venv/`)
2. Installs all dependencies from `requirements.txt`
3. Launches the interactive chatbot and spawns the local MCP servers.

#### Option B: Run Remotely on AWS (For Wireshark JSON-RPC Capture)
If you want to capture the JSON-RPC traffic over a plain TCP connection, you can host the server on an AWS EC2 instance.

**1. Copy the server code to your EC2 instance:**
```bash
# Replace 'keys-aws.pem' and the IP with your own
scp -i keys-aws.pem -r src/server ubuntu@YOUR_EC2_IP:~/server
```

**2. Start the server on AWS using `socat`:**
Connect to your EC2 via SSH and run:
```bash
sudo apt update && sudo apt install socat -y
cd server
nohup socat TCP-LISTEN:5000,fork EXEC:"python3 mcp_server.py" > servidor.log 2>&1 &
```
*(This runs the server in the background so it survives when you close the SSH terminal. Make sure your EC2 Security Group allows Custom TCP Inbound traffic on port 5000).*

**3. Connect your local chatbot to the cloud server:**
Back on your local machine, export the environment variable and start the script:
```bash
export REMOTE_NUTRITIONAL_SERVER="YOUR_EC2_IP:5000"
./run.sh
```

> **Note for Wireshark:** Because we use `socat` to create a plain TCP tunnel (without TLS/HTTPS encryption), you can open Wireshark locally, filter by `tcp.port == 5000`, and inspect the `JSON-RPC 2.0` packets in clear text.

### Step 5 — Interact

Once the panel appears, you can type any message in natural language. Type `logs` to inspect the MCP interaction log, or `salir` / `exit` to quit.

---

## 7. Usage Examples

### Example A — Full Clinical Scenario

```
Tú: Revisa mi perfil (soy PAC-1092). Quiero sustituir los 150g de salmón de mi dieta 
    porque tengo alergia. ¿Hay omega-3 disponible en zona 10?
```

The chatbot will automatically:
1. Call `consultar_perfil_paciente("PAC-1092")` → retrieves allergies (shellfish, dairy)
2. Call `buscar_equivalencia_macronutrientes("Salmón Atlántico", 150)` → finds safe alternatives
3. Call `verificar_inventario_suplementos("omega_3", "zona_10")` → confirms 12 units in stock
4. Synthesize a personalized, allergy-safe recommendation.

### Example B — Inspect MCP Log

```
Tú: logs
```

Displays a formatted table with all JSON-RPC interactions (method, status, timestamp).

### Example C — General Nutrition Question

```
Tú: ¿Cuánta proteína necesito si peso 80kg y quiero ganar músculo?
```

Answered directly from the LLM knowledge base (no tool calls needed).

### Example D — File System Interaction

```
Tú: Lee el archivo README.md y dame un resumen de 3 puntos.
```

The Filesystem MCP server reads the file and the LLM summarizes it.

### Example E — Filesystem + Git Combined Workflow

```
Tú: Crea un archivo NOTES.md con el texto "Reunión de nutricionistas - pendiente revisar plan de PAC-1092", 
    agrégalo al repositorio git y haz un commit con el mensaje "docs: add nutritionist meeting notes".
```

The chatbot will automatically:
1. Call the Filesystem server's `write_file` to create `NOTES.md`.
2. Call the Git server's `git_add` to stage the new file.
3. Call the Git server's `git_commit` to record the change.
4. Confirm the result (e.g., by calling `git_status` or `git_log`).

This demonstrates the scenario suggested by the course guidelines: using the chatbot to create a file, add it to a repository, and commit it — combining two official MCP servers (Filesystem and Git) in a single orchestrated flow.

---

## 8. Database

The simulated clinical database contains **real nutritional data** sourced from:
- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [Open Food Facts](https://world.openfoodfacts.org/)

| File | Records | Description |
|---|---|---|
| `src/server/data/alimentos.csv` | **120 foods** | 12 categories: fish, poultry, meat, dairy, legumes, grains, vegetables, fruits, nuts, seeds, oils, supplements |
| `src/server/data/pacientes.json` | **7 patients** | Full clinical profiles: BMI, allergies, conditions, medications, daily caloric plan |
| `src/server/data/inventario.json` | **5 branches** | Supplement stock per clinic (zona_1, zona_10, zona_14, mixco, antigua_guatemala) |

---

## 9. Project Structure

```
nutrition-mcp-server/
├── .env                          # API keys (NOT committed to git)
├── .gitignore                    # Excludes .env, venv/, logs
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── run.sh                        # Automated startup script
├── setup_data.py                 # Database generator script
└── src/
    ├── client/
    │   ├── chatbot.py            # Host: TokenRouter/Qwen API orchestrator & UI
    │   ├── mcp_client.py         # JSON-RPC 2.0 client (manual implementation)
    │   └── logger.py             # MCP interaction logger (rich tables)
    └── server/
        ├── mcp_server.py         # Custom Nutritional MCP Server (JSON-RPC 2.0)
        └── data/
            ├── alimentos.csv     # 120 foods — nutritional values (USDA-based)
            ├── pacientes.json    # 7 patient clinical profiles
            └── inventario.json   # Supplement inventory (5 clinic branches)
```

---
