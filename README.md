# silver's Anti-AFK

**silver's Anti-AFK** is a desktop application designed to prevent AFK (Away From Keyboard) detection in games or other applications. It works by simulating in-game actions, such as camera movements and button presses, at customizable intervals.

The program includes a user-friendly graphical interface, a system tray icon for quick access, and hotkey support for control without needing to bring the window to the foreground.

## Features

  * **Customizable Intervals:** Set the time between automated actions.

  * **Adjustable Actions:** Control the duration and radius of the simulated camera turns and button presses.

  * **Hotkey Support:** Use a set of pre-defined hotkeys to control the application from anywhere.

  * **Target Window Detection:** Automatically and accurately targets the game window to ensure actions are sent to the correct application.

  * **System Tray Icon:** Minimize the application to your system tray for discreet use.

  * **Configuration File:** All settings and hotkeys are saved to an `options.ini` file for persistent settings.

## How to Use

### 1\. Installation

This program requires Python to be installed on your system. It also has a few dependencies that you'll need to install:

```
pip install pywin32 pyinstaller pillow pystray keyboard vgamepad sv-ttk
```

You will also need to install the **ViGEmBus driver**. The `vgamepad` library relies on this to create a virtual Xbox 360 controller. You can find the driver on its official GitHub page.

### 2\. Running the Program

Once you have the dependencies installed, simply run the main script:

```
python afk.py
```

### 3\. Using the GUI

  * **Controls Tab:**

      * **Set Target Window:** Use the dedicated hotkey to make your currently active window the target for the simulated actions. The program will display the target window's title and process name.

      * **Start/Stop Auto Action:** Click the button or use the hotkey to toggle the automatic actions.

      * **Manual Action:** Instantly perform a single set of actions.

      * **Settings:** Adjust the interval between actions, the duration and radius of camera movements, and the number of loops for the simulated actions.

  * **Keybinds Tab:**

      * Click the "Change" button next to a hotkey to assign a new key combination.

## Compiling to an Executable

You don't need to distribute your Python files\! The project includes a `build.py` script and a `compile.bat` file to create a single, standalone executable using **PyInstaller**.

### How to Compile

1.  Make sure you have all the dependencies listed in the "Installation" section.

2.  Run the `compile.bat` file.

The script will automatically install all necessary dependencies, run the `build.py` file, and create an executable file named `silver's Anti-AFK.exe` in the `dist/` folder.

## Trademark and Licensing

This project's name, **"silver's Anti-AFK,"** is a trademark. Please refer to the `TRADEMARK.md` file for details on the proper use of the name when distributing modified versions of this software.

## Credits

  * **Author:** silver

  * **Contact:** argentum\_47 on Discord

  * **Libraries Used:** `tkinter`, `vgamepad`, `pywin32`, `keyboard`, `pystray`, `Pillow`, `sv-ttk`.

<!-- end list -->

```
```