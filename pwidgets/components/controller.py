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
    self._activate(_selected_slot_index)
    
    while True:
      key = read_sequence()
      if key == 'CTRL_Q':
        break
      if prev == 'CTRL_P':
        if key == 'RIGHT':
          _selected_slot_index = (_selected_slot_index + 1) % len(self.slots)
          self._activate(_selected_slot_index)
        elif key == 'LEFT':
          _selected_slot_index = (_selected_slot_index - 1) % len(self.slots)
          self._activate(_selected_slot_index)

      # print(f"{key=} {_selected_slot_index}")
      prev = key

  def _activate(self, active_slot_index):
    for slot_index, slot in enumerate(self.slots):
      # print(f"{slot_index=} {slot=}")
      slot.state.active = slot_index == active_slot_index
    