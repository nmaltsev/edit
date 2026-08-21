class State:
    def __init__(self, **initial):
        self._values = initial
        self._subscribers = {}

    def __getattr__(self, key):
        try:
            return self._values[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        if key.startswith("_"):
            object.__setattr__(self, key, value)
        else:
            self.set(key, value)

    def set(self, key, value):
        old_value = self._values.get(key)

        if old_value == value:
            return

        self._values[key] = value

        for callback in self._subscribers.get(key, []):
            callback(value, old_value)

    def effect(self, key, callback):
        self._subscribers.setdefault(key, []).append(callback)

        def cleanup():
            self._subscribers[key].remove(callback)

        return cleanup