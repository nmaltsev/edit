import sys
import tty
import termios


KEY_MAP = {
  9: 'TAB', # the same as Ctrl_I !
  13: 'ENTER',
  #27: 'ESC',
  # 32: 'SPACE',
  127: 'BACKSPACE',
}

def litter_key(code:int):
  if code == 65:
    return 'UP'
  if code == 66:
    return 'DOWN'
  if code == 67:
    return 'RIGHT'
  if code == 68:
    return 'LEFT'
  return None

def read_sequence():
    seq = []
    c = 0
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
      tty.setraw(fd)
      while True and c < 6:
          ch = sys.stdin.read(1)
          code = ord(ch)
          
          if c == 0 and (31 < code < 127):
            return ch

          if c == 0 and code in KEY_MAP:
            return KEY_MAP[code]

          # does not distingush Ctrl + a and ctrl + A 
          if c == 0 and (0 < code < 27):
            # Does not detect Ctrl+I
            return f"CTRL_{chr(code + 64)}"
          
          if c == 1 and (0 < code < 27) and seq[0] == 27:
            # Does not detect Ctrl+I
            return f"ALT+CTRL_{chr(code + 64)}"

          print(f"{code=} {c=}", file=sys.stderr)
          seq.append(code)
          c+=1
    finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old)

    return str(seq)


prev = None
while True:
  fd = sys.stdin.fileno()
  old = termios.tcgetattr(fd)
  seq = read_sequence()
  if seq == 'Q' and prev == 'Q':
    break
  print(f'{seq=}')
  prev = seq