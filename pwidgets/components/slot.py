from pwidgets.types import ViewPort
from pwidgets.data_providers.dataprovider import DataProvider
from pwidgets.utils.state import State

class Slot:
  def __init__(self, view_port:ViewPort, data_provider:DataProvider):
    self.view_port = view_port
    self.data_provider = data_provider
    self.state = State(active=False)
    self.state.effect("active", lambda new, old: self.render() if new != old else None)

  def render(self):
    raise Exception('The render method is not implemented')