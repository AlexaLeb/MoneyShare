from repositories import UsersRepoSqlModel


def format_user(user_id: int, users_repo: UsersRepoSqlModel) -> str:
    """
    Возвращает удобное имя пользователя для отображения по user_id.
    Использует репозиторий UsersRepoSqlModel для поиска в БД.
    """
    user = users_repo.get(user_id)
    if not user:
        return f"❓{user_id}"
    if user.first_name:
        return f"<b>{user.first_name}</b>"
    elif user.username:
        return f"@{user.username}<"
    return str(user.id)
