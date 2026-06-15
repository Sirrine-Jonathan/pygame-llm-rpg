import subprocess
import time
import requests
import json
import threading
import webbrowser
import os
import sys

class OllamaBootstrap:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
        # States: "checking", "starting", "pulling", "not_installed", "not_running", "ready", "offline_fallback"
        self.status = "checking" 
        self.progress = 0.0
        self.error_msg = ""
        self.thread = None
        
    def start_check(self):
        self.thread = threading.Thread(target=self._run_check_flow)
        self.thread.daemon = True
        self.thread.start()
        
    def _run_check_flow(self):
        # 1. Test connection
        if self._test_connection():
            self._check_and_pull_model()
            return
            
        # 2. Try starting Ollama service
        self.status = "starting"
        print("Ollama not responding. Attempting to auto-start service...")
        self._start_service()
        
        # Wait up to 5 seconds for service to start
        for _ in range(5):
            time.sleep(1.0)
            if self._test_connection():
                self._check_and_pull_model()
                return
                
        # 3. Connection failed and couldn't start. Check if installed.
        if self._is_installed():
            self.status = "not_running"
            self.error_msg = "Ollama is installed but the background service could not be started automatically."
        else:
            self.status = "not_installed"
            self.error_msg = "Ollama is not installed on this system. Dynamic LLM dialogues require Ollama."
            
    def _test_connection(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=1.0)
            return r.status_code == 200
        except Exception:
            return False
            
    def _is_installed(self):
        import shutil
        return shutil.which("ollama") is not None
        
    def _start_service(self):
        try:
            # Spawn the subprocess cleanly based on OS
            if sys.platform == "win32":
                subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Failed to start Ollama: {e}")

    def _check_and_pull_model(self):
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=2.0)
            if r.status_code == 200:
                data = r.json()
                models = [m["name"] for m in data.get("models", [])]
                
                # Check for llama3.2 (either latest or exact name)
                if any(m.startswith("llama3.2") for m in models):
                    self.status = "ready"
                    print("Model llama3.2 detected. Ready.")
                    return
                    
                # Model not found: start downloading
                self.status = "pulling"
                print("Model llama3.2 missing. Initiating pull request...")
                self._pull_model()
        except Exception as e:
            self.status = "offline_fallback"
            self.error_msg = f"Error querying models: {e}"

    def _pull_model(self):
        url = f"{self.host}/api/pull"
        payload = {"name": "llama3.2"}
        try:
            # Read progress updates from Ollama response stream
            response = requests.post(url, json=payload, stream=True, timeout=600)
            for line in response.iter_lines():
                if line:
                    decoded = json.loads(line.decode('utf-8'))
                    # Calculate progress percent
                    if "completed" in decoded and "total" in decoded and decoded["total"] > 0:
                        self.progress = (decoded["completed"] / decoded["total"]) * 100
                    # Handle success
                    if decoded.get("status") == "success":
                        self.status = "ready"
                        return
        except Exception as e:
            self.status = "offline_fallback"
            self.error_msg = f"Model download failed: {e}"

    def open_download_page(self):
        webbrowser.open("https://ollama.com/download")
