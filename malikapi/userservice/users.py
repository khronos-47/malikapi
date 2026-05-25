# malikapi/userservice/users.py
from datetime import datetime
import uuid
import hashlib
from typing import List, Optional
from userservice.reader import SimpleUserStorage

storage = SimpleUserStorage()

class Users:
    def __init__(self, username: str, password: Optional[str] = None, create_if_missing: bool = True):
        self.username = username
        existing = storage.get_user(username)
        if existing:
            # загружаем существующего пользователя
            self.user = existing
            # если передан пароль и он не совпадает – можно выбросить ошибку
            if password and not self.check_password(password):
                raise ValueError("Invalid password")
        elif create_if_missing:
            # создаём нового
            _uuid = str(uuid.uuid4())
            # записываем uuid в uuids.txt (сохраняем логику из оригинального кода)
            with open('uuids.txt', 'a') as f:
                f.write(_uuid + '\n')
            self.user = {
                'username': username,
                'password': self._hash_password(password) if password else None,
                'status': {'user_status': 'default', 'banned': {}},
                'uuid': _uuid,
                'tables': {},
                'requests': [],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        else:
            raise KeyError(f"User {username} not found")

    # ---------- Вспомогательные методы ----------
    @staticmethod
    def _hash_password(pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()

    def check_password(self, pwd: str) -> bool:
        if not self.user.get('password'):
            return False
        return self.user['password'] == self._hash_password(pwd)

    def save(self):
        self.user['updated_at'] = datetime.now().isoformat()
        storage.save_user(self.username, self.user)

    # ---------- Управление таблицами ----------
    def add_table(self, table_name: str):
        if table_name not in self.user['tables']:
            self.user['tables'][table_name] = {'columns': []}  # [] = все колонки
            self.save()

    def remove_table(self, table_name: str):
        if table_name in self.user['tables']:
            del self.user['tables'][table_name]
            self.save()

    # Grant / revoke на уровне колонок
    def grant_columns(self, table_name: str, columns: List[str]):
        if table_name not in self.user['tables']:
            self.add_table(table_name)
        # если columns == [] – разрешаем все колонки
        current = self.user['tables'][table_name]['columns']
        if current == []:
            # уже всё разрешено
            return
        for col in columns:
            if col not in current:
                current.append(col)
        self.save()

    def revoke_columns(self, table_name: str, columns: List[str]):
        if table_name not in self.user['tables']:
            return
        current = self.user['tables'][table_name]['columns']
        if current == []:
            # запретить всё, кроме явно перечисленных? По логике: если был полный доступ,
            # после revoke можно установить список только разрешённых (пустой = ничего)
            self.user['tables'][table_name]['columns'] = []
        else:
            for col in columns:
                if col in current:
                    current.remove(col)
        self.save()

    # ---------- Управление статусом и баном ----------
    def set_status(self, status: str):
        self.user['status']['user_status'] = status
        self.save()

    def ban(self, reason: str = ""):
        self.user['status']['banned'] = {'reason': reason, 'banned_at': datetime.now().isoformat()}
        self.save()

    def unban(self):
        self.user['status']['banned'] = {}
        self.save()

    # ---------- Логирование запросов ----------
    def add_request(self, request_data: dict):
        """request_data может содержать: endpoint, query, params, timestamp, result_rows_count"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            **request_data
        }
        self.user['requests'].append(entry)
        self.save()
    def cleanup_requests(self, keep_last: int = 1000):
        """Оставляет только последние keep_last записей в requests"""
        if len(self.user.get('requests', [])) > keep_last:
            self.user['requests'] = self.user['requests'][-keep_last:]
            self.save()