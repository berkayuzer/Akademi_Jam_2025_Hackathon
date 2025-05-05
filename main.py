import threading
import uvicorn
from api import app
from ui import build_ui

if __name__ == "__main__":
    def run_api():
        uvicorn.run(app, host="0.0.0.0", port=8000)
    threading.Thread(target=run_api, daemon=True).start()
    demo = build_ui()
    demo.launch(server_port=7860)
