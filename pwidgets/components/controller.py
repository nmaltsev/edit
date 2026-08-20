from typing import List
from pwidgets.components.slot import Slot
from pwidgets.utils.kbd import read_sequence

class Controller:
  def __init__(self, slots: List[Slot]):
    self.slots = slots
    #self.active_widget = slots[0] if len(slots) > 0 else None

  def start(self):
    prev = None
    _selected_slot_index = 0
    
    while True:
      key = read_sequence()
      if key == 'CTRL_Q':
        break
      if prev == 'CTRL_P':
        if key == 'RIGHT':
          _selected_slot_index = (_selected_slot_index + 1) % len(self.slots)
        elif key == 'LEFT':
          _selected_slot_index = (_selected_slot_index - 1) % len(self.slots)

      print(f"{key=} {_selected_slot_index}")
      prev = key

    