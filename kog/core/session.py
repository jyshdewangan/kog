import json
from typing import List, Optional, Dict
from kog.core.config import config

class SessionManager:
    def __init__(self):
        self.sessions_file = config.sessions_file

    def _load_data(self) -> dict:
        try:
            with open(self.sessions_file, "r") as f:
                return json.load(f)
        except Exception:
            return {"current_session": None, "sessions": {}}

    def _save_data(self, data: dict):
        with open(self.sessions_file, "w") as f:
            json.dump(data, f, indent=4)

    def get_current_session(self) -> Optional[str]:
        data = self._load_data()
        return data.get("current_session")

    def list_sessions(self) -> Dict[str, dict]:
        return self._load_data().get("sessions", {})

    def set_current_session(self, name: str) -> None:
        data = self._load_data()
        if name not in data.get("sessions", {}):
            raise ValueError(f"Session '{name}' does not exist.")
        data["current_session"] = name
        self._save_data(data)

    def create_session(self, name: str, set_as_current: bool = True) -> None:
        data = self._load_data()
        if "sessions" not in data:
            data["sessions"] = {}
        if name not in data["sessions"]:
            data["sessions"][name] = {"contexts": []}
        if set_as_current:
            data["current_session"] = name
        self._save_data(data)

    def delete_session(self, name: str) -> bool:
        data = self._load_data()
        if name in data.get("sessions", {}):
            del data["sessions"][name]
            if data.get("current_session") == name:
                data["current_session"] = None
            self._save_data(data)
            return True
        return False

    def add_context_to_session(self, session_name: str, context_name: str) -> None:
        data = self._load_data()
        if session_name not in data.get("sessions", {}):
            self.create_session(session_name, set_as_current=False)
            data = self._load_data() # reload
            
        contexts = data["sessions"][session_name].setdefault("contexts", [])
        if context_name not in contexts:
            contexts.append(context_name)
            self._save_data(data)

    def remove_context_from_session(self, session_name: str, context_name: str) -> bool:
        data = self._load_data()
        session = data.get("sessions", {}).get(session_name)
        if session and "contexts" in session:
            if context_name in session["contexts"]:
                session["contexts"].remove(context_name)
                self._save_data(data)
                return True
        return False

    def get_session_contexts(self, session_name: str) -> List[str]:
        data = self._load_data()
        session = data.get("sessions", {}).get(session_name)
        if session:
            return session.get("contexts", [])
        return []

    def load_session(self, name: str) -> bool:
        # returns True if loaded, False if not found
        data = self._load_data()
        if name in data.get("sessions", {}):
            self.set_current_session(name)
            return True
        return False

    def remove_context_from_all_sessions(self, context_name: str) -> None:
        data = self._load_data()
        changed = False
        for session_data in data.get("sessions", {}).values():
            if "contexts" in session_data and context_name in session_data["contexts"]:
                session_data["contexts"].remove(context_name)
                changed = True
        if changed:
            self._save_data(data)

session_manager = SessionManager()
