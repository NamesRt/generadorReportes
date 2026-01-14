"""
Script de prueba para validar la nueva implementación del Trie
"""
from testChain import load_hierarchy_data, get_superior, normalize_text

print("=" * 80)
print("PRUEBA DE JERARQUÍA CON TRIE")
print("=" * 80)

# Cargar jerarquía
print("\n1. Cargando jerarquía...")
trie, mapping, puestos, divisiones = load_hierarchy_data("", 0, 0)
print("   ✓ Jerarquía cargada exitosamente")

# Casos de prueba
casos_prueba = [
    ("ANALISTA", "DIV. BANCA NEGOCIOS"),
    ("JEFE DE PRODUCTO", "DIV. TRANSFORMACION DATA ANALYTICS"),
    ("SOFTWARE ENGINEER", "TRIBU CANALES DIGITALES Y PRODUCTOS"),
    ("SCRUM MASTER", "DIV. AGILIDAD"),
    ("GERENTE DE DIVISION", "VP.RIESGOS"),
]

print("\n2. Probando búsqueda de superiores:")
print("=" * 80)

for i, (puesto, division) in enumerate(casos_prueba, 1):
    print(f"\n{i}. Puesto: {puesto}")
    print(f"   División: {division}")
    
    puesto_superior, division_superior = get_superior(puesto, division)
    
    if puesto_superior:
        print(f"   ✓ Superior encontrado: {puesto_superior}")
        print(f"     En división: {division_superior}")
    else:
        print(f"   ✗ No se encontró superior en la jerarquía")

print("\n" + "=" * 80)
print("PRUEBA COMPLETADA")
print("=" * 80)
