## Arrow combinations

27,91,65 up
27,91,49,59,50,65 shift up
27,91,49,59,53,65 ctrl up
27,91,49,59,51,65 alt up
27,91,65 ctrl shift up (undetectable combination!)
27,91,49,59,50,65 shift alt up (undetectable combination!)
27,91,49,59,53,65 ctrl alt up (undetectable combination!)

27,91,66 down
27,91,49,59,50,66 shift down
27,91,49,59,53,66 ctrl down
27,91,49,59,51,66 alt down

27,91,67 right
27,91,68 left

-----

27, 102 Ctrl F
27, 6 Ctrl Alt F


\033[0K Clear from cursor to end of line
print("\033[1K", end="", flush=True) # \033[1K Clear from beginning of line to cursor
print("\033[2K", end="", flush=True) # Clear the entire line
	