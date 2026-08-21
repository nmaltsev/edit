state = State(count=0, name="Alice")

state.effect(
    "count",
    lambda new, old: print(f"count: {old} -> {new}")
)

state.count = 1
state.count = 2
state.name = "Bob"
