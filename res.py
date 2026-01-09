import csv
import re
import os
from datetime import datetime
from collections import defaultdict
from testChain import load_hierarchy_data, get_superior, normalize_text

"""
SamAccountName: Seleccionar solo cuentas X
Enabled: True
Description: Extraer codigo del responsable
Agrupar por mes de expiracion de contraseñas

Usuario de red: 25
Nombre: 1
A.pat: 2
A.mat: 3
E-mail: 34
Division: 11
Fam. Puesto: 7
"""

# Variables globales para la jerarquía
hierarchy_mapping = None

def buscarCampoCodigo(Regs_File, codigo):
    """Busca un código en el archivo de registros y retorna sus datos."""
    with open(Regs_File, mode='r', newline='', encoding="utf-8", errors='replace') as file:
        reader = csv.reader(file, delimiter=';')
        # Saltar encabezado si existe
        next(reader, None)
        
        for row in reader:
            if len(row) > 25 and row[25] == codigo:
                # Retornar: Nombre, A.pat, A.mat, E-mail, Division, Fam. Puesto
                return [row[i] if i < len(row) else "" for i in (1, 2, 3, 34, 11, 7)]
    return ["N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]

def buscarGerentePorPuestoYDivision(Regs_File, puesto_norm, division_norm):
    """Busca un gerente en el archivo de registros por puesto y división normalizados."""
    with open(Regs_File, mode='r', newline='', encoding="utf-8", errors='replace') as file:
        reader = csv.reader(file, delimiter=';')
        header = next(reader, None)
        
        for row in reader:
            if len(row) > 25:
                # Normalizar puesto y división de la fila actual
                puesto_actual = normalize_text(row[7]) if len(row) > 7 else ""
                division_actual = normalize_text(row[11]) if len(row) > 11 else ""
                
                # Si hay coincidencia exacta de puesto
                if puesto_norm and puesto_actual == puesto_norm:
                    # Si también se especifica división, verificar coincidencia
                    if division_norm is None or division_actual == division_norm:
                        # Retornar: Codigo, Nombre, A.pat, A.mat, E-mail
                        codigo = row[25] if len(row) > 25 else "N/A"
                        return [codigo, row[1] if len(row) > 1 else "N/A",  
                               row[2] if len(row) > 2 else "N/A",
                               row[3] if len(row) > 3 else "N/A",
                               row[34] if len(row) > 34 else "N/A"]
    
    return ["N/A", "N/A", "N/A", "N/A", "N/A"]

def load_csv(AD_File, Regs_File, mes, anio=None):
    global hierarchy_mapping
    
    # Cargar jerarquía desde el mismo archivo Regs usando índices 7 y 11
    if hierarchy_mapping is None:
        try:
            hierarchy_mapping, _, _, _ = load_hierarchy_data(Regs_File, fam_puesto_col=7, division_col=11)
            print(f"Jerarquía cargada desde {Regs_File}")
        except Exception as e:
            print(f"No se pudo cargar la jerarquía: {e}")
            hierarchy_mapping = {}
    
    datos_por_mes = defaultdict(list)
    
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    
    with open(AD_File, mode='r', newline='', encoding="utf-8", errors='replace') as file:
        reader = csv.reader(file, delimiter=';')
        for row in reader:
            usCod = row[0]
            dispName = row[4]
            enabled = row[14]
            expiration = row[22]
            creation = row[18]
            
            # Filtrar cuentas X habilitadas
            if (usCod.startswith("X") and any(c.isdigit() for c in usCod)) and enabled == "True":
                # Obtener fecha de expiracion de la cuenta primero para filtrar
                account_expires = expiration
                mes_key = "Sin_fecha"
                fecha = None
                
                if account_expires and account_expires != "":
                    try:
                        fecha = datetime.strptime(account_expires.split()[0], "%d/%m/%Y")
                        mes_nombre = meses[fecha.month]
                        mes_key = f"{mes_nombre}{fecha.year}"
                    except:
                        mes_key = "Sin_fecha"
                
                # Filtrar por mes y año si están especificados
                if mes and not mes_key.startswith(mes):
                    continue
                
                if anio and fecha:
                    if fecha.year != int(anio):
                        continue
                elif anio and not fecha:
                    # Si se especificó año pero no hay fecha válida, saltar
                    continue
                
                # Extraer codigo del responsable de la descripcion
                desc = row[7]
                if "Resp" in desc:
                    parts = re.split(r'[ |,.\-:]+', desc)
                    respCod = row[7]
                    for part in parts:
                        if (part.startswith("S") or part.startswith("B") or part.startswith("b") or part.startswith("s")) and any(c.isdigit() for c in part):
                            respCod = part
                            break
                
                data = buscarCampoCodigo(Regs_File, respCod)
                nombre = data[0]
                aPat = data[1]
                aMat = data[2]
                correo = data[3]
                division = data[4]
                puesto = data[5]
                
                # Buscar al gerente del responsable
                gerente_codigo = "N/A"
                gerente_nombre = "N/A"
                gerente_correo = "N/A"
                
                if puesto != "N/A" and puesto != "":  # Si hay puesto del responsable
                    puesto_responsable = puesto
                    division_responsable = division
                    
                    # Obtener el superior usando la jerarquía
                    puesto_superior_norm, division_superior = get_superior(puesto_responsable, division_responsable)
                    
                    if puesto_superior_norm:
                        # Buscar al gerente en el archivo de registros
                        gerente_data = buscarGerentePorPuestoYDivision(Regs_File, puesto_superior_norm, division_superior)
                        if gerente_data[0] != "N/A":
                            gerente_codigo = gerente_data[0]
                            gerente_nombre = gerente_data[1] + " " + gerente_data[2] + " " + gerente_data[3]
                            gerente_correo = gerente_data[4]

                # Almacenar registro
                datos_por_mes[mes_key].append({
                    "SamAccountName": usCod,
                    "DisplayName": dispName,
                    "Responsable": respCod,
                    "NombreResponsable": nombre + " " + aPat + " " + aMat,
                    "CorreoResponsable": correo,
                    "Division": division,
                    "Gerente": gerente_codigo,
                    "NombreGerente": gerente_nombre,
                    "CorreoGerente": gerente_correo,
                    "Enabled": enabled,
                    "whenCreated": creation,
                    "AccountExpires": expiration
                })
                
                print("SamAccountName: {} - DisplayName: {} - Responsable: {} - NombreResponsable: {} - CorreoResponsable: {} - Division: {} - Enabled: {} - whenCreated: {} - AccountExpires: {}".format(
                    usCod, dispName, respCod, nombre + " " + aPat + " " + aMat, correo, division, enabled, creation, expiration
                ))

    output_dir = "reportes" + (mes if mes else "") + (str(anio) if anio else "")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generar archivos CSV con los datos filtrados
    archivos_generados = 0
    for mes_key, datos in datos_por_mes.items():
        nombre_archivo = os.path.join(output_dir, f"{mes_key}.csv")
        with open(nombre_archivo, mode='w', newline='', encoding="utf-8") as csv_file:
            fieldnames = ["SamAccountName", "DisplayName", "Responsable", "NombreResponsable", "CorreoResponsable", "Gerente", "NombreGerente", "CorreoGerente", "Division", "Enabled", "whenCreated", "AccountExpires"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=';')
            
            writer.writeheader()
            writer.writerows(datos)
        
        print(f"\nArchivo creado: {nombre_archivo} con {len(datos)} registros")
        archivos_generados += 1
    
    # Verificar si se generaron archivos
    if archivos_generados == 0:
        filtro_texto = []
        if mes:
            filtro_texto.append(f"mes de {mes}")
        if anio:
            filtro_texto.append(f"año {anio}")
        filtro_str = " y ".join(filtro_texto) if filtro_texto else "los criterios especificados"
        mensaje = f"\nNo se encontraron registros para {filtro_str}"
        print(mensaje)
        raise ValueError(f"No se encontraron registros para {filtro_str}")
    return output_dir

if __name__ == "__main__":
    AD_File = "AD-06-01-26.csv"
    Regs_File = "awa1.csv"
    mes = "Enero"

    dirName = load_csv(AD_File, Regs_File, mes)
