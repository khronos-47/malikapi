import json
import os
import fcntl
from typing import Dict, List
from datetime import datetime

class SimpleUserStorage:
    def __init__(self, filename='cli/users.json'):
        self.filename = filename
        self._ensure_file()
    
    def _ensure_file(self):
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                json.dump({}, f)  # Пустой словарь
    
    def _lock_file(self, fd, exclusive=True):
        fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    
    def _unlock_file(self, fd):
        fcntl.flock(fd, fcntl.LOCK_UN)
    
    def save_user(self, username: str, user_data: Dict):
        with open(self.filename, 'r+') as f:
            self._lock_file(f.fileno())
            try:
                data = json.load(f)
                data[username] = {
                    **user_data,
                    'updated_at': datetime.now().isoformat()
                }
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            finally:
                self._unlock_file(f.fileno())
    
    def get_user(self, username: str) -> Dict:
        with open(self.filename, 'r') as f:
            self._lock_file(f.fileno(), exclusive=False)
            try:
                data = json.load(f)
                print(data)
                return data.get(username)
            finally:
                self._unlock_file(f.fileno())
    
    def get_all_users(self) -> Dict:
        with open(self.filename, 'r') as f:
            self._lock_file(f.fileno(), exclusive=False)
            try:
                return json.load(f)
            finally:
                self._unlock_file(f.fileno())
    
    def delete_user(self, username: str):
        with open(self.filename, 'r+') as f:
            self._lock_file(f.fileno())
            try:
                data = json.load(f)
                if username in data:
                    del data[username]
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
            finally:
                self._unlock_file(f.fileno())

