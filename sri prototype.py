# ================== SRI AI - Stage 2 (Updated & Optimized) ==================
import sys
import os
import time
import math
import json
import queue
import threading
import random
import traceback
import socket
from datetime import datetime
import tkinter as tk
import customtkinter as ctk
import psutil
import pyttsx3
import cv2
from PIL import Image, ImageTk
from gpt4all import GPT4All
import speech_recognition as sr
import webbrowser
import requests  # Added for OpenRouter API

# ------------------- Safe stdout (prevent flush errors) -------------------
class SafeStdOut:
    def write(self, msg):
        try:
            sys.stdout.write(msg)
        except Exception:
            pass
    def flush(self):
        try:
            sys.stdout.flush()
        except Exception:
            pass

sys.stdout = SafeStdOut()
sys.stderr = SafeStdOut()

# ------------------- Config & Globals -------------------
MEMORY_FILE = "Data.json"
MODEL_FOLDER = r"C:/Users/kommi/python project file/models"
# Support multiple offline models: Default to Mistral for general use, fallback to DeepSeek.
GPT_MODELS = {
    "mistral": "Mistral-7B-Instruct-v0.2-Q4_K_M.gguf",  # General/daily use
    "deepseek": "deepseek-r1-7b-instruct-Q4_K_M.gguf"  # For reasoning/coding
}
CURRENT_MODEL = "mistral"  # Default offline model; can switch via commands.
CONTEXT_MAX = 4
gpt = None
memory = []
response_queue = queue.Queue()
preferred_voice_id = None
OPENROUTER_API_KEY = "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"  # Replace with your actual OpenRouter API key
OPENROUTER_MODEL = "qwen/qwen-2.5-72b-instruct"  # Qwen2.5 72B Instruct on OpenRouter

# ------------------- Female Voice Selection -------------------
def choose_female_voice():
    global preferred_voice_id
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        for v in voices:
            name = v.name.lower()
            if any(f in name for f in ["female", "zira", "hazel", "anna", "samantha"]):
                preferred_voice_id = v.id
                break
        if not preferred_voice_id and len(voices) > 1:
            preferred_voice_id = voices[1].id
        elif not preferred_voice_id and voices:
            preferred_voice_id = voices[0].id
        engine.stop()
    except Exception:
        preferred_voice_id = None

choose_female_voice()

# ------------------- Text-to-Speech -------------------
def speak_text(text):
    def _worker(tts_text, voice_id):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 170)
            engine.setProperty("volume", 1.0)
            if voice_id:
                try:
                    engine.setProperty("voice", voice_id)
                except Exception:
                    pass
            engine.say(tts_text)
            engine.runAndWait()
            engine.stop()
        except Exception:
            pass
    threading.Thread(target=_worker, args=(text, preferred_voice_id), daemon=True).start()

# ------------------- GPT4All Integration (Offline Fallback) -------------------
def init_gpt(model_key="mistral"):
    global gpt, CURRENT_MODEL
    try:
        model_name = GPT_MODELS.get(model_key)
        if not model_name:
            raise ValueError(f"Invalid model key: {model_key}")
        print(f"Attempting to load GPT4All model: {model_name} from {MODEL_FOLDER}")
        gpt = GPT4All(model_name=model_name, model_path=MODEL_FOLDER, allow_download=True)
        CURRENT_MODEL = model_key
        print(f"GPT4All model '{model_key}' loaded successfully.")
    except Exception as e:
        print(f"GPT4All initialization failed for {model_key}: {str(e)}\n{traceback.format_exc()}")
        # Fallback to the other model
        fallback_key = "deepseek" if model_key == "mistral" else "mistral"
        print(f"Falling back to {fallback_key}...")
        init_gpt(fallback_key)

def ask_gpt_short(prompt_text):
    try:
        if gpt is None:
            init_gpt(CURRENT_MODEL)
            if gpt is None:
                return "SRI: Local AI model not available - check console for errors (e.g., download failed, path issue, or insufficient RAM)."
        context_parts = ["You are SRI, a friendly, loyal, helful, kind, female AI assistant. I was created by sai srijan. Address the user as 'sir' and be engaging. Provide accurate, concise answers without repeating previous questions or responses. Stay focused on the current query."]
        for conv in memory[-CONTEXT_MAX:]:
            context_parts.append(f"User: {conv.get('user')}")
            context_parts.append(f"SRI: {conv.get('sri')}")
        context_parts.append(f"User: {prompt_text}\nSRI:")
        full_prompt = "\n".join(context_parts)
        response = gpt.generate(full_prompt, max_tokens=150, temp=0.7, top_k=50, top_p=0.95, repeat_penalty=1.3)
        if isinstance(response, (list, tuple)):
            response = " ".join(map(str, response))
        return str(response).strip()
    except Exception as e:
        return f"SRI AI error: {str(e)}"

# ------------------- OpenRouter Integration (Qwen2.5 72B Online) -------------------
def ask_openrouter(prompt_text):
    if not OPENROUTER_API_KEY:
        return None
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "You are SRI, a friendly, loyal, helful, kind, female AI assistant. I was created by sai srijan. Address the user as 'sir' and be engaging. Provide accurate, concise answers without repeating previous questions or responses. Stay focused on the current query."},
                {"role": "user", "content": prompt_text}
            ],
            "max_tokens": 200,  # Limit for concise responses
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None

def check_internet(host="8.8.8.8", port=53, timeout=2):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception:
        return False

def ask_sri(prompt_text):
    global CURRENT_MODEL
    # Check for offline model switch command
    if prompt_text.lower().startswith("use mistral:"):
        CURRENT_MODEL = "mistral"
        prompt_text = prompt_text[12:].strip()
        init_gpt("mistral")
    elif prompt_text.lower().startswith("use deepseek:"):
        CURRENT_MODEL = "deepseek"
        prompt_text = prompt_text[13:].strip()
        init_gpt("deepseek")
    
    if check_internet():
        reply = ask_openrouter(prompt_text)
        if reply:
            return reply
    return ask_gpt_short(prompt_text)

# ------------------- Command Parser -------------------
def parse_command(command):
    command = (command or "").lower().strip()
    try:
        if "open notepad" in command:
            os.system("notepad"); return "Opening Notepad."
        if "open chrome" in command:
            os.system("start chrome"); return "Opening Chrome."
        if "open word" in command:
            os.system("start winword"); return "Opening Word."
        if "open excel" in command:
            os.system("start excel"); return "Opening Excel."
        if "open paint" in command:
            os.system("mspaint"); return "Opening Paint."
        if "open cmd" in command:
            os.system("start cmd"); return "Opening Command Prompt."
        if "what is the time" in command or "tell me the time" in command:
            return f"The time is {time.strftime('%H:%M:%S')}."
        if command.startswith("create file"):
            filename = command.replace("create file", "").strip('"').strip("'").strip()
            if not filename: return "Specify a filename."
            with open(filename, "w", encoding="utf-8") as f: f.write("")
            return f"File '{filename}' created."
        if command.startswith("delete file"):
            filename = command.replace("delete file", "").strip('"').strip("'").strip()
            if not filename: return "Specify filename to delete."
            if os.path.exists(filename):
                os.remove(filename)
                return f"File '{filename}' deleted."
            return "File not found."
        if command.startswith("open website"):
            url = command.replace("open website", "").strip()
            if not url: return "Specify a website."
            if not url.startswith("http"): url = "https://" + url
            webbrowser.open(url)
            return f"Opening website: {url}"
        if "shutdown" in command:
            os.system("shutdown /s /t 5"); return "Shutting down in 5s."
        if "restart" in command:
            os.system("shutdown /r /t 5"); return "Restarting in 5s."
        return None
    except Exception as e:
        return f"Command error: {e}"

# ------------------- Memory Handling -------------------
def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

memory = load_memory()

# ------------------- Worker & Async Handling -------------------
def handle_user_input_async(user_input):
    try:
        local_resp = parse_command(user_input)
        if local_resp:
            memory.append({"user": user_input, "sri": local_resp})
            if len(memory) > 50: memory[:] = memory[-50:]
            response_queue.put(local_resp)
            return
        answer = ask_sri(user_input)
        prefixes = ["Of course sir!", "Yes sir!", "Consider it done, sir.", "Has you wish sir.", "Right away sir.", "At your service sir., ", "On it, sir!"]
        final_resp = f"{random.choice(prefixes)} {answer}"
        memory.append({"user": user_input, "sri": final_resp})
        if len(memory) > 50: memory[:] = memory[-50:]
        save_memory(memory)
        response_queue.put(final_resp)
    except Exception as e:
        response_queue.put(f"SRI internal error: {e}")

def spawn_response_worker(user_input):
    try:
        model_in_use = "Qwen2.5 72B (OpenRouter)" if check_internet() else CURRENT_MODEL
        response_box.insert("end", f"SRI: ...thinking... \n")
        response_box.see("end")
    except Exception: pass
    threading.Thread(target=handle_user_input_async, args=(user_input,), daemon=True).start()

def poll_responses():
    try:
        while not response_queue.empty():
            resp = response_queue.get_nowait()
            response_box.insert("end", f"SRI: {resp}\n\n")
            response_box.see("end")
            speak_text(resp)
    except Exception: pass
    app.after(500, poll_responses)

# ------------------- Speech Recognition -------------------
recognizer = sr.Recognizer()
mic = sr.Microphone()
listening = False

def listen_loop():
    global listening
    while listening:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                app.after(0, lambda: response_box.insert("end", f"Speech API error: {e}\n"))
                continue
            app.after(0, lambda t=text: process_input(t))
        except Exception:
            continue

def start_listening():
    global listening
    if not listening:
        listening = True
        threading.Thread(target=listen_loop, daemon=True).start()
        response_box.insert("end", "🎤 Listening started...\n")

def stop_listening():
    global listening
    listening = False
    response_box.insert("end", "🛑 Listening stopped.\n")

# ------------------- GUI Setup -------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
app = ctk.CTk()
app.title("SRI - Personal AI Assistant")
app.geometry("1300x750")
app.configure(bg="black")

# Left panel
left_frame = ctk.CTkFrame(app, width=250, corner_radius=15)
left_frame.pack(side="left", fill="y", padx=10, pady=10)
system_label = ctk.CTkLabel(left_frame, text="SYSTEM STATUS", font=("Arial", 18, "bold")); system_label.pack(pady=10)
cpu_label = ctk.CTkLabel(left_frame, text="CPU: --%", font=("Arial", 14)); cpu_label.pack(pady=5)
ram_label = ctk.CTkLabel(left_frame, text="RAM: --%", font=("Arial", 14)); ram_label.pack(pady=5)
battery_label = ctk.CTkLabel(left_frame, text="Battery: --%", font=("Arial", 14)); battery_label.pack(pady=5)
storage_label = ctk.CTkLabel(left_frame, text="Storage: --%", font=("Arial", 14)); storage_label.pack(pady=5)
temp_label = ctk.CTkLabel(left_frame, text="CPU Temp: --°C", font=("Arial", 14)); temp_label.pack(pady=5)
health_label = ctk.CTkLabel(left_frame, text="Device Health: --", font=("Arial", 14)); health_label.pack(pady=5)

# AI input
def process_input(user_input):
    if not user_input.strip(): return
    response_box.insert("end", f"You: {user_input}\n")
    response_box.see("end")
    ai_input.delete(0, "end")
    spawn_response_worker(user_input)

ai_input = ctk.CTkEntry(left_frame, placeholder_text="Type your command...", width=200)
ai_input.pack(pady=20)
ai_input.bind("<Return>", lambda event: process_input(ai_input.get()))
ctk.CTkButton(left_frame, text="Send", command=lambda: process_input(ai_input.get())).pack(pady=5)
ctk.CTkButton(left_frame, text="🎤 Start Listening", command=start_listening).pack(pady=5)
ctk.CTkButton(left_frame, text="🛑 Stop Listening", command=stop_listening).pack(pady=5)

# Right panel
right_frame = ctk.CTkFrame(app, width=350, corner_radius=15)
right_frame.pack(side="right", fill="y", padx=10, pady=10)
time_label = ctk.CTkLabel(right_frame, text="--:--:--", font=("Arial", 24, "bold")); time_label.pack(pady=20)
response_box = ctk.CTkTextbox(right_frame, height=450, width=320); response_box.pack(pady=10, padx=5)

# Camera feed
video_frame = tk.Label(right_frame, bg="black"); video_frame.pack(pady=20)
cap = cv2.VideoCapture(0)
def update_camera():
    try:
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(cv2.flip(frame,1), cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame).resize((400,220)))
            video_frame.imgtk = img
            video_frame.config(image=img)
    except Exception: pass
    video_frame.after(30, update_camera)
update_camera()

# Center orb + stars
center_frame = ctk.CTkFrame(app, corner_radius=15)
center_frame.pack(expand=True, fill="both", padx=10, pady=10)
canvas = tk.Canvas(center_frame, bg="black", highlightthickness=0)
canvas.pack(expand=True, fill="both")
orb_size = 30; num_rings = 6; angle = 0; orb = None; rings = []
num_stars = 120; stars = [[random.randint(0,1300), random.randint(0,750), random.randint(1,3), random.uniform(-0.5,0.5), random.uniform(-0.2,0.2)] for _ in range(num_stars)]

def setup_orb(event=None):
    global orb, rings
    canvas.delete("all")
    w,h = canvas.winfo_width(), canvas.winfo_height()
    cx,cy = w//2,h//2
    orb = canvas.create_oval(cx-orb_size,cy-orb_size,cx+orb_size,cy+orb_size,fill="cyan",outline="")
    rings=[]
    for i in range(num_rings):
        r = 80+i*25
        rings.append(canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline="cyan"))

canvas.bind("<Configure>", setup_orb)
app.update(); setup_orb()

def animate_orb_and_stars():
    global angle
    try:
        w,h = canvas.winfo_width(),canvas.winfo_height(); cx,cy=w//2,h//2
        canvas.delete("star")
        for star in stars:
            x,y,size,dx,dy = star
            star[0]+=dx; star[1]+=dy
            star[0]%=w; star[1]%=h
            canvas.create_oval(star[0]-size,star[1]-size,star[0]+size,star[1]+size,fill="white",outline="",tags="star")
        angle+=2
        canvas.coords(orb,cx-orb_size,cy-orb_size,cx+orb_size,cy+orb_size)
        for i,ring in enumerate(rings):
            r=80+i*25
            canvas.coords(ring,cx-r,cy-r,cx+r,cy+r)
            ci=int(128+127*math.sin(math.radians(angle+(i+1)*10)))
            canvas.itemconfig(ring,outline=f"#00{ci:02x}{255-ci:02x}")
    except Exception: pass
    canvas.after(20,animate_orb_and_stars)

# ------------------- System Info -------------------
def update_info():
    try:
        cpu_label.configure(text=f"CPU: {psutil.cpu_percent()}%")
        ram_label.configure(text=f"RAM: {psutil.virtual_memory().percent}%")
        disk = psutil.disk_usage('C:\\')
        storage_label.configure(text=f"Storage: {disk.percent}% ({disk.used//1024*3}GB/{disk.total//1024*3}GB)")
        temps = getattr(psutil, "sensors_temperatures", lambda: None)()
        try:
            temp_label.configure(text=f"CPU Temp: {list(temps.values())[0][0].current:.1f}°C" if temps else "CPU Temp: N/A")
        except:
            temp_label.configure(text="CPU Temp: N/A")
        batt = psutil.sensors_battery()
        battery_label.configure(text=f"Battery: {batt.percent}%" if batt else "Battery: N/A")
        health_label.configure(text="Device Health: Good" if batt and batt.percent > 20 else "Device Health: Low" if batt else "Device Health: N/A")
        time_label.configure(text=time.strftime("%H:%M:%S"))
    except Exception: pass
    app.after(1000, update_info)

# Start loops
update_info(); animate_orb_and_stars(); poll_responses()
threading.Thread(target=init_gpt, daemon=True).start()

# ------------------- Run App -------------------
try:
    app.mainloop()
finally:
    try: cap.release()
    except Exception: pass
    try: cv2.destroyAllWindows()
    except Exception: pass