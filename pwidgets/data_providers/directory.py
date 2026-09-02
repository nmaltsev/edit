import os
from .dataprovider import DataProvider
from typing import Optional

class Directory(DataProvider):
  def __init__(self, path:str):
    super().__init__()
    self.items = []
    self.path = path

  def refresh(self):
    dirs = []
    files = []

    for name in os.listdir(self.path):
      full = os.path.join(self.path, name)

      if os.path.isdir(full):
        dirs.append(name)
      else:
        files.append(name)

    dirs.sort()
    files.sort()

    self.items = [".."] + dirs + files
  
  def get_item(self, index:int) -> Optional[str]:
    if len(self.items) > index:
      return None
    item = self.items[index]

    if item is None:
      return None
    
    if item == "..":
      return os.path.dirname(self.path)

    return os.path.join(self.path, item)