import os
import subprocess
import sys
import webbrowser
import tkinter as tk
from tkinter import messagebox, BooleanVar, Checkbutton

# Paleta de colores
FONDO = "#0a192f"
PRINCIPAL = "#9b0e32"
TEXTO = "#ffffff"

# Repositorio
REPO_URL = "https://github.com/assizalcaraz/bot-google-drive"
CARPETA_DESTINO = "bot_google_drive"

def comando_existe(comando):
    try:
        subprocess.check_output([comando, "--version"])
        return True
    except Exception:
        return False

def crear_acceso_directo():
    if os.name == "nt":
        escritorio = os.path.join(os.environ["USERPROFILE"], "Desktop")
        acceso_path = os.path.join(escritorio, "Bot Google Drive.lnk")
        script_path = os.path.abspath(os.path.join(CARPETA_DESTINO, "main.py"))

        powershell = f'''
        $WshShell = New-Object -ComObject WScript.Shell;
        $Shortcut = $WshShell.CreateShortcut("{acceso_path}");
        $Shortcut.TargetPath = "python";
        $Shortcut.Arguments = '"{script_path}"';
        $Shortcut.WorkingDirectory = "{os.path.dirname(script_path)}";
        $Shortcut.Save();
        '''
        subprocess.run(["powershell", "-Command", powershell], shell=True)

def instalar_app():
    if not comando_existe("git"):
        messagebox.showerror("Falta Git", "Git no está instalado. Por favor, instalalo antes de continuar.")
        return
    if not comando_existe("python"):
        messagebox.showerror("Falta Python", "Python no está instalado. Por favor, instalalo antes de continuar.")
        return

    try:
        if not os.path.exists(CARPETA_DESTINO):
            subprocess.check_call(["git", "clone", REPO_URL, CARPETA_DESTINO])
        
        os.chdir(CARPETA_DESTINO)
        subprocess.Popen([sys.executable, "main.py"])
        webbrowser.open("http://localhost:5000/")
        if crear_acceso_var.get():
            crear_acceso_directo()
        messagebox.showinfo("Éxito", "La aplicación se está ejecutando.")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

# Paleta de colores actualizada
FONDO = "#000000"       # azul petróleo
PRINCIPAL = "#ffffff"   # rojo vibrante
TEXTO = "#cf0e75"        # blanco cálido


# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Instalador")
ventana.configure(bg=FONDO)

# Checkbox
crear_acceso_var = BooleanVar()
check = Checkbutton(
    ventana,
    text="Crear acceso directo en el escritorio",
    variable=crear_acceso_var,
    fg=TEXTO,
    bg=FONDO,
    activebackground=FONDO,
    activeforeground=TEXTO,
    selectcolor=PRINCIPAL,
    font=("Arial", 10)
)
check.pack(pady=10)

# Botón bordó corregido
btn_instalar = tk.Button(
    ventana,
    text="Instalar y Ejecutar",
    command=instalar_app,
    bg=PRINCIPAL,
    fg=TEXTO,
    activebackground=PRINCIPAL,
    activeforeground=TEXTO,
    highlightthickness=0,      # quita borde blanco en macOS
    borderwidth=0,             # elimina el marco clásico
    relief="flat",             # estilo plano
    padx=14,
    pady=8,
    font=("Arial", 11, "bold")
)
btn_instalar.pack(pady=15)




ventana.mainloop()
