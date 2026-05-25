# malikapi/cli/app.py
import typer
from malikapi.userservice.users import Users
from typing import List
user_app = typer.Typer(help="User management")

@user_app.command()
def create(
    name: str,
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
    role: str = typer.Option("reader"),
):
    """Создать нового пользователя"""
    user = Users(name, password=password, create_if_missing=True)
    user.add_table("kaltable")   # пример, можно убрать или сделать опциональным
    user.save()
    print(f"✅ User {name} created (role={role})")

@user_app.command()
def delete(name: str):
    """Удалить пользователя"""
    # Просто удаляем из storage – реализуем метод в SimpleUserStorage
    storage = Users(name, create_if_missing=False)._storage  # некрасиво, лучше добавить метод в storage
    # Упростим: добавим метод delete_user в reader.py
    from malikapi.userservice.reader import SimpleUserStorage
    s = SimpleUserStorage()
    s.delete_user(name)
    print(f"🗑️ User {name} deleted")

@user_app.command()
def list():
    """Список всех пользователей (только username, статус)"""
    from malikapi.userservice.reader import SimpleUserStorage
    s = SimpleUserStorage()
    users = s.get_all_users()
    for name, data in users.items():
        status = data.get('status', {}).get('user_status', 'unknown')
        banned = 'banned' if data.get('status', {}).get('banned') else 'active'
        print(f"{name} | status: {status} | {banned}")

@user_app.command()
def grant_table(name: str, table: str):
    """Выдать доступ к таблице (все колонки)"""
    user = Users(name, create_if_missing=False)
    user.add_table(table)
    print(f"🔓 Granted full access to {table} for {name}")

@user_app.command()
def revoke_table(name: str, table: str):
    """Забрать доступ к таблице"""
    user = Users(name, create_if_missing=False)
    user.remove_table(table)
    print(f"🔒 Revoked access to {table} for {name}")

@user_app.command()
def grant_columns(name: str, table: str, columns: List[str] = typer.Argument(..., help="Space-separated column names")):
    """Выдать доступ к конкретным колонкам таблицы"""
    user = Users(name, create_if_missing=False)
    user.grant_columns(table, columns)
    print(f"🔓 Granted columns {columns} on {table} to {name}")

@user_app.command()
def revoke_columns(name: str, table: str, columns: List[str] = typer.Argument(...)):
    """Забрать доступ к колонкам"""
    user = Users(name, create_if_missing=False)
    user.revoke_columns(table, columns)
    print(f"🔒 Revoked columns {columns} on {table} from {name}")

@user_app.command()
def ban(name: str, reason: str = typer.Option("no reason")):
    """Забанить пользователя"""
    user = Users(name, create_if_missing=False)
    user.ban(reason)
    print(f"⛔ User {name} banned (reason: {reason})")

@user_app.command()
def unban(name: str):
    """Разбанить"""
    user = Users(name, create_if_missing=False)
    user.unban()
    print(f"✅ User {name} unbanned")

@user_app.command()
def set_status(name: str, status: str):
    """Установить статус (active, readonly, etc.)"""
    user = Users(name, create_if_missing=False)
    user.set_status(status)
    print(f"🔄 User {name} status set to {status}")

# Основное приложение
app = typer.Typer(help="Replication Service CLI")
app.add_typer(user_app, name="user")

def run():
    app()

if __name__ == "__main__":
    run()