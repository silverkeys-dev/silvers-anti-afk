# build.py - A more reliable script for compiling the application.
# This script uses Python and pathlib to find necessary paths and run PyInstaller,
# avoiding the inconsistencies of batch file commands.

import PyInstaller.__main__
import os
import sys
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).parent
SCRIPT_NAME = Path('afk.py')
EXECUTABLE_NAME = "silver's Anti-AFK"
ASSETS_FOLDER = Path('assets')
ICON_FILE = Path('off.ico')

def build():
    """
    Finds all necessary paths and runs PyInstaller with the correct configuration.
    """
    print("--- Starting Build Process ---")
    
    script_path = ROOT_DIR / SCRIPT_NAME
    if not script_path.exists():
        print(f"ERROR: The main script '{script_path}' was not found.")
        sys.exit(1)

    # 1. Locate the vgamepad package to include its necessary DLLs
    try:
        import vgamepad
        vgpad_path = Path(vgamepad.__file__).parent.resolve()
        print(f"Found vgamepad library at: {vgpad_path}")
    except (ImportError, ModuleNotFoundError):
        print("ERROR: Could not find the 'vgamepad' library.")
        print("Please run 'pip install vgamepad' and try again.")
        sys.exit(1)

    # 2. Construct paths for PyInstaller arguments
    icon_path = ROOT_DIR / ASSETS_FOLDER / ICON_FILE
    
    # os.pathsep is the correct separator (';' on Windows, ':' on Linux/Mac)
    pyinstaller_args = [
        str(script_path),
        '--onefile',
        '--windowed',
        f'--name={EXECUTABLE_NAME}',
        f'--add-data={ASSETS_FOLDER}{os.pathsep}{ASSETS_FOLDER}',
        f'--add-data={vgpad_path}{os.pathsep}vgamepad',
        '--clean',
    ]

    # 3. Add the icon argument only if the icon file actually exists
    if icon_path.exists():
        print(f"Using icon: {icon_path}")
        pyinstaller_args.append(f'--icon={icon_path}')
    else:
        print(f"WARNING: Icon file not found at '{icon_path}'. A default icon will be used.")

    # 4. Run PyInstaller
    print("\n--- Running PyInstaller with the following arguments ---")
    for arg in pyinstaller_args:
        print(f"  {arg}")
    print("------------------------------------------------------\n")

    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("\n--- Compilation Successful! ---")
        print(f"Executable is located in: dist\\{EXECUTABLE_NAME}.exe")
    except Exception as e:
        print("\n--- PyInstaller Error ---")
        print(e)
        print("-------------------------\n")
        sys.exit(1)

if __name__ == '__main__':
    # Pre-flight check for dependencies before starting the build
    try:
        from PIL import Image
        import pystray
        import keyboard
        import win32gui
    except ImportError as e:
        print(f"Error: A required library is missing: {e.name}")
        print("Please run 'pip install --upgrade pywin32 pillow pystray keyboard' and try again.")
        sys.exit(1)
        
    build()