import unicodedata
import csv
from typing import Any, List, Tuple, Optional, Dict

def normalize(s: str, remove_accents: bool = True) -> str:
    if s is None: return ""
    s = s.casefold().strip()
    if remove_accents:
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", s)

def normalize_text(text: str) -> str:
    """Normaliza texto para comparaciones (sin acentos, mayúsculas/minúsculas)."""
    return normalize(text, remove_accents=True)

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.values = []        # lista de payloads asociados a esta palabra
        self.originals = set()  # formas originales (para devolver texto con tildes)

class Trie:
    def __init__(self, remove_accents: bool = True):
        self.root = TrieNode()
        self.remove_accents = remove_accents

    def _norm(self, word: str) -> str:
        return normalize(word, remove_accents=self.remove_accents)

    def insert(self, word: str, value: Any) -> None:
        """Inserta word y asocia value (puede ser cualquier objeto)."""
        norm = self._norm(word)
        node = self.root
        for ch in norm:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.values.append(value)    # agrega la vinculación
        node.originals.add(word)

    def search(self, word: str) -> List[Any]:
        """Devuelve lista de valores asociados a la palabra (o [] si no existe)."""
        norm = self._norm(word)
        node = self.root
        for ch in norm:
            if ch not in node.children:
                return []
            node = node.children[ch]
        return node.values[0] if node.is_end else []

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Tuple[str, List[Any]]]:
        """Devuelve lista de (palabra_original, [valores]) que empiezan con prefix."""
        norm = self._norm(prefix)
        node = self.root
        for ch in norm:
            if ch not in node.children:
                return []
            node = node.children[ch]

        results = []

        def dfs(n: TrieNode, path: list):
            if len(results) >= limit:
                return
            if n.is_end:
                # puede haber varias formas originales; devolvemos cada una junto a sus values
                for orig in n.originals:
                    results.append((orig, list(n.values)))
                    if len(results) >= limit:
                        return
            for c, child in n.children.items():
                path.append(c)
                dfs(child, path)
                path.pop()

        dfs(node, [])
        return results

# ---------- Ejemplo de uso ----------
if __name__ == "__main__":
    t = Trie(remove_accents=True)
    # asociamos un diccionario (p. ej. fila del CSV) a cada palabra
    t.insert("ANALYTICS CENTER OF EXCELLENCE", "CHIEF DATA & DIGITAL ANALYTICS OFFICER")
    t.insert("ANALYTICS TRANSLATOR", "GERENTE DE DIVISION")
    t.insert("DATA OFFICE", "HEAD DATA OFFICER")
    t.insert("DIV. AGILIDAD", "AGILE HEAD")
    t.insert("DIV. ANALYTICS INTELLIGENCE", "GERENTE DE DIVISION")
    t.insert("DIV. ASESORIA LEGAL PRODUCTOS SERVICIOS Y CONTRATOS", "GERENTE DE DIVISION")
    t.insert("DIV. AGILIDAD", "AGILE HEAD")
    t.insert("DIV. BANCA NEGOCIOS", "GERENTE DE DIVISION")
    t.insert("DIV. CIBERSEGURIDAD", "Requiere búsqueda manual")
    t.insert("DIV. CLUB SUELDO", "GERENTE DE DIVISION")
    t.insert("DIV. ESTRATEGIA E INTELIGENCIA DE NEGOCIOS", "GERENTE DE DIVISION")
    t.insert("DIV. ESTRATEGIA IBK", "awa")
    t.insert("DIV. ESTRATEGIA IFS", "GERENTE DE DIVISIÓN")
    t.insert("DIV. ESTRATEGIA Y PLANNING", "PRINCIPAL LEAD")
    t.insert("DIV. MARKETING & CUSTOMER EXPERIENCE", "GERENTE DE DIVISION")
    t.insert("DIV. MESA DE DISTRIBUCION", "GERENTE DE DIVISION")
    t.insert("DIV. METODOLOGIAS Y GESTION DE PORTAFOLIO", "GERENTE DE DIVISION")
    t.insert("DIV. PLANEAMIENTO E INTELIGENCIA DE NEGOCIOS", "GERENTE DE DIVISION")
    t.insert("DIV. PLANEAMIENTO Y ANALISIS FINANCIERO", "GERENTE DE DIVISION")
    t.insert("DIV. SEGMENTO ESTADO", "GERENTE DE DIVISION")
    t.insert("DIV. SEGMENTO HIPOTECARIO E INMOBILIARIO", "GERENTE DE DIVISION")
    t.insert("DIV. SERVICIO AL CLIENTE", "GERENTE DE DIVISION")
    t.insert("DIV. TRANSFORMACIÓN BANCA COMERCIAL Y MDC", "GERENTE DE DIVISION")
    t.insert("DIV. TRANSFORMACION DATA ANALYTICS", "GERENTE DE DIVISION")
    t.insert("DIV. TRANSFORMACION DE RIESGOS RETAIL", "GERENTE DE DIVISION")
    t.insert("DIV. TRANSFORMACION MEDIOS DE PAGO Y MERCHANTS", "GERENTE DE DIVISION")
    t.insert("DIV. VENTAS RETAIL", "GERENTE DE DIVISION")
    t.insert("DIV.ADMINISTRACION Y CONTROL DE GESTION", "GERENTE DE DIVISION")
    t.insert("DIV.ADMISION DE RIESGOS CORPORATIVOS", "GERENTE DE DIVISION")
    t.insert("DIV.ADMISION DE RIESGOS EMPRESARIALES", "GERENTE DE DIVISION")
    t.insert("DIV.ARQUITECTURA TECNOLOGICA", "GERENTE DE DIVISION")
    t.insert("DIV.AUDITORIA INTERNA", "GERENTE DE DIVISION")
    t.insert("DIV.BANCA CORPORATIVA", "GERENTE DE DIVISION")
    t.insert("DIV.BANCA EMPRESA", "GERENTE DE DIVISION")
    t.insert("DIV.BCA.INSTITUCIONAL Y CORRESPONSALIA", "GERENTE DE DIVISION")
    t.insert("DIV.CONTABILIDAD", "GERENTE DE DIVISIÓN")
    t.insert("DIV.CUMPLIMIENTO", "CHIEF COMPLIANCE OFFICER")
    t.insert("DIV.ECOSISTEMA COMERCIAL", "GERENTE DE DIVISION")
    t.insert("DIV.ESTRUCTURACION COMERCIAL", "GERENTE DE DIVISION")
    t.insert("DIV.GESTION DE PREVENCION DEL FRAUDE", "GERENTE DE DIVISION")
    t.insert("DIV.GESTION Y TRANSFORMACION DE PROCESOS", "GERENTE DE DIVISION")
    t.insert("DIV.IMPUESTOS", "GERENTE DE DIVISION")
    t.insert("DIV.LABENTANA", "INNOVATION PRINCIPAL LEAD")
    t.insert("DIV.MESA DE POSICION", "GERENTE DE DIVISION")
    t.insert("DIV.PRODUCTOS SERVICIOS Y CANALES PARA EMPRESAS", "GERENTE DE DIVISION")
    t.insert("DIV.RIESGO OPERACIONAL Y CONTINUIDAD DEL NEGOCIO", "GERENTE DE DIVISION")
    t.insert("DIV.RIESGOS BANCA PERSONAS", "GERENTE DE DIVISION")
    t.insert("DIV.RIESGOS DE BANCA PEQUEÑA EMPRESA", "GERENTE DE DIVISION")
    t.insert("DIV.RIESGOS MERCADO", "GERENTE DE DIVISION")
    t.insert("DIV.SEGUIMIENTO DE RIESGOS Y RECUPERACIONES", "GERENTE DE DIVISION")
    t.insert("DIV.SOLUCIONES DE PAGO", "GERENTE DE DIVISION")
    t.insert("DIV.TDAS.LIMA", "GERENTE DE DIVISION")
    t.insert("DIV.TDAS.PROVINCIA", "GERENTE DE DIVISION")
    t.insert("DPTO. DESARROLLO Y GESTION DE CANALES", "JEFE DE GESTION E INNOVACION")
    t.insert("GCIA CENTRAL DE CANALES Y SERVICIO AL CLIENTE", "GERENTE CENTRAL")
    t.insert("GCIA CENTRAL SERVICIOS TI", "GERENTE CENTRAL")
    t.insert("GCIA.CENTRAL ESTRATEGIA Y TRANSFORMACIÓN TECNOLÓGICA", "GERENTE CENTRAL")
    t.insert("GERENCIA CENTRAL DE TRANFORMACION DE RIESGOS Y SOLUCIONES DE PAGOS", "GERENTE CENTRAL")
    t.insert("GERENCIA GENERAL", "GERENTE GENERAL")
    t.insert("HEAD OFFICE DE RIESGOS RETAIL", "HEAD")
    t.insert("INTELIGENCIA CONTINUA", "GERENTE DE DIVISION")
    t.insert("MODEL RISK MANAGEMENT", "MODEL RISK MONITORING LEAD")
    t.insert("MODELOS. & MLOPs", "GERENTE DE DIVISION")
    t.insert("PRESIDENCIA", "MOZO")
    t.insert("SERVICIOS CLOUD", "GERENTE DE DIVISION")
    t.insert("SQUAD - IZIPAY", "PRINCIPAL SERVICE OWNER")
    t.insert("TRIBU CANALES DIGITALES Y PRODUCTOS", "LIDER DE TRIBU")
    t.insert("TRIBU CICLO DE VIDA Y VALOR", "LIDER DE TRIBU")
    t.insert("TRIBU PAGOS", "LIDER DE TRIBU")
    t.insert("TRIBU RENTA ALTA", "LIDER DE TRIBU")
    t.insert("TRIBU SEGMENTO MASIVOS Y ENTRADA", "GERENTE CENTRAL")
    t.insert("VP. GESTION Y DESARROLLO HUMANO", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.ASUNTOS CORPORATIVOS Y LEGALES", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.COMERCIAL", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.ECOSISTEMA DE PAYMENTS", "SUBGERENTE INTERNACIONALIZACION")
    t.insert("VP.FINANZAS", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.MERCADO CAPITALES", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.NEGOCIOS RETAIL Y CANALES", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.OPERACIONES Y TECNOLOGIA", "VICE PRESIDENTE EJECUTIVO")
    t.insert("VP.RIESGOS", "VICE PRESIDENTE EJECUTIVO")




    print(t.search("ANALYTICS CENTER OF EXCELLENCE"))    # devuelve lista con los 2 dicts
    print(t.search("VP.RIESGOS"))    # True si remove_accents=True -> mismos dicts
    print(t.search("HEAD OFFICE DE RIESGOS RETAIL"))  # [('árbol', [{'id':3}]), ('armario', [{'id':4}])]


# Trie global para la jerarquía
_hierarchy_trie = None

def load_hierarchy_data(csv_file: str, fam_puesto_col: int = 10, division_col: int = 11) -> Tuple[Trie, Dict, List, List]:
    """
    Carga datos de jerarquía en un Trie para búsqueda eficiente.
    Retorna: (trie, mapping_dict, lista_puestos, lista_divisiones)
    """
    global _hierarchy_trie
    
    if _hierarchy_trie is None:
        _hierarchy_trie = Trie(remove_accents=True)
        
        # Insertar todas las relaciones de jerarquía predefinidas
        jerarquia = {
            "ANALYTICS CENTER OF EXCELLENCE": "CHIEF DATA & DIGITAL ANALYTICS OFFICER",
            "ANALYTICS TRANSLATOR": "GERENTE DE DIVISION",
            "DATA OFFICE": "HEAD DATA OFFICER",
            "DIV. AGILIDAD": "AGILE HEAD",
            "DIV. ANALYTICS INTELLIGENCE": "GERENTE DE DIVISION",
            "DIV. ASESORIA LEGAL PRODUCTOS SERVICIOS Y CONTRATOS": "GERENTE DE DIVISION",
            "DIV. BANCA NEGOCIOS": "GERENTE DE DIVISION",
            "DIV. CIBERSEGURIDAD": "GERENTE DE DIVISION",
            "DIV. CLUB SUELDO": "GERENTE DE DIVISION",
            "DIV. ESTRATEGIA E INTELIGENCIA DE NEGOCIOS": "GERENTE DE DIVISION",
            "DIV. ESTRATEGIA IBK": "GERENTE DE DIVISION",
            "DIV. ESTRATEGIA IFS": "GERENTE DE DIVISIÓN",
            "DIV. ESTRATEGIA Y PLANNING": "PRINCIPAL LEAD",
            "DIV. MARKETING & CUSTOMER EXPERIENCE": "GERENTE DE DIVISION",
            "DIV. MESA DE DISTRIBUCION": "GERENTE DE DIVISION",
            "DIV. METODOLOGIAS Y GESTION DE PORTAFOLIO": "GERENTE DE DIVISION",
            "DIV. PLANEAMIENTO E INTELIGENCIA DE NEGOCIOS": "GERENTE DE DIVISION",
            "DIV. PLANEAMIENTO Y ANALISIS FINANCIERO": "GERENTE DE DIVISION",
            "DIV. SEGMENTO ESTADO": "GERENTE DE DIVISION",
            "DIV. SEGMENTO HIPOTECARIO E INMOBILIARIO": "GERENTE DE DIVISION",
            "DIV. SERVICIO AL CLIENTE": "GERENTE DE DIVISION",
            "DIV. TRANSFORMACIÓN BANCA COMERCIAL Y MDC": "GERENTE DE DIVISION",
            "DIV. TRANSFORMACION DATA ANALYTICS": "GERENTE DE DIVISION",
            "DIV. TRANSFORMACION DE RIESGOS RETAIL": "GERENTE DE DIVISION",
            "DIV. TRANSFORMACION MEDIOS DE PAGO Y MERCHANTS": "GERENTE DE DIVISION",
            "DIV. VENTAS RETAIL": "GERENTE DE DIVISION",
            "DIV.ADMINISTRACION Y CONTROL DE GESTION": "GERENTE DE DIVISION",
            "DIV.ADMISION DE RIESGOS CORPORATIVOS": "GERENTE DE DIVISION",
            "DIV.ADMISION DE RIESGOS EMPRESARIALES": "GERENTE DE DIVISION",
            "DIV.ARQUITECTURA TECNOLOGICA": "GERENTE DE DIVISION",
            "DIV.AUDITORIA INTERNA": "GERENTE DE DIVISION",
            "DIV.BANCA CORPORATIVA": "GERENTE DE DIVISION",
            "DIV.BANCA EMPRESA": "GERENTE DE DIVISION",
            "DIV.BCA.INSTITUCIONAL Y CORRESPONSALIA": "GERENTE DE DIVISION",
            "DIV.CONTABILIDAD": "GERENTE DE DIVISIÓN",
            "DIV.CUMPLIMIENTO": "CHIEF COMPLIANCE OFFICER",
            "DIV.ECOSISTEMA COMERCIAL": "GERENTE DE DIVISION",
            "DIV.ESTRUCTURACION COMERCIAL": "GERENTE DE DIVISION",
            "DIV.GESTION DE PREVENCION DEL FRAUDE": "GERENTE DE DIVISION",
            "DIV.GESTION Y TRANSFORMACION DE PROCESOS": "GERENTE DE DIVISION",
            "DIV.IMPUESTOS": "GERENTE DE DIVISION",
            "DIV.LABENTANA": "INNOVATION PRINCIPAL LEAD",
            "DIV.MESA DE POSICION": "GERENTE DE DIVISION",
            "DIV.PRODUCTOS SERVICIOS Y CANALES PARA EMPRESAS": "GERENTE DE DIVISION",
            "DIV.RIESGO OPERACIONAL Y CONTINUIDAD DEL NEGOCIO": "GERENTE DE DIVISION",
            "DIV.RIESGOS BANCA PERSONAS": "GERENTE DE DIVISION",
            "DIV.RIESGOS DE BANCA PEQUEÑA EMPRESA": "GERENTE DE DIVISION",
            "DIV.RIESGOS MERCADO": "GERENTE DE DIVISION",
            "DIV.SEGUIMIENTO DE RIESGOS Y RECUPERACIONES": "GERENTE DE DIVISION",
            "DIV.SOLUCIONES DE PAGO": "GERENTE DE DIVISION",
            "DIV.TDAS.LIMA": "GERENTE DE DIVISION",
            "DIV.TDAS.PROVINCIA": "GERENTE DE DIVISION",
            "DPTO. DESARROLLO Y GESTION DE CANALES": "JEFE DE GESTION E INNOVACION",
            "GCIA CENTRAL DE CANALES Y SERVICIO AL CLIENTE": "GERENTE CENTRAL",
            "GCIA CENTRAL SERVICIOS TI": "GERENTE CENTRAL",
            "GCIA.CENTRAL ESTRATEGIA Y TRANSFORMACIÓN TECNOLÓGICA": "GERENTE CENTRAL",
            "GERENCIA CENTRAL DE TRANFORMACION DE RIESGOS Y SOLUCIONES DE PAGOS": "GERENTE CENTRAL",
            "GERENCIA GENERAL": "GERENTE GENERAL",
            "HEAD OFFICE DE RIESGOS RETAIL": "HEAD",
            "INTELIGENCIA CONTINUA": "GERENTE DE DIVISION",
            "MODEL RISK MANAGEMENT": "MODEL RISK MONITORING LEAD",
            "MODELOS. & MLOPs": "GERENTE DE DIVISION",
            "PRESIDENCIA": "PRESIDENTE",
            "SERVICIOS CLOUD": "GERENTE DE DIVISION",
            "SQUAD - IZIPAY": "PRINCIPAL SERVICE OWNER",
            "TRIBU CANALES DIGITALES Y PRODUCTOS": "LIDER DE TRIBU",
            "TRIBU CICLO DE VIDA Y VALOR": "LIDER DE TRIBU",
            "TRIBU PAGOS": "LIDER DE TRIBU",
            "TRIBU RENTA ALTA": "LIDER DE TRIBU",
            "TRIBU SEGMENTO MASIVOS Y ENTRADA": "GERENTE CENTRAL",
            "VP. GESTION Y DESARROLLO HUMANO": "VICE PRESIDENTE EJECUTIVO",
            "VP.ASUNTOS CORPORATIVOS Y LEGALES": "VICE PRESIDENTE EJECUTIVO",
            "VP.COMERCIAL": "VICE PRESIDENTE EJECUTIVO",
            "VP.ECOSISTEMA DE PAYMENTS": "VICE PRESIDENTE EJECUTIVO",
            "VP.FINANZAS": "VICE PRESIDENTE EJECUTIVO",
            "VP.MERCADO CAPITALES": "VICE PRESIDENTE EJECUTIVO",
            "VP.NEGOCIOS RETAIL Y CANALES": "VICE PRESIDENTE EJECUTIVO",
            "VP.OPERACIONES Y TECNOLOGIA": "VICE PRESIDENTE EJECUTIVO",
            "VP.RIESGOS": "VICE PRESIDENTE EJECUTIVO",
        }
        
        # Insertar en el Trie: división/área -> puesto superior
        for division, puesto_superior in jerarquia.items():
            _hierarchy_trie.insert(division, puesto_superior)
    
    # Crear un mapping dict para compatibilidad
    mapping_dict = {}
    lista_puestos = []
    lista_divisiones = []
    
    return (_hierarchy_trie, mapping_dict, lista_puestos, lista_divisiones)

def get_superior(puesto_actual: str, division_actual: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Busca el puesto superior en la jerarquía usando el Trie.
    
    Args:
        puesto_actual: Puesto actual de la persona
        division_actual: División/área donde trabaja
        
    Returns:
        (puesto_superior_normalizado, division_superior)
        donde puesto_superior está normalizado para búsqueda
    """
    global _hierarchy_trie
    
    if _hierarchy_trie is None:
        load_hierarchy_data("", 0, 0)  # Cargar jerarquía predefinida
    
    # Normalizar la división para búsqueda
    division_norm = normalize_text(division_actual) if division_actual else ""
    
    # Buscar en el Trie por división/área
    puesto_superior = _hierarchy_trie.search(division_actual)
    
    if puesto_superior and isinstance(puesto_superior, str):
        # Retornar el puesto superior normalizado y la misma división
        return (normalize_text(puesto_superior), division_actual)
    
    # Si no se encuentra, retornar None
    return (None, None)

# Crear instancia global del mapping para mantener compatibilidad
mapping = {}

