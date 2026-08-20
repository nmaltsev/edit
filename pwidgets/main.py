from pwidgets.components.multiline_select import MultilineSelect
from pwidgets.utils.terminal import clear, move_cursor
from pwidgets.data_providers.directory import Directory

def main():
  clear()
  print('start')
  multiline_select = MultilineSelect((2,3,5,5), Directory())
  multiline_select.render()

  multiline_select2 = MultilineSelect((20,3,10,10), Directory())
  multiline_select2.render()

