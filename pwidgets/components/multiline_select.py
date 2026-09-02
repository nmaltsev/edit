from .slot import Slot
from pwidgets.utils.terminal import move_cursor
from pwidgets.utils.ui import trim_name, fill

class MultilineSelect(Slot):
  def __init__(self, view_port, data_provider):
    super().__init__(view_port, data_provider)
    self.update()
    self.state.effect("scroll_offset", lambda new, old: self.render() if new != old else None)
    self.state.effect("selected_index", lambda new, old: self.render() if new != old else None)

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


  def render(self):
    x, y, w, h = self.view_port
    visible = self.data_provider.items[self.state.scroll_offset:self.state.scroll_offset + h]

    move_cursor(x, y - 1)
    print(f"{self.state.active}".ljust(w, ' '))

    for row in range(h):
      move_cursor(x, y + row)
      idx = self.state.scroll_offset + row

      if idx < len(self.data_provider.items):
        name = self.data_provider.items[idx]
        prefix = ">" if idx == self.state.selected_index else " "
        text = prefix + trim_name(name, w - 1)
      else:
        text = ""

      print(fill(text, w), end="")
    # sys.stdout.flush()

  
  def refresh(self):
    self.data_provider.refresh()

    if self.state.selected_index >= len(self.data_provider.items):
      self.state.selected_index = max(0, len(self.data_provider.items) - 1)

  def update(self, *args, **kargs):
    if len(args) > 0 or len(kargs) > 0:
      self.data_provider.__init__(*args, **kargs)
    self.state.selected_index = 0
    self.state.scroll_offset = 0
    self.refresh()

  def handle_keypress(self, key: str):
    if key == "UP":
      if self.state.selected_index > 0:
        self.state.selected_index -= 1

        if self.state.selected_index < self.state.scroll_offset:
          self.state.scroll_offset -= 1

    if key == "HOME":
      self.state.selected_index = self.state.scroll_offset = 0

    elif key == "DOWN":
      if self.state.selected_index < len(self.data_provider.items) - 1:
        self.state.selected_index += 1
        bottom = self.state.scroll_offset + self.view_port[3]

        if self.state.selected_index >= bottom:
          self.state.scroll_offset += 1

    elif key == "ENTER":
      pass
        # path = browser.current_full_path()

        # if os.path.isdir(path):
        #     browser.current_path = path
        #     browser.selected_index = 0
        #     browser.scroll_offset = 0
        #     browser.refresh()

        # elif os.path.isfile(path):
        #     return ("OPEN_FILE", path)