from .slot import Slot
from pwidgets.utils.terminal import move_cursor

class MultilineSelect(Slot):
  def __init__(self, view_port, data_provider):
    super().__init__(view_port, data_provider)

  def render(self):
    #print(f'TODO {self.viewport=}')
    #move_cursor(*self.viewport[0:2])
    lines = ['*', '**', '***', '****']
    x, line_number, width, height = self.view_port
    view_lines = lines[:self.view_port[3]]
    view_lines.extend([''] * (height - len(view_lines)))
    #print(view_lines)
    #line_number = self.view_port[1]
    move_cursor(x, line_number - 1)
    print(f"{self.state.active}".ljust(width, ' '))

    for line in view_lines:
      move_cursor(x, line_number)
      print(line[:width].ljust(width, 'X'))
      line_number += 1
