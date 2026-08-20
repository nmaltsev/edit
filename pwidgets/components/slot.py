from pwidgets.types import ViewPort
from pwidgets.data_providers.dataprovider import DataProvider

class Slot:
  def __init__(self, view_port:ViewPort, data_provider:DataProvider):
    self.view_port = view_port
    self.data_provider = data_provider

  def render(self):
    raise Exception('The render method is not implemented')