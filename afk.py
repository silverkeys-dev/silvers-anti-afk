# afk.py - Refactored Version with sv-ttk Theme and UI Polish
# A tool to automate game actions with a GUI for control.

import tkinter as tk
from tkinter import messagebox, ttk, font as tkfont
import time
import threading
import keyboard
import win32gui
import win32con
import win32api
import win32process
import configparser
import os
import sys
import math
from PIL import Image, ImageTk
import pystray
from typing import Optional

# --- NEW IMPORT ---
import sv_ttk
# ------------------

try:
    import vgamepad as vg
except ImportError:
    messagebox.showerror("Dependency Missing", "vgamepad library is required. Please install it and the ViGEmBus driver.")
    sys.exit(1)

class App:
    """Main application class for the Anti-AFK tool."""
    TOOLTIP_BG_COLOR = "#FFFFE0"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.gamepad: Optional[vg.VX360Gamepad] = None
        self.toggle = False
        self.next_fire = 0.0
        self.is_listening = False
        self.tray_icon: Optional[pystray.Icon] = None
        
        self.icon_on_path = self._resource_path("assets/on.ico")
        self.icon_off_path = self._resource_path("assets/off.ico")

        self._setup_variables()
        self._load_config()
        self._setup_gui()
        self._update_ui_text()
        self._setup_vgamepad()
        self.update_hotkeys()

        threading.Thread(target=self._auto_loop, daemon=True).start()
        threading.Thread(target=self._setup_tray_icon, daemon=True).start()
        self.root.after(200, self._update_gui_loop)

    # --------------------------------------------------------------------------
    # Setup and Configuration Methods
    # --------------------------------------------------------------------------
    def _setup_variables(self):
        """Initialize default settings and hotkeys."""
        self.settings = {
            'interval': 6, 'speed_multiplier': 1.0, 'action_duration': 1.0,
            'circle_radius': 0.8, 'circle_loops': 1
        }
        self.hotkeys = {
            'toggle_auto': 'f1', 'manual_action': 'f2', 'show_time': 'f3',
            'set_window': 'f4', 'exit_app': 'ctrl+o'
        }
        self.registered_hotkeys = []
        self.keybind_buttons = []
        self.keybind_entries = {} # --- CHANGE: To store entry widgets for dynamic resizing
        
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None
        self.target_proc_name: Optional[str] = None

    def _get_config_path(self) -> str:
        """Get the path for the config file, compatible with PyInstaller."""
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'options.ini')

    def _load_config(self):
        """Load configuration from options.ini."""
        config = configparser.ConfigParser()
        config_path = self._get_config_path()
        if not os.path.exists(config_path):
            self._save_config()
        
        config.read(config_path)
        for key, default in self.settings.items():
            self.settings[key] = type(default)(config.get('Settings', key, fallback=default))
        for key, default in self.hotkeys.items():
            self.hotkeys[key] = config.get('Keybinds', key, fallback=default)

    def _save_config(self):
        """Save current configuration to options.ini."""
        config = configparser.ConfigParser()
        config['Settings'] = {k: str(v) for k, v in self.settings.items()}
        config['Keybinds'] = self.hotkeys
        try:
            with open(self._get_config_path(), 'w') as configfile:
                config.write(configfile)
        except Exception as e:
            self._update_status(f"Error saving config: {e}")

    def _setup_vgamepad(self):
        """Initializes the virtual gamepad."""
        try:
            self.gamepad = vg.VX360Gamepad()
            self._update_status("Virtual gamepad initialized.")
        except Exception as e:
            self._update_status(f"Gamepad Error: {e}")
            messagebox.showwarning("Gamepad Error", "Could not initialize virtual gamepad. Ensure ViGEmBus driver is installed.")

    # --------------------------------------------------------------------------
    # Core Action Logic (No changes in this section)
    # --------------------------------------------------------------------------
    def _prepare_target_window(self) -> Optional[int]:
        hwnd = self.target_hwnd
        if not hwnd:
            self._update_status("Target window not set")
            return None
        if not win32gui.IsWindow(hwnd):
            self.target_hwnd = None; self._update_ui_text(); self._update_status("Target window no longer exists.")
            return None
        try:
            if win32gui.IsIconic(hwnd): win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd); time.sleep(0.3 * self.settings['speed_multiplier'])
            if win32gui.GetForegroundWindow() != hwnd:
                self._update_status("Failed to bring target window to foreground"); return None
        except win32gui.error as e:
            self._update_status(f"Window activation error: {e}"); return None
        return hwnd

    def perform_game_actions(self):
        initial_mouse = win32gui.GetCursorPos(); prev_hwnd = win32gui.GetForegroundWindow()
        hwnd = self._prepare_target_window()
        if not hwnd: return
        try:
            self._perform_camera_turn(); time.sleep(0.1 * self.settings['speed_multiplier'])
            if self.gamepad:
                self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A); self.gamepad.update()
                time.sleep(0.1)
                self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A); self.gamepad.update()
            self._update_status(f"Actions sent to: {self.target_title}")
        except Exception as e: self._update_status(f"Error during actions: {e}")
        finally:
            if prev_hwnd and win32gui.IsWindow(prev_hwnd) and win32gui.GetForegroundWindow() != prev_hwnd:
                try: win32gui.SetForegroundWindow(prev_hwnd)
                except win32gui.error: pass
            try: win32api.SetCursorPos(initial_mouse)
            except win32api.error: pass

    def _perform_camera_turn(self):
        if not self.gamepad: return
        steps, radius, duration = 60, self.settings['circle_radius'], self.settings['action_duration']
        for _ in range(self.settings['circle_loops']):
            for i in range(steps + 1):
                angle = (i / steps) * 2 * math.pi
                x, y = math.cos(angle) * radius, math.sin(angle) * radius
                self.gamepad.right_joystick_float(x_value_float=x, y_value_float=y); self.gamepad.update()
                time.sleep(duration / steps)
        self.gamepad.right_joystick_float(0.0, 0.0); self.gamepad.update()
        
    def _auto_loop(self):
        while True:
            if self.toggle and time.time() >= self.next_fire:
                self.perform_game_actions()
                self.next_fire = time.time() + self.settings['interval']
            time.sleep(0.1)

    # --------------------------------------------------------------------------
    # Hotkey and UI Action Methods
    # --------------------------------------------------------------------------
    def _toggle_auto(self):
        self.toggle = not self.toggle
        if self.toggle:
            self.next_fire = time.time() + self.settings['interval']
            self._update_status("Auto Action: ON")
            if self.tray_icon: self.tray_icon.icon = self.icon_on
            self.root.iconbitmap(self.icon_on_path)
        else:
            self._update_status("Auto Action: OFF")
            if self.tray_icon: self.tray_icon.icon = self.icon_off
            self.root.iconbitmap(self.icon_off_path)
        self._update_ui_text()

    def manual_action(self):
        threading.Thread(target=self.perform_game_actions, daemon=True).start()

    def _show_time_left(self):
        message = f"Next action in: {max(0, int(self.next_fire - time.time()))}s" if self.toggle else "Auto action is OFF"
        self._update_status(message); self._show_tooltip(message)

    def _set_target_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd: self._update_status("Could not get foreground window."); return
            self.target_hwnd = hwnd; self.target_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            self.target_proc_name = os.path.basename(win32process.GetModuleFileNameEx(handle, 0)); win32api.CloseHandle(handle)
            self._update_ui_text(); self._update_status(f"Target window set to: {self.target_title}")
        except Exception as e:
            self.target_hwnd, self.target_title, self.target_proc_name = None, None, None
            self._update_ui_text(); self._update_status(f"Error setting window: {e}")

    def test_target_detection(self):
        if self.target_hwnd and win32gui.IsWindow(self.target_hwnd):
            self._update_status(f"Success! Target is '{self.target_title}'")
        else:
            self.target_hwnd = None; self._update_status("Failure: Target window not set or has been closed.")
            self._update_ui_text()

    def update_hotkeys(self):
        for hotkey in self.registered_hotkeys:
            try: keyboard.remove_hotkey(hotkey)
            except Exception: pass
        self.registered_hotkeys.clear()
        actions = {'toggle_auto': self._toggle_auto, 'manual_action': self.manual_action, 'show_time': self._show_time_left, 
                   'set_window': self._set_target_window, 'exit_app': self._quit_app}
        for name, func in actions.items():
            hotkey = self.hotkeys[name]
            try:
                keyboard.add_hotkey(hotkey, func); self.registered_hotkeys.append(hotkey)
            except Exception as e: self._update_status(f"Failed to set hotkey '{hotkey}': {e}")
        self._update_ui_text()

    def _start_listening(self, hotkey_name: str, str_var: tk.StringVar):
        if self.is_listening: return
        self.is_listening = True
        for hotkey in self.registered_hotkeys: keyboard.remove_hotkey(hotkey)
        self._update_status("Press a key combination..."); str_var.set("Listening...")
        for btn in self.keybind_buttons: btn.config(state="disabled")
        threading.Thread(target=self._hotkey_listener_thread, args=(hotkey_name, str_var), daemon=True).start()

    def _hotkey_listener_thread(self, hotkey_name: str, str_var: tk.StringVar):
        hotkey = keyboard.read_hotkey(suppress=False)
        self.root.after(0, self._on_hotkey_recorded, hotkey, hotkey_name, str_var)

    def _on_hotkey_recorded(self, hotkey: str, hotkey_name: str, str_var: tk.StringVar):
        self.hotkeys[hotkey_name] = hotkey; formatted_hotkey = self._format_hotkey(hotkey)
        str_var.set(formatted_hotkey)
        # --- FIX: Dynamically set width of the entry that was just changed ---
        entry_widget = self.keybind_entries.get(hotkey_name)
        if entry_widget:
            entry_widget.config(width=len(formatted_hotkey) + 2)
        # -------------------------------------------------------------------
        self._update_status(f"New hotkey set to '{formatted_hotkey}'.")
        self._save_config(); self.update_hotkeys()
        for btn in self.keybind_buttons: btn.config(state="normal")
        self.is_listening = False

    # --------------------------------------------------------------------------
    # GUI Creation and Update Methods
    # --------------------------------------------------------------------------
    def _setup_gui(self):
        self.root.title("silver's Anti-AFK"); self.root.iconbitmap(self.icon_off_path)
        self.root.geometry("420x520"); self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        
        # --- FIX: Define a monospaced font for the keybind entries ---
        self.mono_font = tkfont.Font(family="Consolas", size=10)
        # -----------------------------------------------------------

        self.countdown_var = tk.StringVar(value="Auto action is OFF"); self.status_var = tk.StringVar(value="Status: Idle")
        self.manual_btn_text = tk.StringVar(); self.auto_btn_text = tk.StringVar(); self.test_btn_text = tk.StringVar()
        self.target_window_var = tk.StringVar()

        notebook = ttk.Notebook(self.root); notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self._create_controls_tab(notebook); self._create_keybinds_tab(notebook)

        status_bar = ttk.Frame(self.root, padding=(5, 2)); status_bar.pack(side="bottom", fill="x")

        # --- FIX: Apply custom style to the status bar label for readability ---
        ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").pack(side="left")
        # -------------------------------------------------------------------

    def _create_controls_tab(self, parent_notebook: ttk.Notebook):
        tab = ttk.Frame(parent_notebook, padding="10"); parent_notebook.add(tab, text='Controls')
        target_frame = ttk.LabelFrame(tab, text="Target Window", padding="10"); target_frame.pack(pady=5, fill="x")
        ttk.Label(target_frame, textvariable=self.target_window_var, wraplength=350, justify=tk.CENTER).pack()
        ttk.Label(tab, textvariable=self.countdown_var, font=("Segoe UI", 12)).pack(pady=10)
        settings_frame = ttk.Frame(tab); settings_frame.pack(pady=5)
        self._create_settings_entries(settings_frame)
        ttk.Button(tab, textvariable=self.test_btn_text, command=self.test_target_detection).pack(pady=5, fill='x', side='bottom')
        ttk.Button(tab, textvariable=self.auto_btn_text, command=self._toggle_auto).pack(pady=5, fill='x', side='bottom')
        ttk.Button(tab, textvariable=self.manual_btn_text, command=self.manual_action).pack(pady=5, fill='x', side='bottom')

    def _create_settings_entries(self, parent_frame: ttk.Frame):
        self.entries = {}
        setting_defs = {"Cooldown (s):": ('interval', self._validate_int), "Speed Multiplier:": ('speed_multiplier', self._validate_float),
                        "Loop Duration (s):": ('action_duration', self._validate_float), "Circle Radius:": ('circle_radius', self._validate_float),
                        "Circle Loops:": ('circle_loops', self._validate_int)}
        for i, (label, (key, vcmd)) in enumerate(setting_defs.items()):
            ttk.Label(parent_frame, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            entry = ttk.Entry(parent_frame, width=8, validate='key', validatecommand=(self.root.register(vcmd), '%P'))
            entry.insert(0, str(self.settings[key])); entry.grid(row=i, column=1)
            ttk.Button(parent_frame, text="Set", command=lambda k=key, e=entry: self._set_setting(k, e)).grid(row=i, column=2, padx=5)
            self.entries[key] = entry

    def _create_keybinds_tab(self, parent_notebook: ttk.Notebook):
        tab = ttk.Frame(parent_notebook, padding="10"); parent_notebook.add(tab, text='Keybinds')
        keybind_frame = ttk.LabelFrame(tab, text="Click 'Change' then press your new hotkey", padding="10"); keybind_frame.pack(fill="x")
        keybind_defs = {"Toggle Auto Action:": "toggle_auto", "Manual Action:": "manual_action", "Show Time Left:": "show_time", 
                        "Set Target Window:": "set_window", "Exit Application:": "exit_app"}
        self.keybind_buttons.clear(); self.keybind_entries.clear()
        for i, (label, key) in enumerate(keybind_defs.items()):
            ttk.Label(keybind_frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            hotkey_str = self._format_hotkey(self.hotkeys.get(key, ''))
            str_var = tk.StringVar(value=hotkey_str)
            # --- FIX: Apply monospaced font and dynamic width ---
            entry = ttk.Entry(keybind_frame, textvariable=str_var, state='readonly', font=self.mono_font, width=len(hotkey_str) + 2)
            entry.grid(row=i, column=1, padx=5)
            self.keybind_entries[key] = entry # Store the widget
            # ----------------------------------------------------
            button = ttk.Button(keybind_frame, text="Change", command=lambda k=key, s=str_var: self._start_listening(k, s))
            button.grid(row=i, column=2)
            self.keybind_buttons.append(button)

    def _update_ui_text(self):
        self.manual_btn_text.set(f"Manual Action ({self._format_hotkey(self.hotkeys['manual_action'])})")
        self.test_btn_text.set("Test Target Detection")
        if self.toggle: self.auto_btn_text.set(f"Stop Auto Action ({self._format_hotkey(self.hotkeys['toggle_auto'])})")
        else: self.auto_btn_text.set(f"Start Auto Action ({self._format_hotkey(self.hotkeys['toggle_auto'])})")
        if self.target_hwnd and self.target_title: self.target_window_var.set(f"{self.target_title} - {self.target_proc_name}")
        else: self.target_window_var.set(f"No window set. Press '{self._format_hotkey(self.hotkeys['set_window'])}' on a window.")

    def _set_setting(self, key: str, entry_widget: ttk.Entry):
        try:
            value = entry_widget.get(); caster = type(self.settings[key]); new_val = caster(value)
            if new_val <= 0 or (key == 'circle_radius' and not (0.0 < new_val <= 1.0)): raise ValueError
            self.settings[key] = new_val; self._update_status(f"{key.replace('_', ' ').capitalize()} set to {new_val}"); self._save_config()
        except (ValueError, TypeError): messagebox.showerror("Error", f"Please enter a valid positive number for {key}.")

    def _update_gui_loop(self):
        if self.toggle: self.countdown_var.set(f"Next action in: {max(0, int(self.next_fire - time.time()))}s")
        else: self.countdown_var.set("Auto action is OFF")
        self.root.after(200, self._update_gui_loop)

    def _show_tooltip(self, text: str):
        tooltip = tk.Toplevel(self.root); tooltip.wm_overrideredirect(True); tooltip.wm_attributes("-topmost", True)
        label = ttk.Label(tooltip, text=text, padding=(5, 3), background=self.TOOLTIP_BG_COLOR, relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack(); x, y = win32gui.GetCursorPos(); tooltip.geometry(f"+{x+20}+{y+10}") 
        tooltip.after(2000, tooltip.destroy)

    # --------------------------------------------------------------------------
    # System Tray and Application Lifecycle (No changes in this section)
    # --------------------------------------------------------------------------
    def _setup_tray_icon(self):
        try:
            self.icon_off = Image.open(self._resource_path("assets/off.ico"))
            self.icon_on = Image.open(self._resource_path("assets/on.ico"))
        except FileNotFoundError: messagebox.showerror("Error", "Icon files not found in 'assets' subfolder."); self._quit_app(); return
        title = "silver's Anti-AFK"
        menu = (pystray.MenuItem('Show', self.root.deiconify, default=True), pystray.MenuItem('Quit', self._quit_app))
        self.tray_icon = pystray.Icon(title, self.icon_off, title, menu)
        if self.tray_icon: self.tray_icon.run()

    def _quit_app(self):
        if self.tray_icon: self.tray_icon.stop()
        self.root.quit(); self.root.destroy()
    
    # --------------------------------------------------------------------------
    # Static Utility Methods (No changes in this section)
    # --------------------------------------------------------------------------
    @staticmethod
    def _resource_path(relative_path: str) -> str:
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        return os.path.join(base_path, relative_path)
    
    @staticmethod
    def _format_hotkey(hotkey_str: str) -> str:
        return '+'.join([part.strip().capitalize() for part in str(hotkey_str).split('+')])

    def _update_status(self, message: str):
        if self.root and self.root.winfo_exists():
            self.root.after(0, lambda: self.status_var.set(f"Status: {message}"))
    
    @staticmethod
    def _validate_int(v: str) -> bool: return v.isdigit() or v == ""
    
    @staticmethod
    def _validate_float(v: str) -> bool:
        if v == "" or v == ".": return True
        try: float(v); return True
        except ValueError: return False

if __name__ == "__main__":
    root = tk.Tk()
    sv_ttk.set_theme("dark")

    # --- FIX: Define custom styles for fonts and colors ---
    style = ttk.Style()
    # Use a slightly nicer global font
    style.configure(".", font=("Segoe UI", 10)) 
    # Create a custom style for the status bar with a light blue/cyan color
    style.configure("Status.TLabel", foreground="#00BFFF", font=("Segoe UI", 9))
    # ----------------------------------------------------

    app = App(root)
    root.mainloop()