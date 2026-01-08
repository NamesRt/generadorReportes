# ejemplo: helper_hierarchy_example.py
import csv
import unicodedata
import re
from difflib import get_close_matches
from collections import defaultdict

def normalize_text(s):
    if not s or s == "": return ""
    s = str(s).upper().strip()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def load_hierarchy_data(csv_file, fam_puesto_col=7, division_col=11):
    """
    Carga y procesa el archivo CSV con la jerarquía de puestos.
    Por defecto usa índices 7 (Fam. Puesto) y 11 (Division) para regs.csv

    Args:
        csv_file: Ruta al archivo CSV
        fam_puesto_col: Índice de columna para Fam. Puesto (default: 7)
        division_col: Índice de columna para Division (default: 11)

    Returns:
        mapping: dict original_puesto -> info (puesto_norm, division_norm, superior_norm, superior_division)
        division_titles: dict division_norm -> list of (puesto_norm, rank)
        global_titles: list of (puesto_norm, rank)
        infer_rank: function(title_norm) -> int
    """
    # -----------------------------
    # 1) Leer CSV
    # -----------------------------
    data = []
    with open(csv_file, mode='r', newline='', encoding="utf-8", errors='replace') as file:
        reader = csv.reader(file, delimiter=';')
        header = next(reader, None)  # Saltar encabezado

        for row in reader:
            if len(row) > max(fam_puesto_col, division_col):
                fam_puesto = row[fam_puesto_col] if fam_puesto_col < len(row) else ""
                division = row[division_col] if division_col < len(row) else ""

                puesto_norm = normalize_text(fam_puesto)
                division_norm = normalize_text(division)

                if puesto_norm:  # Solo agregar si el puesto no está vacío
                    data.append({
                        "fam_puesto": fam_puesto,
                        "division": division,
                        "puesto_norm": puesto_norm,
                        "division_norm": division_norm
                    })

    # -----------------------------
    # 2) Heurísticas / ladders
    # -----------------------------
    # Jerarquía organizacional canonical (orden: 0 = más alto)
    ORG_HIERARCHY = [
        "CEO/CHIEF/CTO/COO/PRESIDENTE",
        "VP/SVP/DIRECCIÓN",
        "DIRECTOR",
        "HEAD",
        "GERENTE/MANAGER",
        "SUBDIRECTOR/SUBGERENTE",
        "JEFE/LEAD",
        "LÍDER/TEAM LEAD",
        "COORDINADOR",
        "SUPERVISOR",
        "EJECUTIVO/SPECIALIST",
        "ANALISTA",
        "ASISTENTE",
        "PRACTICANTE/INTERN"
    ]

    # Escalera técnica (de menor a mayor)
    TECH_LADDER = [
        "PRACTICANTE/INTERN",
        "JUNIOR",
        "MID/REGULAR",
        "SENIOR",
        "LEAD/TECH LEAD",
        "ENGINEERING MANAGER",
        "DIRECTOR ENGINEERING",
        "VP ENGINEERING",
        "CTO/CHIEF"
    ]

    # Mapeos por patrón a categoría canonical (EXPANDIDO)
    KEYWORD_TO_CATEGORY = {
        # C-Level
        r"\bCEO\b|\bCHIEF\b|\bCTO\b|\bCOO\b|\bPRESIDENTE\b": "CEO/CHIEF/CTO/COO/PRESIDENTE",
        r"\bVICE PRESIDENTE EJECUTIVO\b|\bVP\b|\bSVP\b": "VP/SVP/DIRECCIÓN",
        
        # Dirección
        r"\bDIRECTOR\b": "DIRECTOR",
        r"\bHEAD OFFICE\b|\bHEAD DE\b|\bHEAD\b": "HEAD",
        
        # Gerencia
        r"\bGERENTE CENTRAL\b": "GERENTE CENTRAL",
        r"\bGERENTE DE AREA\b": "GERENTE DE AREA",
        r"\bGERENTE ZONAL\b": "GERENTE ZONAL",
        r"\bGERENTE DE DIVISION\b": "GERENTE DE DIVISION",
        r"\bGERENTE TIENDA\b|\bGERENTE ASISTENTE\b": "GERENTE ASISTENTE",
        r"\bGERENTE\b|\bMANAGER\b": "GERENTE/MANAGER",
        
        # Sub-gerencia
        r"\bSUBDIRECTOR\b|\bSUBGERENTE\b": "SUBDIRECTOR/SUBGERENTE",
        
        # Jefatura
        r"\bJEFE ZONAL\b": "JEFE ZONAL",
        r"\bJEFE COMERCIAL\b": "JEFE COMERCIAL",
        r"\bJEFE\b|\bCHIEF OF\b": "JEFE/LEAD",
        r"\bTEAM MANAGER\b": "TEAM MANAGER",
        
        # Liderazgo
        r"\bLEAD DE\b|\bTEAM LEAD\b|\bTECH LEAD\b": "TEAM LEAD",
        r"\bLIDER DE\b|\bLÍDER\b|\bLIDER\b": "LÍDER/TEAM LEAD",
        
        # Coordinación y Supervisión
        r"\bCOORDINADOR\b": "COORDINADOR",
        r"\bSUPERVISOR\b": "SUPERVISOR",
        
        # Especialización Senior
        r"\bPRINCIPAL EXPERT\b": "PRINCIPAL EXPERT",
        r"\bPRINCIPAL LEAD\b|\bPRINCIPAL ENGINEER\b": "PRINCIPAL LEAD",
        r"\bPRINCIPAL\b": "PRINCIPAL",
        r"\bEXPERT\b": "EXPERT",
        r"\bSTRATEGIST\b": "STRATEGIST",
        r"\bADVISOR\b": "ADVISOR",
        
        # Roles Ágiles
        r"\bAGILE COACH\b": "AGILE COACH",
        r"\bSCRUM MASTER\b": "SCRUM MASTER",
        r"\bAGILE TEAM FACILITATOR\b": "AGILE TEAM FACILITATOR",
        
        # Roles de Arquitectura y Engineering
        r"\bBUSINESS ARCHITECT\b|\bTECHNOLOGY ARCHITECT\b|\bARCHITECT\b": "ARCHITECT",
        r"\bSOFTWARE TEST ENGINEER\b|\bSOFTWARE ENGINEER\b|\bENGINEER\b": "TECH_ROLE",
        r"\bDESARROLLADOR\b|\bDEVELOPER\b": "TECH_ROLE",
        
        # Roles de Data
        r"\bDATA SCIENTIST ADVISOR\b|\bDATA SCIENTIST EXPERT\b": "DATA SCIENTIST SENIOR",
        r"\bDATA SCIENTIST\b": "DATA SCIENTIST",
        r"\bDATA ENGINEER\b": "DATA ENGINEER",
        r"\bDATA ANALYST ADVISOR\b": "DATA ANALYST SENIOR",
        r"\bDATA ANALYST\b": "DATA ANALYST",
        
        # Roles de Product/Design
        r"\bPRODUCT DESIGNER\b|\bDESIGN LEAD\b": "DESIGN LEAD",
        r"\bDESIGNER\b|\bDESIGN\b": "DESIGNER",
        r"\bPRODUCT LEAD\b": "PRODUCT LEAD",
        r"\bPRODUCT\b": "PRODUCT",
        r"\bCONVERSATION DESIGNER\b|\bCONVERSATION DESIGN\b": "CONVERSATION DESIGNER",
        
        # Roles de Growth/Business
        r"\bGROWTH HACKER\b|\bGROWTH LEAD\b": "GROWTH LEAD",
        r"\bGROWTH\b": "GROWTH",
        r"\bBUSINESS DESIGNER\b|\bBUSINESS ARCHITECT\b": "BUSINESS DESIGNER",
        r"\bBUSINESS ANALYST\b": "BUSINESS ANALYST",
        r"\bBUSINESS\b": "BUSINESS",
        
        # Roles de Innovación
        r"\bINNOVATION PRINCIPAL LEAD\b": "INNOVATION LEAD",
        r"\bINNOVATION\b": "INNOVATION",
        
        # Especialistas
        r"\bSPECIALIST\b|\bESPECIALISTA\b": "SPECIALIST",
        
        # Ejecutivos y Analistas
        r"\bRELATIONSHIP MANAGER\b": "RELATIONSHIP MANAGER",
        r"\bEJECUTIVO\b|\bEXECUTIVE\b": "EJECUTIVO/SPECIALIST",
        r"\bANALISTA SR\b|\bANALISTA SENIOR\b": "ANALISTA SENIOR",
        r"\bANALISTA\b|\bANALYST\b": "ANALISTA",
        
        # Roles de Soporte
        r"\bGESTOR\b": "GESTOR",
        r"\bASESOR\b": "ASESOR",
        r"\bCAMPAIGN\b": "CAMPAIGN",
        r"\bASSOCIATE\b": "ASSOCIATE",
        r"\bASISTENTE\b|\bASSISTANT\b": "ASISTENTE",
        r"\bREPRESENTANTE\b": "REPRESENTANTE",
        r"\bTECNICO\b": "TECNICO",
        r"\bAUXILIAR\b": "AUXILIAR",
        
        # Entrada
        r"\bTRAINEE\b": "TRAINEE",
        r"\bPRACTICANTE\b|\bPRACTICAS\b|\bINTERN\b": "PRACTICANTE/INTERN",
        r"\bJUNIOR\b|\bJR\b": "JUNIOR",
        
        # Roles sin categoría clara
        r"\bCX\b": "CX",
        r"\bREAL TIME OPERATION\b": "REAL TIME OPERATION",
    }

    # Tokens de seniority
    SENIORITY_TOKENS = {
        r"\bPRACTICANTE\b|\bINTERN\b": "PRACTICANTE/INTERN",
        r"\bJUNIOR\b|\b JR\b|\bJR\b": "JUNIOR",
        r"\bMID\b|\bINTERMEDIATE\b": "MID/REGULAR",
        r"\bSENIOR\b|\b SR\b|\bSR\b": "SENIOR",
        r"\bLEAD\b|\bTECH LEAD\b|\bTEAM LEAD\b": "LEAD/TECH LEAD",
        r"\bPRINCIPAL\b": "LEAD/TECH LEAD",
        r"\bMANAGER\b|\bGERENTE\b": "ENGINEERING MANAGER",
        r"\bDIRECTOR\b": "DIRECTOR ENGINEERING",
        r"\bVP\b|\bVICE PRESIDENT\b": "VP ENGINEERING",
        r"\bCTO\b|\bCHIEF\b": "CTO/CHIEF"
    }

    # Heurística expandida de seniority (lista preferente; más alto primero)
    # Orden: 0 = más alto (CEO) ... N = más bajo (Practicante)
    seniority_keywords = [
        # C-Level y Alta Dirección (0-3)
        ("CEO", 0), ("CHIEF", 0), ("PRESIDENTE", 0),
        ("VICE PRESIDENTE EJECUTIVO", 1), ("VP", 1), ("SVP", 1),
        ("GERENTE CENTRAL", 2),
        
        # Dirección (4-6)
        ("DIRECTOR", 4), ("HEAD OFFICE", 4),
        ("HEAD DE", 5), ("HEAD DATA", 5), ("HEAD", 5),
        
        # Gerencia (7-12)
        ("GERENTE DE AREA", 7), ("GERENTE ZONAL", 8), ("GERENTE DE DIVISION", 9),
        ("GERENTE TIENDA", 10), ("GERENTE ASISTENTE", 11), ("GERENTE", 10),
        
        # Sub-Gerencia (13-15)
        ("SUBDIRECTOR", 13), ("SUBGERENTE", 14),
        
        # Jefatura/Lead (16-22)
        ("JEFE ZONAL", 16), ("JEFE COMERCIAL", 17), ("JEFE DE", 17), ("JEFE", 18),
        ("TEAM MANAGER", 19), ("MANAGER", 19),
        ("LEAD DE", 20), ("TEAM LEAD", 21), ("TECH LEAD", 21),
        ("LIDER DE", 21), ("LIDER", 22),
        
        # Coordinación (23-25)
        ("COORDINADOR", 23),
        
        # Supervisión (26-28)
        ("SUPERVISOR", 26),
        
        # Especialización Senior (29-35)
        ("PRINCIPAL EXPERT", 29), ("PRINCIPAL LEAD", 30), ("PRINCIPAL ENGINEER", 30), ("PRINCIPAL", 31),
        ("EXPERT", 32), ("STRATEGIST", 33),
        ("ADVISOR", 34), ("LEAD", 35),
        
        # Roles Senior/Especializados (36-50)
        ("SENIOR", 36), ("SR", 36),
        ("SPECIALIST", 37), ("ESPECIALISTA DE", 37), ("ESPECIALISTA", 38),
        ("AGILE COACH", 39),
        ("SCRUM MASTER", 40),
        ("BUSINESS ARCHITECT", 41), ("TECHNOLOGY ARCHITECT", 41), ("ARCHITECT", 42),
        ("ENGINEER", 43), ("SOFTWARE TEST ENGINEER", 43), ("SOFTWARE ENGINEER", 43),
        ("DATA SCIENTIST", 44),
        ("PRODUCT DESIGNER", 45), ("DESIGNER", 46),
        ("INNOVATION", 47),
        
        # Nivel Mid/Ejecutivo (51-70)
        ("AGILE TEAM FACILITATOR", 51),
        ("EJECUTIVO DE", 52), ("EJECUTIVO", 53),
        ("RELATIONSHIP MANAGER", 54),
        ("GROWTH HACKER", 55), ("GROWTH LEAD", 56), ("GROWTH", 57),
        ("BUSINESS DESIGNER", 58), ("BUSINESS ANALYST", 59), ("BUSINESS", 60),
        ("DATA ENGINEER", 61), ("DATA ANALYST", 62),
        ("PRODUCT LEAD", 63), ("PRODUCT", 64),
        ("CONVERSATION DESIGNER", 65), ("CONVERSATION DESIGN", 65),
        ("DESIGN", 66),
        ("ANALISTA DE", 67), ("ANALISTA", 68),
        ("GESTOR", 69), ("ASESOR", 70),
        
        # Roles de Soporte (71-80)
        ("CAMPAIGN", 71),
        ("ASSOCIATE", 72),
        ("ASISTENTE DE", 73), ("ASISTENTE", 74),
        ("REPRESENTANTE", 75),
        ("TECNICO", 76),
        ("AUXILIAR", 77),
        ("TRAMITADOR", 78),
        
        # Entrada (81-85)
        ("TRAINEE", 81), ("PRACTICANTE", 82),
        ("JUNIOR", 83), ("JR", 83),
        
        # Roles sin categoría clara (90)
        ("CX", 90), ("REAL TIME OPERATION", 90)
    ]

    def infer_rank(title_norm):
        """Infiere el rank basado en palabras clave, considerando orden de aparición."""
        best_rank = 999  # Valor alto por defecto
        
        for keyword, rank in seniority_keywords:
            if keyword in title_norm:
                # Retornar el rank más bajo encontrado (más alto en jerarquía)
                if rank < best_rank:
                    best_rank = rank
        
        return best_rank

    # Agregar rank a cada elemento
    for item in data:
        item["rank"] = infer_rank(item["puesto_norm"])

    # -----------------------------
    # 3) Precomputar títulos por división y global
    # -----------------------------
    division_titles = {}
    division_data = defaultdict(list)

    for item in data:
        division_data[item["division_norm"]].append(item)

    for div, items in division_data.items():
        # Agrupar por puesto y obtener el rank mínimo
        puesto_ranks = {}
        for item in items:
            puesto = item["puesto_norm"]
            if puesto not in puesto_ranks or item["rank"] < puesto_ranks[puesto]:
                puesto_ranks[puesto] = item["rank"]

        # Ordenar por rank (más alto primero -> rank menor)
        sorted_puestos = sorted(puesto_ranks.items(), key=lambda x: x[1])
        division_titles[div] = sorted_puestos

    # Títulos globales
    global_puesto_ranks = {}
    for item in data:
        puesto = item["puesto_norm"]
        if puesto not in global_puesto_ranks or item["rank"] < global_puesto_ranks[puesto]:
            global_puesto_ranks[puesto] = item["rank"]

    global_titles = sorted(global_puesto_ranks.items(), key=lambda x: x[1])

    # -----------------------------
    # 4) Funciones para detectar categoría / seniority y obtener siguiente escalón
    # -----------------------------
    def detect_category(title_norm):
        for pat, cat in KEYWORD_TO_CATEGORY.items():
            if re.search(pat, title_norm):
                return cat
        return None

    def detect_seniority(title_norm):
        for pat, label in SENIORITY_TOKENS.items():
            if re.search(pat, title_norm):
                return label
        return None

    def next_in_org_hierarchy(category):
        """Devuelve label canonical del siguiente cargo de mayor rango (string) o None."""
        # intentar ubicar category en ORG_HIERARCHY por igualdad o substring
        idx = None
        for i, v in enumerate(ORG_HIERARCHY):
            if v == category or v.split("/")[0] in category or category in v:
                idx = i
                break
        if idx is None:
            return None
        if idx == 0:
            return None
        return ORG_HIERARCHY[idx - 1]

    def next_in_tech_ladder(seniority_label):
        try:
            idx = TECH_LADDER.index(seniority_label)
        except ValueError:
            # mapear valores comunes
            map_equiv = {
                "TECH_ROLE": "MID/REGULAR",
                "MID/REGULAR": "SENIOR"
            }
            label = map_equiv.get(seniority_label, None)
            if label:
                idx = TECH_LADDER.index(label)
            else:
                return None
        if idx >= len(TECH_LADDER) - 1:
            return None
        return TECH_LADDER[idx + 1]

    def get_next_higher(title_norm):
        """
        Dado un título normalizado, devuelve un label objetivo (string) que representa
        el siguiente cargo de mayor rango (por ejemplo 'GERENTE/MANAGER' o 'ENGINEERING MANAGER').
        """
        cat = detect_category(title_norm)
        if cat == "TECH_ROLE":
            senior = detect_seniority(title_norm)
            if not senior:
                senior = "MID/REGULAR"
            next_tech = next_in_tech_ladder(senior)
            if next_tech:
                return next_tech
            # fallback razonable
            return "GERENTE/MANAGER"
        else:
            # usar categoría org si se detecta
            if cat:
                nxt = next_in_org_hierarchy(cat)
                if nxt:
                    return nxt
            # si no detectamos categoría explícita, intentar por seniority token
            senior = detect_seniority(title_norm)
            if senior:
                # mapear seniority técnico a org si aplica
                if senior in ("ENGINEERING MANAGER", "DIRECTOR ENGINEERING", "VP ENGINEERING", "CTO/CHIEF"):
                    # mapear a ORG equivalente de mayor rango
                    return "GERENTE/MANAGER" if senior == "ENGINEERING MANAGER" else "DIRECTOR"
                # fallback
                return "GERENTE/MANAGER"
            # si no hay nada detectable, devolver None
            return None

    # -----------------------------
    # 5) Heurística para buscar un puesto real que coincida con el objetivo
    # -----------------------------
    def find_real_title_for_target(target_label, division_norm=None):
        """
        Trata de encontrar un puesto real (puesto_norm) que corresponda al target_label.
        Preferencia: buscar en la misma división; si no, buscar globalmente.
        Devuelve (puesto_norm, division_found) o (None, None)
        """
        if not target_label:
            return None, None

        # 1) buscar por substring exacto en la misma división (si se dio)
        if division_norm and division_norm in division_titles:
            for puesto, r in division_titles[division_norm]:
                if target_label in puesto or any(tok in puesto for tok in target_label.split("/")):
                    return puesto, division_norm

        # 2) buscar un puesto global que contenga el label
        for puesto, r in global_titles:
            if target_label in puesto or any(tok in puesto for tok in target_label.split("/")):
                # intentar encontrar su división: buscar en division_titles
                for div, items in division_titles.items():
                    if any(puesto == p for p, _ in items):
                        return puesto, div
                return puesto, None

        # 3) coincidencias aproximadas sobre la lista global de puestos
        candidates = [p for p, _ in global_titles]
        matches = get_close_matches(target_label, candidates, n=2, cutoff=0.5)
        if matches:
            # devolver el primero que encontremos con su división (si la tiene)
            puesto = matches[0]
            for div, items in division_titles.items():
                if any(puesto == p for p, _ in items):
                    return puesto, div
            return puesto, None

        return None, None

    # -----------------------------
    # 6) Heurística principal para encontrar superior directo
    # -----------------------------
    def find_superior_for(title_norm, division_norm=None):
        """
        Devuelve (superior_puesto_norm, superior_division) o (None, None)
        Prioridad:
        1. Buscar en la misma división un puesto con rank menor (más alto)
        2. Buscar en divisiones relacionadas (misma gerencia/área)
        3. Usar estrategia híbrida con categorías
        4. Buscar globalmente el superior más cercano
        5. Reglas manuales de fallback
        """
        rank = infer_rank(title_norm)
        
        # 1) Buscar en la misma división primero (PRIORIDAD ALTA)
        if division_norm and division_norm in division_titles:
            candidates = division_titles[division_norm]
            # Buscar el puesto con el rank inmediatamente inferior (más alto en jerarquía)
            best_match = None
            min_rank_diff = float('inf')
            
            for puesto, r in candidates:
                if r < rank:
                    rank_diff = rank - r
                    if rank_diff < min_rank_diff:
                        min_rank_diff = rank_diff
                        best_match = (puesto, division_norm)
            
            if best_match:
                return best_match
        
        # 2) Buscar en divisiones relacionadas (mismo prefijo o área)
        if division_norm:
            # Extraer prefijos comunes: "DIV.", "GCIA.", "VP.", "TRIBU"
            related_divisions = []
            for div in division_titles.keys():
                if div == division_norm:
                    continue
                # Buscar divisiones con palabras clave comunes
                div_words = set(division_norm.split())
                other_words = set(div.split())
                common_words = div_words & other_words
                if len(common_words) >= 2:  # Al menos 2 palabras en común
                    related_divisions.append(div)
            
            # Buscar en divisiones relacionadas
            best_related = None
            min_related_diff = float('inf')
            
            for div in related_divisions:
                if div in division_titles:
                    for puesto, r in division_titles[div]:
                        if r < rank:
                            rank_diff = rank - r
                            if rank_diff < min_related_diff:
                                min_related_diff = rank_diff
                                best_related = (puesto, div)
            
            if best_related:
                return best_related
        
        # 3) Intentar estrategia híbrida con categorías
        target_label = get_next_higher(title_norm)
        if target_label:
            # Primero buscar en la misma división
            if division_norm:
                puesto_real, div_real = find_real_title_for_target(target_label, division_norm)
                if puesto_real:
                    return puesto_real, div_real
            
            # Si no se encuentra, buscar globalmente
            puesto_real, div_real = find_real_title_for_target(target_label, None)
            if puesto_real:
                return puesto_real, div_real
        
        # 4) Buscar globalmente el puesto con rank inmediatamente inferior
        best_global = None
        min_global_diff = float('inf')
        
        for puesto, r in global_titles:
            if r < rank:
                rank_diff = rank - r
                if rank_diff < min_global_diff:
                    min_global_diff = rank_diff
                    # Intentar recuperar su división
                    found_div = None
                    for div, items in division_titles.items():
                        if any(puesto == p for p, _ in items):
                            found_div = div
                            break
                    best_global = (puesto, found_div if found_div else None)
        
        if best_global:
            return best_global
        
        # 5) Reglas manuales específicas por palabra clave (FALLBACKS)
        # Estas reglas crean puestos genéricos cuando no se encuentra nada
        fallback_rules = [
            # Reglas de Gerencia
            (["GERENTE DE AREA", "GERENTE ZONAL"], "GERENTE CENTRAL"),
            (["GERENTE DE DIVISION", "GERENTE TIENDA"], "GERENTE DE AREA"),
            (["GERENTE ASISTENTE"], "GERENTE"),
            (["SUBGERENTE", "SUB-GERENTE"], "GERENTE"),
            
            # Reglas de Jefatura
            (["JEFE ZONAL", "JEFE COMERCIAL"], "SUBGERENTE"),
            (["JEFE", "TEAM MANAGER"], "SUBGERENTE"),
            (["LIDER DE", "LEAD DE", "COORDINADOR"], "JEFE"),
            (["SUPERVISOR"], "JEFE"),
            
            # Reglas Técnicas/Agile
            (["SCRUM MASTER", "AGILE TEAM FACILITATOR"], "TEAM MANAGER"),
            (["AGILE COACH"], "SUBGERENTE"),
            (["TEAM LEADER"], "TEAM MANAGER"),
            
            # Reglas de Especialización
            (["PRINCIPAL EXPERT", "PRINCIPAL LEAD"], "SUBGERENTE"),
            (["PRINCIPAL"], "SUBGERENTE"),
            (["SPECIALIST", "ESPECIALISTA", "EXPERT", "ADVISOR"], "JEFE"),
            (["ARCHITECT"], "SUBGERENTE"),
            
            # Reglas de Roles Modernos
            (["GROWTH HACKER", "GROWTH LEAD"], "SUBGERENTE"),
            (["GROWTH"], "JEFE"),
            (["PRODUCT DESIGNER", "DESIGN LEAD", "CONVERSATION DESIGN LEAD"], "SUBGERENTE"),
            (["DESIGNER", "CONVERSATION DESIGNER"], "TEAM LEADER"),
            (["PRODUCT LEAD", "DIGITAL PRODUCT LEAD"], "SUBGERENTE"),
            (["PRODUCT", "DIGITAL PRODUCT"], "TEAM LEADER"),
            (["DATA SCIENTIST ADVISOR", "DATA SCIENTIST EXPERT"], "SUBGERENTE"),
            (["DATA SCIENTIST LEAD"], "SUBGERENTE"),
            (["DATA SCIENTIST"], "TEAM LEADER"),
            (["DATA ENGINEER"], "TEAM LEADER"),
            (["DATA ANALYST ADVISOR"], "JEFE"),
            (["DATA ANALYST"], "SUPERVISOR"),
            (["BUSINESS DESIGNER", "BUSINESS ARCHITECT LEAD"], "SUBGERENTE"),
            (["BUSINESS ARCHITECT", "BUSINESS ANALYST"], "TEAM LEADER"),
            (["BUSINESS"], "SUPERVISOR"),
            
            # Reglas de Analistas
            (["ANALISTA SR", "ANALISTA SENIOR"], "JEFE"),
            (["ANALISTA DE"], "SUPERVISOR"),
            (["ANALISTA"], "SUPERVISOR"),
            
            # Reglas de Ejecutivos
            (["RELATIONSHIP MANAGER"], "JEFE"),
            (["EJECUTIVO DE"], "SUPERVISOR"),
            (["EJECUTIVO"], "SUPERVISOR"),
            
            # Reglas de Soporte
            (["GESTOR"], "SUPERVISOR"),
            (["ASESOR"], "SUPERVISOR"),
            (["CAMPAIGN PRINCIPAL LEAD"], "SUBGERENTE"),
            (["CAMPAIGN"], "TEAM LEADER"),
            (["ASSOCIATE"], "ANALISTA"),
            (["ASISTENTE DE"], "ANALISTA"),
            (["ASISTENTE"], "ANALISTA"),
            (["REPRESENTANTE"], "EJECUTIVO"),
            (["TECNICO"], "ESPECIALISTA"),
            (["AUXILIAR"], "ASISTENTE"),
            (["TRAMITADOR"], "ASISTENTE"),
            
            # Reglas de Entrada
            (["TRAINEE"], "ASISTENTE"),
            (["PRACTICANTE", "INTERN"], "ASISTENTE"),
            (["JUNIOR", "JR"], "ANALISTA"),
            
            # Roles sin categoría clara
            (["CX", "REAL TIME OPERATION"], "SUPERVISOR"),
        ]
        
        for keywords, target_puesto in fallback_rules:
            if any(kw in title_norm for kw in keywords):
                # Normalizar el target_puesto
                target_norm = normalize_text(target_puesto)
                
                # Primero intentar encontrar un puesto real que coincida
                if division_norm and division_norm in division_titles:
                    for puesto, r in division_titles[division_norm]:
                        if target_norm in puesto or any(part in puesto for part in target_norm.split()):
                            return puesto, division_norm
                
                # Buscar globalmente
                for puesto, r in global_titles:
                    if target_norm in puesto or any(part in puesto for part in target_norm.split()):
                        # Encontrar su división
                        for div, items in division_titles.items():
                            if any(puesto == p for p, _ in items):
                                return puesto, div
                        return puesto, None
                
                # Si no se encuentra puesto real, devolver el normalizado genérico
                return target_norm, division_norm if division_norm else None
        
        # 6) Si nada funciona, devolver el target_label directamente
        if target_label:
            return target_label, None
        
        return None, None

    # -----------------------------
    # 7) Construir mapping original -> info (usando find_superior_for)
    # -----------------------------
    mapping = {}
    for item in data:
        original = item["fam_puesto"]
        pn = item["puesto_norm"]
        dn = item["division_norm"]
        sup, sup_div = find_superior_for(pn, dn)
        mapping[original] = {
            "puesto_norm": pn,
            "division_norm": dn,
            "superior_norm": sup,
            "superior_division": sup_div
        }

    return mapping, division_titles, global_titles, infer_rank

# Variables globales (se cargarán al llamar load_hierarchy_data)
mapping = {}
division_titles = {}
global_titles = None
_infer_rank = None

# -----------------------------
# 8) Función pública para consultar (acepta coincidencias aproximadas)
# -----------------------------
def get_superior(puesto_query, division_query=None):
    pq_norm = normalize_text(puesto_query)
    dq_norm = normalize_text(division_query) if division_query else None

    # búsqueda exacta por puesto original (clave) o puesto normalizado en mapping
    for k, v in mapping.items():
        if v["puesto_norm"] == pq_norm and (dq_norm is None or v["division_norm"] == dq_norm):
            return v["superior_norm"], v["superior_division"]
        if normalize_text(k) == pq_norm and (dq_norm is None or v["division_norm"] == dq_norm):
            return v["superior_norm"], v["superior_division"]

    # coincidencias aproximadas entre puestos normalizados
    candidates = list({v["puesto_norm"] for v in mapping.values()})
    matches = get_close_matches(pq_norm, candidates, n=3, cutoff=0.6)
    if matches:
        best = matches[0]
        for k, v in mapping.items():
            if v["puesto_norm"] == best and (dq_norm is None or v["division_norm"] == dq_norm):
                return v["superior_norm"], v["superior_division"]

    # Si no se encuentra en el mapping, aplicar reglas de fallback directamente
    # Esto cubre casos donde el puesto no está en Libro3.csv pero necesitamos inferir su superior
    rank = _infer_rank(pq_norm) if _infer_rank else 999
    
    fallback_rules = [
        # Reglas de Gerencia
        (["GERENTE DE AREA", "GERENTE ZONAL"], "GERENTE CENTRAL"),
        (["GERENTE DE DIVISION", "GERENTE TIENDA"], "GERENTE DE AREA"),
        (["GERENTE ASISTENTE"], "GERENTE"),
        (["SUBGERENTE", "SUB-GERENTE"], "GERENTE"),
        
        # Reglas de Jefatura
        (["JEFE ZONAL", "JEFE COMERCIAL"], "SUBGERENTE"),
        (["JEFE", "TEAM MANAGER"], "SUBGERENTE"),
        (["LIDER DE", "LEAD DE", "COORDINADOR"], "JEFE"),
        (["SUPERVISOR"], "JEFE"),
        
        # Reglas Técnicas/Agile
        (["SCRUM MASTER", "AGILE TEAM FACILITATOR"], "TEAM MANAGER"),
        (["AGILE COACH"], "SUBGERENTE"),
        (["TEAM LEADER"], "TEAM MANAGER"),
        
        # Reglas de Especialización
        (["PRINCIPAL EXPERT", "PRINCIPAL LEAD"], "SUBGERENTE"),
        (["PRINCIPAL"], "SUBGERENTE"),
        (["SPECIALIST", "ESPECIALISTA", "EXPERT", "ADVISOR"], "JEFE"),
        (["ARCHITECT"], "SUBGERENTE"),
        
        # Reglas de Roles Modernos
        (["GROWTH HACKER", "GROWTH LEAD"], "SUBGERENTE"),
        (["GROWTH"], "JEFE"),
        (["PRODUCT DESIGNER", "DESIGN LEAD", "CONVERSATION DESIGN LEAD"], "SUBGERENTE"),
        (["DESIGNER", "CONVERSATION DESIGNER"], "TEAM LEADER"),
        (["PRODUCT LEAD", "DIGITAL PRODUCT LEAD"], "SUBGERENTE"),
        (["PRODUCT", "DIGITAL PRODUCT"], "TEAM LEADER"),
        (["DATA SCIENTIST ADVISOR", "DATA SCIENTIST EXPERT"], "SUBGERENTE"),
        (["DATA SCIENTIST LEAD"], "SUBGERENTE"),
        (["DATA SCIENTIST"], "TEAM LEADER"),
        (["DATA ENGINEER"], "TEAM LEADER"),
        (["DATA ANALYST ADVISOR"], "JEFE"),
        (["DATA ANALYST"], "SUPERVISOR"),
        (["BUSINESS DESIGNER", "BUSINESS ARCHITECT LEAD"], "SUBGERENTE"),
        (["BUSINESS ARCHITECT", "BUSINESS ANALYST"], "TEAM LEADER"),
        (["BUSINESS"], "SUPERVISOR"),
        
        # Reglas de Engineers
        (["PRINCIPAL ENGINEER"], "SUBGERENTE"),
        (["SOFTWARE TEST ENGINEER", "SOFTWARE ENGINEER", "ENGINEER"], "TEAM LEADER"),
        
        # Reglas de Analistas
        (["ANALISTA SR", "ANALISTA SENIOR"], "JEFE"),
        (["ANALISTA DE"], "SUPERVISOR"),
        (["ANALISTA"], "SUPERVISOR"),
        
        # Reglas de Ejecutivos
        (["RELATIONSHIP MANAGER"], "JEFE"),
        (["EJECUTIVO DE"], "SUPERVISOR"),
        (["EJECUTIVO"], "SUPERVISOR"),
        
        # Reglas de Soporte
        (["GESTOR"], "SUPERVISOR"),
        (["ASESOR"], "SUPERVISOR"),
        (["CAMPAIGN PRINCIPAL LEAD"], "SUBGERENTE"),
        (["CAMPAIGN"], "TEAM LEADER"),
        (["ASSOCIATE"], "ANALISTA"),
        (["ASISTENTE DE"], "ANALISTA"),
        (["ASISTENTE"], "ANALISTA"),
        (["REPRESENTANTE"], "EJECUTIVO"),
        (["TECNICO"], "ESPECIALISTA"),
        (["AUXILIAR"], "ASISTENTE"),
        (["TRAMITADOR"], "ASISTENTE"),
        
        # Reglas de Entrada
        (["TRAINEE"], "ASISTENTE"),
        (["PRACTICANTE", "INTERN"], "ASISTENTE"),
        (["JUNIOR", "JR"], "ANALISTA"),
        
        # Roles sin categoría clara
        (["CX", "REAL TIME OPERATION"], "SUPERVISOR"),
    ]
    
    for keywords, target_puesto in fallback_rules:
        if any(kw in pq_norm for kw in keywords):
            target_norm = normalize_text(target_puesto)
            # Buscar en el mapping global si existe este puesto
            for k, v in mapping.items():
                if target_norm in v["puesto_norm"] or v["puesto_norm"] in target_norm:
                    if dq_norm is None or v["division_norm"] == dq_norm:
                        return v["puesto_norm"], v["division_norm"]
            # Si no se encuentra, devolver normalizado
            return target_norm, dq_norm

    return None, None

# Ejemplo de uso:
if __name__ == "__main__":
    import sys

    # Permitir ingresar el nombre del archivo como argumento
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "Libro3.csv"  # Nombre del archivo CSV con la jerarquía de puestos

    try:
        # Cargar los datos
        mapping, division_titles, global_titles, _infer_rank = load_hierarchy_data(csv_file)
        print(f"Archivo cargado correctamente: {csv_file}")
        print(f"  Total de puestos procesados: {len(mapping)}")

        # Ejemplo de consulta
        print("\nEjemplo de consulta:")
        resultado = get_superior("ANALISTA DE PRODUCTO VALUE PROPOSITION", "DIV. BANCA NEGOCIOS")
        print(f"Superior de 'ANALISTA DE PRODUCTO VALUE PROPOSITION': {resultado}")
        # devuelve: (posición_superior_normalizada, "DIV. BANCA NEGOCIOS") o (posición_superior, None)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{csv_file}'")
    except Exception as e:
        print(f"Error al procesar el archivo: {str(e)}")
