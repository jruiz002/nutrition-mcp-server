import csv
import json
import os
import random

# Ensure the data directory exists
os.makedirs('src/server/data', exist_ok=True)

def generar_alimentos_csv():
    # Abundant dataset of foods, focused on common diets and nutrition
    alimentos = [
        {"id": "AL-001", "nombre": "Salmón", "categoria": "pescado", "proteina_g": 20.0, "carbohidratos_g": 0.0, "grasa_g": 13.0, "kcal": 208, "alergeno": "pescado"},
        {"id": "AL-002", "nombre": "Pechuga de Pollo", "categoria": "aves", "proteina_g": 31.0, "carbohidratos_g": 0.0, "grasa_g": 3.6, "kcal": 165, "alergeno": "ninguno"},
        {"id": "AL-003", "nombre": "Pavo Magro", "categoria": "aves", "proteina_g": 29.0, "carbohidratos_g": 0.0, "grasa_g": 2.0, "kcal": 135, "alergeno": "ninguno"},
        {"id": "AL-004", "nombre": "Huevos", "categoria": "lacteos_huevos", "proteina_g": 13.0, "carbohidratos_g": 1.1, "grasa_g": 11.0, "kcal": 155, "alergeno": "huevo"},
        {"id": "AL-005", "nombre": "Tofu", "categoria": "vegetariano", "proteina_g": 16.0, "carbohidratos_g": 1.9, "grasa_g": 8.7, "kcal": 144, "alergeno": "soya"},
        {"id": "AL-006", "nombre": "Lentejas", "categoria": "legumbres", "proteina_g": 9.0, "carbohidratos_g": 20.0, "grasa_g": 0.4, "kcal": 116, "alergeno": "ninguno"},
        {"id": "AL-007", "nombre": "Arroz Integral", "categoria": "cereales", "proteina_g": 2.6, "carbohidratos_g": 23.0, "grasa_g": 0.9, "kcal": 111, "alergeno": "ninguno"},
        {"id": "AL-008", "nombre": "Avena", "categoria": "cereales", "proteina_g": 16.9, "carbohidratos_g": 66.3, "grasa_g": 6.9, "kcal": 389, "alergeno": "gluten_traza"},
        {"id": "AL-009", "nombre": "Atún en Agua", "categoria": "pescado", "proteina_g": 25.5, "carbohidratos_g": 0.0, "grasa_g": 0.8, "kcal": 116, "alergeno": "pescado"},
        {"id": "AL-010", "nombre": "Leche Entera", "categoria": "lacteos", "proteina_g": 3.2, "carbohidratos_g": 4.8, "grasa_g": 3.3, "kcal": 61, "alergeno": "lacteos"},
        {"id": "AL-011", "nombre": "Leche de Almendras", "categoria": "vegetariano", "proteina_g": 0.4, "carbohidratos_g": 0.1, "grasa_g": 1.1, "kcal": 13, "alergeno": "frutos_secos"},
        {"id": "AL-012", "nombre": "Yogur Griego", "categoria": "lacteos", "proteina_g": 10.0, "carbohidratos_g": 3.6, "grasa_g": 0.4, "kcal": 59, "alergeno": "lacteos"},
        {"id": "AL-013", "nombre": "Carne de Res Magra", "categoria": "carnes", "proteina_g": 26.0, "carbohidratos_g": 0.0, "grasa_g": 15.0, "kcal": 250, "alergeno": "ninguno"},
        {"id": "AL-014", "nombre": "Camarones", "categoria": "mariscos", "proteina_g": 24.0, "carbohidratos_g": 0.2, "grasa_g": 0.3, "kcal": 99, "alergeno": "mariscos"},
        {"id": "AL-015", "nombre": "Frijoles Negros", "categoria": "legumbres", "proteina_g": 21.0, "carbohidratos_g": 62.0, "grasa_g": 0.9, "kcal": 341, "alergeno": "ninguno"},
        {"id": "AL-016", "nombre": "Pasta de Trigo", "categoria": "cereales", "proteina_g": 14.0, "carbohidratos_g": 75.0, "grasa_g": 1.5, "kcal": 371, "alergeno": "gluten"},
        {"id": "AL-017", "nombre": "Espinaca", "categoria": "verduras", "proteina_g": 2.9, "carbohidratos_g": 3.6, "grasa_g": 0.4, "kcal": 23, "alergeno": "ninguno"},
        {"id": "AL-018", "nombre": "Brócoli", "categoria": "verduras", "proteina_g": 2.8, "carbohidratos_g": 6.6, "grasa_g": 0.4, "kcal": 34, "alergeno": "ninguno"},
        {"id": "AL-019", "nombre": "Nueces", "categoria": "frutos_secos", "proteina_g": 15.0, "carbohidratos_g": 14.0, "grasa_g": 65.0, "kcal": 654, "alergeno": "frutos_secos"},
        {"id": "AL-020", "nombre": "Manzana", "categoria": "frutas", "proteina_g": 0.3, "carbohidratos_g": 14.0, "grasa_g": 0.2, "kcal": 52, "alergeno": "ninguno"},
        {"id": "AL-021", "nombre": "Plátano", "categoria": "frutas", "proteina_g": 1.1, "carbohidratos_g": 22.8, "grasa_g": 0.3, "kcal": 89, "alergeno": "ninguno"}
    ]

    # Generate more data dynamically to make it "abundante" as requested.
    bases = ["Cerdo", "Pavo", "Queso", "Crema", "Mantequilla", "Garbanzo", "Quinoa", "Chía", "Cacahuate", "Pan"]
    tipos = ["Premium", "Magro", "Integral", "Blanco", "Sano", "Orgánico"]
    alergenos = ["ninguno", "gluten", "lacteos", "frutos_secos", "soya"]
    
    for i in range(22, 101):
        base = random.choice(bases)
        tipo = random.choice(tipos)
        alimentos.append({
            "id": f"AL-{i:03d}",
            "nombre": f"{base} {tipo}",
            "categoria": "variado",
            "proteina_g": round(random.uniform(0.5, 30.0), 1),
            "carbohidratos_g": round(random.uniform(0.0, 80.0), 1),
            "grasa_g": round(random.uniform(0.0, 50.0), 1),
            "kcal": random.randint(50, 500),
            "alergeno": random.choice(alergenos)
        })

    with open('src/server/data/alimentos.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "nombre", "categoria", "proteina_g", "carbohidratos_g", "grasa_g", "kcal", "alergeno"])
        writer.writeheader()
        writer.writerows(alimentos)
    print("✓ Generado alimentos.csv (100 registros)")

def generar_pacientes_json():
    pacientes = {
        "PAC-1092": {
            "nombre": "Juan Pérez",
            "edad": 35,
            "imc": 26.5,
            "condiciones_medicas": ["resistencia_a_la_insulina"],
            "alergias": ["mariscos", "lacteos"],
            "objetivo": "Reducción de grasa"
        },
        "PAC-1093": {
            "nombre": "María Gonzalez",
            "edad": 28,
            "imc": 22.1,
            "condiciones_medicas": [],
            "alergias": ["gluten"],
            "objetivo": "Mantenimiento"
        },
        "PAC-1094": {
            "nombre": "Carlos López",
            "edad": 45,
            "imc": 31.0,
            "condiciones_medicas": ["hipertension"],
            "alergias": ["frutos_secos"],
            "objetivo": "Pérdida de peso"
        }
    }
    with open('src/server/data/pacientes.json', 'w', encoding='utf-8') as f:
        json.dump(pacientes, f, indent=4, ensure_ascii=False)
    print("✓ Generado pacientes.json")

def generar_inventario_json():
    inventario = {
        "zona_10": {
            "omega_3": {"disponible": 12, "precio": 150.0},
            "proteina_suero": {"disponible": 5, "precio": 450.0},
            "vitamina_c": {"disponible": 20, "precio": 80.0}
        },
        "zona_14": {
            "omega_3": {"disponible": 0, "precio": 150.0},
            "proteina_suero": {"disponible": 15, "precio": 450.0},
            "vitamina_c": {"disponible": 50, "precio": 80.0},
            "creatina": {"disponible": 8, "precio": 300.0}
        }
    }
    with open('src/server/data/inventario.json', 'w', encoding='utf-8') as f:
        json.dump(inventario, f, indent=4, ensure_ascii=False)
    print("✓ Generado inventario.json")

if __name__ == "__main__":
    generar_alimentos_csv()
    generar_pacientes_json()
    generar_inventario_json()
    print("Base de datos simulada creada exitosamente.")
