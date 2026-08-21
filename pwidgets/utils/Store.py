from typing import Any, Callable


class Store:
    def __init__(self, **initial):
        self._values = initial
        self._subscribers: dict[str, list[Callable]] = {}

    def get(self, key: str) -> Any:
        return self._values.get(key)

    def set(self, key: str, value: Any):
        old_value = self._values.get(key)

        # React-like behavior: don't notify if nothing changed.
        if old_value == value:
            return

        self._values[key] = value

        for callback in self._subscribers.get(key, []):
            callback(value, old_value)

    def subscribe(self, key: str, callback: Callable):
        self._subscribers.setdefault(key, []).append(callback)

        # Return an unsubscribe function.
        def unsubscribe():
            subscribers = self._subscribers.get(key, [])
            if callback in subscribers:
                subscribers.remove(callback)

        return unsubscribe