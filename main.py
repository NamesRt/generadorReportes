import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from res import load_csv
import os

class ReportGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Reportes de Cuentas")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Variables
        self.ad_file = tk.StringVar()
        self.regs_file = tk.StringVar()
        self.selected_month = tk.StringVar(value="Enero")
        self.selected_year = tk.StringVar(value="2026")
        
        # Configurar interfaz
        self.create_widgets()
    
    def create_widgets(self):
        # Título
        title_label = tk.Label(
            self.root, 
            text="Generador de Reportes de Cuentas AD", 
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        # Frame para archivo AD
        ad_frame = tk.Frame(self.root, pady=10)
        ad_frame.pack(fill="x", padx=20)
        
        tk.Label(ad_frame, text="Archivo AD:", width=15, anchor="w").pack(side="left")
        ad_entry = tk.Entry(ad_frame, textvariable=self.ad_file, width=40)
        ad_entry.pack(side="left", padx=5)
        tk.Button(ad_frame, text="Buscar...", command=self.select_ad_file).pack(side="left")
        
        # Frame para archivo Regs
        regs_frame = tk.Frame(self.root, pady=10)
        regs_frame.pack(fill="x", padx=20)
        
        tk.Label(regs_frame, text="Archivo Registros:", width=15, anchor="w").pack(side="left")
        regs_entry = tk.Entry(regs_frame, textvariable=self.regs_file, width=40)
        regs_entry.pack(side="left", padx=5)
        tk.Button(regs_frame, text="Buscar...", command=self.select_regs_file).pack(side="left")
        
        # Frame para mes
        month_frame = tk.Frame(self.root, pady=10)
        month_frame.pack(fill="x", padx=20)
        
        tk.Label(month_frame, text="Mes:", width=15, anchor="w").pack(side="left")
        
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            "Todos"
        ]
        month_combo = ttk.Combobox(
            month_frame, 
            textvariable=self.selected_month, 
            values=meses,
            state="readonly",
            width=20
        )
        month_combo.pack(side="left", padx=5)
        
        # Frame para año
        year_frame = tk.Frame(self.root, pady=10)
        year_frame.pack(fill="x", padx=20)
        
        tk.Label(year_frame, text="Año:", width=15, anchor="w").pack(side="left")
        
        # Generar lista de años (últimos 10 años hasta el actual)
        import datetime
        current_year = datetime.datetime.now().year
        years = [str(year) for year in range(current_year, current_year - 11, -1)]
        
        year_combo = ttk.Combobox(
            year_frame, 
            textvariable=self.selected_year, 
            values=years,
            state="readonly",
            width=20
        )
        year_combo.pack(side="left", padx=5)
        
        # Frame para botones
        button_frame = tk.Frame(self.root, pady=30)
        button_frame.pack()
        
        tk.Button(
            button_frame, 
            text="Generar Reportes", 
            command=self.generate_reports,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack()
        
        # Frame para status
        self.status_frame = tk.Frame(self.root, pady=10)
        self.status_frame.pack(fill="both", expand=True, padx=20)
        
        tk.Label(self.status_frame, text="Estado:", font=("Arial", 10, "bold"), height=1).pack(anchor="w")
        
        self.status_text = tk.Text(self.status_frame, height=6, width=70, state="disabled")
        self.status_text.pack(fill="both", expand=True)
        
        # Scrollbar para el status
        scrollbar = tk.Scrollbar(self.status_text)
        scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.status_text.yview)
    
    def select_ad_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo AD",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.ad_file.set(filename)
    
    def select_regs_file(self):
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de datos de colaborador",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.regs_file.set(filename)
    
    def log_status(self, message):
        self.status_text.config(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.config(state="disabled")
        self.root.update()
    
    def generate_reports(self):
        # Validar que se hayan seleccionado los archivos
        if not self.ad_file.get():
            messagebox.showerror("Error", "Por favor seleccione el archivo AD")
            return
        
        if not self.regs_file.get():
            messagebox.showerror("Error", "Por favor seleccione el archivo de Registros")
            return
        
        # Validar que los archivos existan
        if not os.path.exists(self.ad_file.get()):
            messagebox.showerror("Error", "El archivo AD no existe")
            return
        
        if not os.path.exists(self.regs_file.get()):
            messagebox.showerror("Error", "El archivo de Registros no existe")
            return
        
        # Limpiar status
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, "end")
        self.status_text.config(state="disabled")
        
        self.log_status("Iniciando generación de reportes...")
        self.log_status(f"Archivo AD: {os.path.basename(self.ad_file.get())}")
        self.log_status(f"Archivo Registros: {os.path.basename(self.regs_file.get())}")
        self.log_status("Jerarquía: Se construirá desde archivo de Registros")
        
        # Determinar mes
        mes_seleccionado = self.selected_month.get()
        if mes_seleccionado == "Todos":
            mes_seleccionado = None
            self.log_status("Mes: Todos")
        else:
            self.log_status(f"Mes: {mes_seleccionado}")
        
        # Determinar año
        año_seleccionado = self.selected_year.get()
        self.log_status(f"Año: {año_seleccionado}")
        
        self.log_status("-" * 50)
        
        try:
            # Llamar a la función de procesamiento
            outputDir = load_csv(self.ad_file.get(), self.regs_file.get(), mes_seleccionado, año_seleccionado)
            
            self.log_status("-" * 50)
            self.log_status(f"Reportes generados exitosamente en la carpeta '{outputDir}'")
            messagebox.showinfo(
                "Éxito", 
                f"Los reportes se han generado correctamente en la carpeta '{outputDir}'"
            )
        except Exception as e:
            self.log_status(f"✗ Error: {str(e)}")
            messagebox.showerror("Error", f"Error al generar reportes:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ReportGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
