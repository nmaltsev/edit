from pwidgets.types import ViewPort
from pwidgets.data_providers.dataprovider import DataProvider
from pwidgets.utils.state import State

class Slot:
  def __init__(self, view_port:ViewPort, data_provider:DataProvider):
    self.view_port = view_port
    self.data_provider = data_provider
    self.state = State(active=None)
    self.state.effect("active", lambda new, old: self.render() if new != old else None)

  def render(self):
    raise Exception('The render method is not implemented')

  # def render(self):
  #   lines = ['*', '**', '***', '****']
  #   x, line_number, width, height = self.view_port
  #   view_lines = lines[:self.view_port[3]]
  #   view_lines.extend([''] * (height - len(view_lines)))
  #   #print(view_lines)
  #   #line_number = self.view_port[1]
  #   move_cursor(x, line_number - 1)
  #   print(f"{self.state.active}".ljust(width, ' '))

  #   for line in view_lines:
  #     move_cursor(x, line_number)
  #     print(line[:width].ljust(width, 'X'))
  #     line_number += 1