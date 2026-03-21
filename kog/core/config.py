import os
import json
from pathlib import Path

class ConfigManager:
    def __init__(self):
        self.base_dir = Path.home() / ".kog"
        self.sessions_file = self.base_dir / "sessions.json"
        self.contexts_file = self.base_dir / "contexts.json"
        self.chroma_dir = self.base_dir / "chroma"
        self.ensure_directories()

    def ensure_directories(self):
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.sessions_file.exists():
            with open(self.sessions_file, "w") as f:
                json.dump({"current_session": None, "sessions": {}}, f)
                
        if not self.contexts_file.exists():
            with open(self.contexts_file, "w") as f:
                json.dump({"contexts": {}}, f)
                
config = ConfigManager()
