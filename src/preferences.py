from gi.repository import GLib
import os
import json

class UserPreferences:
    def __init__(self):
        self.preferences = {
            "nsfw": False,
            "doh": False,
            "provider": "Auto",
        }
        self.directory = GLib.get_user_config_dir()
        if os.name == "nt":
            self.directory = os.path.join(self.directory, "Waifu Downloader for Windows")
        os.makedirs(self.directory, exist_ok=True)
        self.file = os.path.join(self.directory, "config.json")
        if not os.path.exists(self.file):
        	f = open(self.file, "w+")
        	f.write(json.dumps(self.preferences))
        	f.close()
        try:
            f = open(self.file, 'r')
            self.preferences = json.loads(f.read())
            f.close()
        except Exception as error:
            print(f"Could not load preferences: {error}")

    def reload_preferences(self):
        try:
            f = open(self.file, 'r')
            self.preferences = json.loads(f.read())
            f.close()
        except Exception as error:
            print(f"Could not reload preferences: {error}")

    def get_preference(self, key):
        self.reload_preferences()
        if key in self.preferences:
            return self.preferences[key]
        else:
            return None
    def set_preference(self, key, value):
        self.preferences[key] = value
        try:
            f = open(self.file, "w+")
            f.write(json.dumps(self.preferences))
            f.close()
        except Exception as error:
            print(f"Could not save preferences: {error}")
