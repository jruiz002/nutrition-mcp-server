import sys
import json
import csv
import os

# Server paths for data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def load_json(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_csv(filename):
    filepath = os.path.join(DATA_DIR, filename)
    data = []
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    return data

def consultar_perfil_paciente(paciente_id):
    pacientes = load_json('pacientes.json')
    if paciente_id in pacientes:
        return pacientes[paciente_id]
    return {"error": f"Paciente {paciente_id} no encontrado."}

def buscar_equivalencia_macronutrientes(alimento_origen, gramos):
    alimentos = load_csv('alimentos.csv')
    
    if not alimento_origen:
        return {"error": "Falta el parámetro 'alimento_origen'."}
    if gramos is None:
        return {"error": "Falta el parámetro 'gramos'."}
        
    # Buscar el alimento original (match parcial)
    origen = None
    for a in alimentos:
        if alimento_origen.lower() in a['nombre'].lower():
            origen = a
            break
            
    if not origen:
        return {"error": f"Alimento '{alimento_origen}' no encontrado en la base de datos."}
        
    try:
        gramos = float(gramos)
        prot_origen_total = (float(origen['proteina_g']) / 100.0) * gramos
        carb_origen_total = (float(origen['carbohidratos_g']) / 100.0) * gramos
        grasa_origen_total = (float(origen['grasa_g']) / 100.0) * gramos
    except ValueError:
        return {"error": "El parámetro 'gramos' debe ser numérico."}
        
    # Buscar posibles sustitutos basados principalmente en proteína
    sustitutos = []
    for a in alimentos:
        if a['nombre'] != origen['nombre']:
            try:
                prot_a = float(a['proteina_g'])
                if prot_a > 5.0: # Focus on protein sources
                    # Cuantos gramos de 'a' se necesitan para igualar prot_origen_total
                    gramos_necesarios = (prot_origen_total * 100.0) / prot_a
                    if gramos_necesarios > 0 and gramos_necesarios < 500: # Reasonable portions
                        sustitutos.append({
                            "nombre": a['nombre'],
                            "gramos_sugeridos": round(gramos_necesarios, 1),
                            "alergeno": a['alergeno']
                        })
            except ValueError:
                continue
                
    # Sort and return top 3 closest in reasonable grams
    sustitutos.sort(key=lambda x: abs(x['gramos_sugeridos'] - gramos))
    return {
        "alimento_original": origen['nombre'],
        "gramos_original": gramos,
        "macronutrientes_aportados": {
            "proteina_g": round(prot_origen_total, 1),
            "carbohidratos_g": round(carb_origen_total, 1),
            "grasa_g": round(grasa_origen_total, 1)
        },
        "opciones_equivalentes": sustitutos[:3]
    }

def verificar_inventario_suplementos(categoria_producto, sucursal):
    inventario = load_json('inventario.json')
    if sucursal not in inventario:
        return {"error": f"Sucursal '{sucursal}' no encontrada."}
        
    sucursal_inv = inventario[sucursal]
    if categoria_producto not in sucursal_inv:
        return {"error": f"Producto '{categoria_producto}' no encontrado en {sucursal}."}
        
    return {
        "sucursal": sucursal,
        "producto": categoria_producto,
        "disponibilidad": sucursal_inv[categoria_producto]
    }


def send_response(response_dict):
    """Escribe la respuesta en formato JSON-RPC al stdout y hace flush."""
    sys.stdout.write(json.dumps(response_dict) + "\n")
    sys.stdout.flush()

def handle_initialize(request):
    """Maneja la petición de inicialización del protocolo MCP."""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "nutritional-mcp-server",
                "version": "1.0.0"
            }
        }
    }

def handle_tools_list(request):
    """Devuelve la lista de herramientas disponibles."""
    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "tools": [
                {
                    "name": "consultar_perfil_paciente",
                    "description": "Consulta el expediente de un paciente usando su ID (ej. PAC-1092). Retorna información de alergias y condiciones.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "paciente_id": {
                                "type": "string",
                                "description": "El ID del paciente."
                            }
                        },
                        "required": ["paciente_id"]
                    }
                },
                {
                    "name": "buscar_equivalencia_macronutrientes",
                    "description": "Encuentra sustitutos de alimentos que aporten cantidades similares de proteína.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "alimento_origen": {
                                "type": "string",
                                "description": "El nombre del alimento a sustituir (ej. 'Salmón')."
                            },
                            "gramos": {
                                "type": "number",
                                "description": "Gramos del alimento origen."
                            }
                        },
                        "required": ["alimento_origen", "gramos"]
                    }
                },
                {
                    "name": "verificar_inventario_suplementos",
                    "description": "Verifica si hay stock de un suplemento en una sucursal específica.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "categoria_producto": {
                                "type": "string",
                                "description": "El id o categoria del producto (ej. omega_3, proteina_suero)."
                            },
                            "sucursal": {
                                "type": "string",
                                "description": "El nombre de la sucursal (ej. zona_10, zona_14)."
                            }
                        },
                        "required": ["categoria_producto", "sucursal"]
                    }
                }
            ]
        }
    }

def handle_tools_call(request):
    """Ejecuta la herramienta solicitada."""
    params = request.get("params", {})
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})
    
    result = None
    is_error = False

    if tool_name == "consultar_perfil_paciente":
        pid = tool_args.get("paciente_id") or tool_args.get("id_paciente")
        if not pid:
            result = "Error: Falta el parámetro 'paciente_id'."
        else:
            result = consultar_perfil_paciente(pid)
    elif tool_name == "buscar_equivalencia_macronutrientes":
        ao = tool_args.get("alimento_origen") or tool_args.get("alimento") or tool_args.get("alimento_base")
        g = tool_args.get("gramos") or tool_args.get("cantidad_gramos") or tool_args.get("cantidad")
        result = buscar_equivalencia_macronutrientes(ao, g)
    elif tool_name == "verificar_inventario_suplementos":
        result = verificar_inventario_suplementos(tool_args.get("categoria_producto"), tool_args.get("sucursal"))
    else:
        is_error = True
        result = f"Tool '{tool_name}' no existe."

    if isinstance(result, dict) and "error" in result:
        is_error = True
        result = result["error"]

    return {
        "jsonrpc": "2.0",
        "id": request.get("id"),
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                }
            ],
            "isError": is_error
        }
    }

def main():
    """Bucle principal del servidor que lee de stdin."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line)
            method = request.get("method")
            
            if method == "initialize":
                response = handle_initialize(request)
                send_response(response)
            elif method == "notifications/initialized":
                # No response needed for notifications
                pass
            elif method == "ping":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {}
                }
                send_response(response)
            elif method == "tools/list":
                response = handle_tools_list(request)
                send_response(response)
            elif method == "tools/call":
                response = handle_tools_call(request)
                send_response(response)
            else:
                # Handle unknown method if it's not a notification
                if "id" in request:
                    send_response({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method {method} not found"
                        }
                    })
                    
        except json.JSONDecodeError:
            # Handle parsing error (only if it wasn't an empty line)
            if line.strip():
                send_response({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                })
        except Exception as e:
            # Handle other errors
            if "request" in locals() and "id" in request:
                send_response({
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                })

if __name__ == "__main__":
    main()
