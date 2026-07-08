import sys
import tty
import termios


KEY_MAP = {
  9: 'TAB', # the same as Ctrl_I !
  13: 'ENTER',
  #27: 'ESC',
  32: 'SPACE',
}


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
          
          if (
            c == 0 and (32 < code < 129)):
            return ch

          if c == 0 and code in KEY_MAP:
            return KEY_MAP[code]

          if c == 0 and (0 < code < 27):
            # Does not detect Ctrl+I
            return f"CTRL_{chr(code + 64)}"

          print(f"{code=} {c=}", file=sys.stderr, end='\n')
          seq.append(code)
  
          c+=1
    finally:
      termios.tcsetattr(
          fd,
          termios.TCSADRAIN,
          old,
      )

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
