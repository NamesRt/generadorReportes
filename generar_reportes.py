"""
Script de prueba directo para generar reportes
"""
from res import load_csv
import os

print("=" * 80)
print("GENERANDO REPORTES DE ENERO 2026")
print("=" * 80)

# Archivos de entrada
ad_file = "AD-06-01-26.csv"
regs_file = "regs.csv"

# Verificar que existan
if not os.path.exists(ad_file):
    print(f"ERROR: No se encuentra el archivo {ad_file}")
    exit(1)

if not os.path.exists(regs_file):
    print(f"ERROR: No se encuentra el archivo {regs_file}")
    exit(1)

print(f"\nArchivo AD: {ad_file}")
print(f"Archivo Registros: {regs_file}")
print(f"Mes: Enero")
print(f"Año: 2026")

print("\n" + "=" * 80)
print("PROCESANDO...")
print("=" * 80 + "\n")

# Generar reportes
load_csv(ad_file, regs_file, "Enero", "2026")

print("\n" + "=" * 80)
print("PROCESO COMPLETADO")
print("=" * 80)
