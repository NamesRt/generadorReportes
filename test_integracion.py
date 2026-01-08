"""
Script de prueba de integración completa del sistema
Simula el flujo completo: AD -> Responsable -> Gerente
"""
import csv
from testChain import load_hierarchy_data, get_superior, normalize_text

print("=" * 80)
print("PRUEBA DE INTEGRACION COMPLETA DEL SISTEMA")
print("=" * 80)

# 1. Cargar jerarquía desde regs.csv
print("\n1. Cargando jerarquia desde regs.csv...")
try:
    from testChain import mapping
    mapping_test, _, _, _ = load_hierarchy_data("regs.csv", fam_puesto_col=7, division_col=11)
    print(f"   OK - {len(mapping_test)} puestos cargados")
except Exception as e:
    print(f"   ERROR: {e}")
    exit(1)

# 2. Leer archivo de registros de prueba
print("\n2. Leyendo archivo regs_test.csv...")
personas = []
try:
    with open("regs_test.csv", mode='r', newline='', encoding="utf-8", errors='replace') as file:
        reader = csv.reader(file, delimiter=';')
        next(reader, None)  # Saltar encabezado
        
        for row in reader:
            if len(row) > 25:
                persona = {
                    "codigo": row[25],
                    "nombre": row[1],
                    "apellido": row[2],
                    "puesto": row[7],
                    "division": row[11],
                    "email": row[34]
                }
                personas.append(persona)
    print(f"   OK - {len(personas)} personas encontradas")
except FileNotFoundError:
    print("   ADVERTENCIA: regs_test.csv no encontrado, generando datos de ejemplo...")
    personas = [
        {"codigo": "S12345", "nombre": "Juan", "apellido": "Perez", "puesto": "ANALISTA DE PRODUCTO VALUE PROPOSITION", "division": "DIV. BANCA NEGOCIOS", "email": "juan.perez@empresa.com"},
        {"codigo": "B23456", "nombre": "Maria", "apellido": "Garcia", "puesto": "JEFE DE PRODUCTO", "division": "DIV. BANCA NEGOCIOS", "email": "maria.garcia@empresa.com"},
        {"codigo": "S34567", "nombre": "Carlos", "apellido": "Lopez", "puesto": "SUBGERENTE DE PRODUCTOS", "division": "DIV. BANCA NEGOCIOS", "email": "carlos.lopez@empresa.com"},
        {"codigo": "S45678", "nombre": "Ana", "apellido": "Martinez", "puesto": "SCRUM MASTER", "division": "TRIBU CANALES DIGITALES Y PRODUCTOS", "email": "ana.martinez@empresa.com"},
        {"codigo": "B56789", "nombre": "Pedro", "apellido": "Rodriguez", "puesto": "SOFTWARE ENGINEER", "division": "DIV. TRANSFORMACION DATA ANALYTICS", "email": "pedro.rodriguez@empresa.com"},
    ]
    print(f"   OK - {len(personas)} personas de ejemplo creadas")

# 3. Probar búsqueda de superiores
print("\n3. Probando busqueda de superiores jerarquicos...")
print("\n" + "=" * 80)

resultados = []
for persona in personas[:10]:  # Probar primeros 10
    puesto = persona["puesto"]
    division = persona["division"]
    
    # Buscar superior usando testChain
    superior_puesto, superior_division = get_superior(puesto, division)
    
    # Buscar persona con ese puesto superior en el archivo
    gerente_encontrado = None
    if superior_puesto:
        superior_norm = normalize_text(superior_puesto) if isinstance(superior_puesto, str) else superior_puesto
        for p in personas:
            p_puesto_norm = normalize_text(p["puesto"])
            p_div_norm = normalize_text(p["division"]) if p["division"] else None
            
            # Verificar coincidencia de puesto
            if superior_norm == p_puesto_norm or superior_norm in p_puesto_norm:
                # Verificar división si está especificada
                if superior_division:
                    superior_div_norm = normalize_text(superior_division)
                    if p_div_norm == superior_div_norm:
                        gerente_encontrado = p
                        break
                else:
                    gerente_encontrado = p
                    break
    
    resultado = {
        "persona": persona,
        "superior_puesto": superior_puesto,
        "superior_division": superior_division,
        "gerente_encontrado": gerente_encontrado
    }
    resultados.append(resultado)

# 4. Mostrar resultados
exitos = 0
parciales = 0
fallos = 0

for i, res in enumerate(resultados):
    persona = res["persona"]
    print(f"\n{i+1}. {persona['nombre']} {persona['apellido']} ({persona['codigo']})")
    print(f"   Puesto: {persona['puesto']}")
    print(f"   Division: {persona['division']}")
    
    if res["superior_puesto"]:
        print(f"   -> Superior jerarquico: {res['superior_puesto']}")
        if res["superior_division"]:
            print(f"      Division: {res['superior_division']}")
        
        if res["gerente_encontrado"]:
            g = res["gerente_encontrado"]
            print(f"   [OK] Gerente encontrado en archivo:")
            print(f"        {g['nombre']} {g['apellido']} ({g['codigo']})")
            print(f"        Email: {g['email']}")
            exitos += 1
        else:
            print(f"   [PARCIAL] Superior identificado pero no hay persona con ese puesto en archivo")
            parciales += 1
    else:
        print(f"   [FALLO] No se identifico superior jerarquico")
        fallos += 1

# 5. Resumen
print("\n" + "=" * 80)
print("RESUMEN DE INTEGRACION")
print("=" * 80)
print(f"Total de pruebas: {len(resultados)}")
print(f"  - Exitos completos (superior + gerente encontrado): {exitos}")
print(f"  - Parciales (superior identificado, gerente no en archivo): {parciales}")
print(f"  - Fallos (no se identifico superior): {fallos}")

tasa_exito = ((exitos + parciales) / len(resultados) * 100) if resultados else 0
print(f"\nTasa de identificacion de superiores: {tasa_exito:.1f}%")

# 6. Prueba de funciones de main.py
print("\n" + "=" * 80)
print("PRUEBA DE FUNCIONES DE MAIN.PY")
print("=" * 80)

try:
    from res import buscarCampoCodigo, buscarGerentePorPuestoYDivision
    
    # Simular búsqueda de responsable
    print("\n1. Probando buscarCampoCodigo...")
    if personas:
        codigo_prueba = personas[0]["codigo"]
        print(f"   Buscando codigo: {codigo_prueba}")
        resultado = buscarCampoCodigo("regs_test.csv", codigo_prueba)
        print(f"   Resultado: {resultado}")
        if resultado[0] != "N/A":
            print("   OK - Funcion operativa")
        else:
            print("   ADVERTENCIA - No se encontro el codigo")
    
    # Simular búsqueda de gerente
    print("\n2. Probando buscarGerentePorPuestoYDivision...")
    if resultados[0]["superior_puesto"]:
        puesto_sup = normalize_text(resultados[0]["superior_puesto"])
        div_sup = normalize_text(resultados[0]["superior_division"]) if resultados[0]["superior_division"] else None
        print(f"   Buscando puesto: {puesto_sup}")
        print(f"   En division: {div_sup}")
        gerente = buscarGerentePorPuestoYDivision("regs_test.csv", puesto_sup, div_sup)
        print(f"   Resultado: {gerente}")
        if gerente[0] != "N/A":
            print("   OK - Funcion operativa")
        else:
            print("   ADVERTENCIA - No se encontro gerente con ese puesto")

except ImportError as e:
    print(f"   ERROR al importar main.py: {e}")
except FileNotFoundError:
    print("   ADVERTENCIA: regs_test.csv no encontrado para pruebas de busqueda")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 80)
print("FIN DE PRUEBAS DE INTEGRACION")
print("=" * 80)
