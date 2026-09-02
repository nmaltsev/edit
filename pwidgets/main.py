import os
from pwidgets.components.multiline_select import MultilineSelect
from pwidgets.components.controller import Controller
#from pwidgets.components import Controller, MultilineSelect
from pwidgets.utils.terminal import clear, move_cursor
from pwidgets.data_providers.directory import Directory

def main():
  clear()
  # print('start')
  multiline_select1 = MultilineSelect((2,3,20,10), Directory(os.getcwd()))
  multiline_select2 = MultilineSelect((25,3,20,10), Directory(os.getcwd()))
  multiline_select3 = MultilineSelect((50,3,20,10), Directory(os.getcwd()))

  app_controller = Controller([multiline_select1, multiline_select2, multiline_select3])
  app_controller.start()
