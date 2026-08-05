import random

def find_files(path, pattern):
    n = len(pattern) * 3
    return [str(random.randint(0, 100000)) for _ in range(n)]