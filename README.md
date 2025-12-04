# SRI-AI-ASSISTANT

🤖 SRI: The AI Assistant Prototype (Stage 2)
Overview
This repository contains the prototype code for SRI (Intelligent AI Assistant), a multi-functional AI assistant built using Python. SRI aims to provide conversational responses, perform local system commands (like opening applications and managing files), and monitor system health—all within a custom graphical user interface (GUI).

This is a Stage 2 prototype; it is intended for testing and development only. It is not optimized for production and may contain bugs.

✨ Key Features
SRI combines local capabilities with powerful large language models (LLMs) to create a versatile desktop assistant:

Hybrid LLM Integration:

Offline Fallback: Uses GPT4All (specifically Mistral-7B and DeepSeek-7B) for local, private chat when the internet is unavailable or as the default.

Online High-Performance: Integrates with the OpenRouter API to access state-of-the-art models like Qwen 2.5 72B Instruct for superior reasoning and responses when an internet connection is detected.

Voice Interaction: Includes Speech Recognition (via Google API) for verbal input and Text-to-Speech (pyttsx3) for spoken replies.

Local Command Execution: Can execute basic system commands (e.g., open notepad, create file, shutdown).

System Monitoring GUI (CustomTkinter): A dynamic interface that displays real-time system status (CPU, RAM, Battery, Storage, Time) and a live video feed (webcam).

Conversational Memory: Saves and loads conversation history to provide context-aware responses (stored in Data.json).

Visual Feedback: Features an animated, responsive central orb/star field.

⚙️ Requirements & Setup
This prototype relies on several external libraries and local model files.

1. Prerequisites
Python 3.x

Operating System: Windows (many command functions, like os.system("start chrome"), are Windows-specific).

2. Installation
Clone the repository:

Bash

git clone [Your-Repo-URL]
cd SRI-AI-Prototype
Install Python dependencies:

Bash

pip install -r requirements.txt
# (Assuming a requirements.txt with: customkinter, psutil, pyttsx3, opencv-python, Pillow, gpt4all, SpeechRecognition, requests)
Note: The cv2 (OpenCV) dependency is for the camera feed.

GPT4All Models Setup (Crucial for Offline Mode):

The code is configured to look for models in the directory C:/Users/kommi/python project file/models.

You must download the following two GGUF files and place them in that specific path (or update the MODEL_FOLDER variable in sri_ai.py):

Mistral-7B-Instruct-v0.2-Q4_K_M.gguf

deepseek-r1-7b-instruct-Q4_K_M.gguf

OpenRouter API Key (Optional, for Online Mode):

Get an API key from OpenRouter.

Replace "your_openrouter_API_key" in the code with your actual key:

Python

OPENROUTER_API_KEY = "sk-..." # Replace this
▶️ How to Run
Simply execute the main script:

Bash

python sri_ai.py
(Rename your main file to sri_ai.py or use the correct filename.)

The GUI will launch, and the GPT4All model will begin loading in a background thread.

⚠️ Prototype Status & Known Limitations
Resource Intensive: Loading large GGUF models and running the GUI/video feed simultaneously requires significant RAM and CPU resources.

Hardcoded Paths: The MODEL_FOLDER path and local command paths are currently hardcoded for a specific Windows environment.

Limited Error Handling: Robust error handling (especially for external APIs and file operations) is still under development.

No Configuration File: Settings like API keys and model paths are currently managed directly in the script.

🤝 Contribution
As a prototype, this project welcomes feedback and contributions! Feel free to open issues or submit pull requests for:

Improving cross-platform compatibility.

Implementing a proper configuration file (e.g., .env or .json).

Optimizing model loading and memory usage.

Expanding the list of available local commands.
