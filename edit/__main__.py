from .main import main
from .syntax_highlighting import ENABLE_SYNTAX_HIGHLIGHTING
__version__ = '5.2026.06.17'

if __name__ == '__main__':
    USE_TAB = False
    TAB_SIZE = 2
    main(use_tab = USE_TAB, tab_size = TAB_SIZE)