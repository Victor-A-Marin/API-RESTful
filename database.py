from datetime import datetime
from typing import Optional, Dict, Any, List

class InMemoryUserRepository:
    def __init__(self) -> None:
        self._db: Dict[int, Dict[str, Any]] = {}
        self._current_id = 1

    def save(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        if user_data.get("id") is None:
            user_data["id"] = self._current_id
            user_data["deleted_at"] = None
            self._db[self._current_id] = user_data
            self._current_id += 1
        else:
            existing = self._db.get(user_data["id"], {})
            if "deleted_at" not in user_data:
                user_data["deleted_at"] = existing.get("deleted_at")
            self._db[user_data["id"]] = user_data
        return self._db[user_data["id"]]

    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._db.get(user_id)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for user in self._db.values():
            if user["email"] == email:
                return user
        return None

    def delete(self, user_id: int) -> bool:
        if user_id in self._db:
            self._db[user_id]["deleted_at"] = datetime.utcnow().isoformat()
            return True
        return False

class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._db: Dict[int, Dict[str, Any]] = {}
        self._current_id = 1

    def save(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        if task_data.get("id") is None:
            task_data["id"] = self._current_id
            self._db[self._current_id] = task_data
            self._current_id += 1
        else:
            self._db[task_data["id"]] = task_data
        return self._db[task_data["id"]]

    def find_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self._db.get(task_id)

    def find_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        return [task for task in self._db.values() if user_id in task.get("user_ids", [])]

    def delete(self, task_id: int) -> bool:
        if task_id in self._db:
            del self._db[task_id]
            return True
        return False