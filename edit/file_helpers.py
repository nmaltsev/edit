import os
import shutil

def load_file(path:str):
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:
            lines = f.read().splitlines()
        return lines or [""]
    return [""]


def save_file(path:str, doc_lines: list[str]):
    with open(path,"w",encoding="utf-8") as f:
        f.write("\n".join(doc_lines))

def rm_path(path:str):
    if os.path.isdir(path):
        shutil.rmtree(path)
    elif os.path.exists(path):
        os.remove(path)