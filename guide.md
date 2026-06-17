# Edit Text Editor - User Manual

## Overview

`edit` is a terminal-based text editor with an integrated file browser.

The application starts in **File Browser Mode** and allows creating, opening, editing, renaming, deleting, and searching files directly from the terminal.

---

# Launching the Application

## Launch as a Python Module

```bash
python -m edit
```

Starts the application in the current working directory.

---

## Open a File Directly

```bash
python -m edit path/to/file.txt
```

The file is loaded immediately and the editor opens in Edit Mode.

---

## Open a Directory

```bash
python -m edit path/to/directory
```

The file browser starts in the specified directory.

---

## Launch from Source

```bash
python edit/__main__.py
```

Starts the application using the default configuration:

```python
USE_TAB = False
TAB_SIZE = 2
```

---

# Application Modes

## File Browser Mode

Used to:

* Navigate directories
* Open files
* Create files
* Create directories
* Rename files/directories
* Delete files/directories
* Search files by name

---

## Edit Mode

Used to edit file contents.

Supports:

* Text insertion
* Selection
* Copy/Cut/Paste
* Indentation
* Navigation
* Saving

---

## Log Mode

Debug mode that displays raw key events.

---

## Modal Mode

Used for confirmation dialogs such as:

* Close editor confirmation
* Exit confirmation

---

# Global Hotkeys

These hotkeys work regardless of the current editor content.

| Hotkey      | Description                                                 |
| ----------- | ----------------------------------------------------------- |
| `CTRL_R`    | Refresh screen and recalculate layout after terminal resize |
| `ALT+RIGHT` | Toggle between File Browser Mode and Edit Mode              |
| `CTRL_P`    | Toggle Edit Mode ⇄ Log Mode                                 |

---

# File Browser Mode Hotkeys

## Navigation

| Hotkey  | Description                                    |
| ------- | ---------------------------------------------- |
| `UP`    | Move selection up                              |
| `DOWN`  | Move selection down                            |
| `ENTER` | Open selected file or enter selected directory |

---

## File Operations

| Hotkey   | Description                       |
| -------- | --------------------------------- |
| `CTRL_N` | Create new file                   |
| `CTRL_D` | Create new directory              |
| `CTRL_E` | Rename selected file or directory |
| `DELETE` | Delete selected file or directory |
| `CTRL_P` | Search files by filename pattern  |

---

## Editor Creation

| Hotkey  | Description                              |
| ------- | ---------------------------------------- |
| `ALT+N` | Create a new empty document (`Untitled`) |

---

## Application Exit

| Hotkey         | Description                     |
| -------------- | ------------------------------- |
| `CTRL_Q`       | Press once to show exit warning |
| `CTRL_Q` twice | Exit application                |

Message shown:

```text
Press CTRL_Q again to exit
```

---

# Edit Mode Hotkeys

## File Operations

| Hotkey   | Description          |
| -------- | -------------------- |
| `CTRL_S` | Save current file    |
| `ALT+S`  | Save As              |
| `CTRL_Q` | Close current editor |

### Close Editor Behavior

If the document contains unsaved changes:

```text
Save before close? y/n
```

* `y` → save and close
* any other key → cancel close

If there are no unsaved changes:

* editor closes immediately
* returns to File Browser Mode

---

## Selection

| Hotkey            | Description                           |
| ----------------- | ------------------------------------- |
| `SHIFT+LEFT`      | Extend selection left                 |
| `SHIFT+RIGHT`     | Extend selection right                |
| `SHIFT+UP`        | Extend selection upward               |
| `SHIFT+DOWN`      | Extend selection downward             |
| `SHIFT+HOME`      | Extend selection to beginning of line |
| `SHIFT+END`       | Extend selection to end of line       |
| `SHIFT+PAGE_UP`   | Extend selection one page up          |
| `SHIFT+PAGE_DOWN` | Extend selection one page down        |
| `CTRL_A`          | Select entire document                |

---

## Clipboard

| Hotkey   | Description              |
| -------- | ------------------------ |
| `CTRL_C` | Copy selection           |
| `CTRL_X` | Cut selection            |
| `CTRL_V` | Paste clipboard contents |

Clipboard uses:

* macOS: `pbcopy` / `pbpaste`
* Linux: `xclip`
* Internal clipboard fallback if OS clipboard is unavailable

---

## Indentation

| Hotkey               | Description             |
| -------------------- | ----------------------- |
| `TAB`                | Insert indentation      |
| `TAB` with selection | Indent selected lines   |
| `[Z` with selection  | Unindent selected lines |

Indentation uses:

* tab character when `use_tab=True`
* spaces when `use_tab=False`

---

## Text Editing

| Hotkey                  | Description                    |
| ----------------------- | ------------------------------ |
| Any printable character | Insert character               |
| `ENTER`                 | Insert new line                |
| `BACKSPACE`             | Delete character before cursor |
| `DELETE`                | Delete character at cursor     |

---

## Cursor Movement

| Hotkey      | Description               |
| ----------- | ------------------------- |
| `LEFT`      | Move cursor left          |
| `RIGHT`     | Move cursor right         |
| `UP`        | Move cursor up            |
| `DOWN`      | Move cursor down          |
| `HOME`      | Move to beginning of line |
| `END`       | Move to end of line       |
| `PAGE_UP`   | Move one page up          |
| `PAGE_DOWN` | Move one page down        |

---

# Log Mode Hotkeys

| Hotkey         | Description                |
| -------------- | -------------------------- |
| Any key        | Display detected key value |
| `CTRL_W`       | Clear log screen           |
| `CTRL_T` twice | Display terminal size      |

Example:

```text
columns: 120 lines: 40
```

---

# Status Information

## Top Status Line

Displays:

```text
<current_directory>|<opened_file>
```

Example:

```text
/home/user/projects|main.py
```

---

## Editor Status Line

Displays:

### Cursor Position

```text
(line:column) 'character' filename
```

Example:

```text
(10:5) 'a' main.py
```

### Selection

```text
(start_row,start_col,end_row,end_col) filename
```

Example:

```text
(2,1,8,12) main.py
```

### Modified File

Unsaved files are marked with:

```text
*
```

Example:

```text
main.py*
```

---

# Current Application Termination Flow

## From File Browser

1. Press `CTRL_Q`
2. Warning appears

```text
Press CTRL_Q again to exit
```

3. Press `CTRL_Q` again
4. Application terminates

---

## From Edit Mode

1. Press `CTRL_Q`

### If file is modified

```text
Save before close? y/n
```

* `y` saves file and closes editor
* editor returns to File Browser

### If file is not modified

* editor closes immediately
* returns to File Browser

The application itself is not terminated from Edit Mode.

---

# Supported Platforms

## macOS

Clipboard support via:

```bash
pbcopy
pbpaste
```

---

## Linux

Clipboard support via:

```bash
xclip
```

Install if necessary:

```bash
sudo apt install xclip
```

---

# Default Configuration

```python
USE_TAB = False
TAB_SIZE = 2
```

Meaning:

* indentation uses spaces
* one indentation level equals two spaces
