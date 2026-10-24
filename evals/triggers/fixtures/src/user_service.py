class UserRepo:
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id}

    def save_user(self, user: dict) -> None:
        pass


class UserService:
    def __init__(self, repo: UserRepo) -> None:
        self.repo = repo

    def get_user(self, user_id: str) -> dict:
        return self.repo.get_user(user_id)

    def save_user(self, user: dict) -> None:
        return self.repo.save_user(user)
