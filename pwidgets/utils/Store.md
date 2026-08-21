state = Store(
    count=0,
    name="Alice",
)


def on_count_changed(new_value, old_value):
    print(f"count changed: {old_value} -> {new_value}")


unsubscribe = state.subscribe("count", on_count_changed)

state.set("count", 1)
# count changed: 0 -> 1

state.set("count", 2)
# count changed: 1 -> 2

state.set("name", "Bob")
# nothing happens

state.set("count", 2)
# nothing happens because the value didn't actually change

unsubscribe()

state.set("count", 3)
# nothing happens