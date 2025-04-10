import os
import subprocess
import webbrowser
import tkinter as tk
from tkinter import messagebox

REPO_URL = "https://github.com/assizalcaraz/bot-google-drive" 
CARPETA_DESTINO = "mi_app"

def comando_existe(comando):
    return subprocess.call(f"type {comando}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def instalar_app():
    if not comando_existe("git"):
        messagebox.showerror("Falta Git", "Git no está instalado. Por favor, instalalo antes de continuar.")
        return
    if not comando_existe("docker"):
        messagebox.showerror("Falta Docker", "Docker no está instalado. Por favor, instalalo antes de continuar.")
        return

    try:
        if not os.path.exists(CARPETA_DESTINO):
            subprocess.check_call(["git", "clone", REPO_URL, CARPETA_DESTINO])
        
        os.chdir(CARPETA_DESTINO)
        subprocess.Popen(["docker-compose", "up", "-d", "--build"])
        webbrowser.open("http://localhost")
        messagebox.showinfo("Éxito", "La aplicación se está ejecutando en http://localhost")
    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error: {e}")

# Interfaz gráfica mínima
ventana = tk.Tk()
ventana.title("Instalador de la app")
ventana.geometry("400x200")
ventana.configure(bg="#131720")

titulo = tk.Label(ventana, text="Instalador de la App", font=("Arial", 16), fg="white", bg="#131720")
titulo.pack(pady=20)

btn_instalar = tk.Button(ventana, text="Instalar y Ejecutar", command=instalar_app, bg="#561928", fg="white", padx=10, pady=5)
btn_instalar.pack()

ventana.mainloop()
