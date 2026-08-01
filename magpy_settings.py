import tkinter as tk
from tkinter import messagebox
from tkinter import ttk # Import ttk for themed widgets
import json
import os
import sys
import ctypes

# Global mapping for Virtual Key Codes (Windows specific)
VK_CODE_MAP = {
    "VK_ESCAPE": 0x1B,
    "VK_PAGE_UP": 0x21,
    "VK_PAGE_DOWN": 0x22,
    "VK_UP": 0x26,
    "VK_DOWN": 0x28,
    "VK_LEFT": 0x25,
    "VK_RIGHT": 0x27,
    "VK_ALT": 0x12,
    "VK_F1": 0x70, "VK_F2": 0x71, "VK_F3": 0x72, "VK_F4": 0x73, "VK_F5": 0x74,
    "VK_F6": 0x75, "VK_F7": 0x76, "VK_F8": 0x77, "VK_F9": 0x78, "VK_F10": 0x79,
    "VK_F11": 0x7A, "VK_F12": 0x7B,
    "VK_SPACE": 0x20, "VK_RETURN": 0x0D, "VK_BACK": 0x08, "VK_TAB": 0x09,
    "VK_SHIFT": 0x10, "VK_CONTROL": 0x11,
    # Add more as needed
}
REVERSE_VK_CODE_MAP = {v: k for k, v in VK_CODE_MAP.items()}

# Define cache path in the AppData folder
SETTINGS_FILE = os.path.join(os.getenv('APPDATA'), 'MagPy', 'settings.json')

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SettingsApp:
    def __init__(self, master):
        self.master = master
        master.title("MagPy Settings")
        master.geometry("420x480") # Increased height for filter selection
        master.resizable(False, False)

        # Set the application icon
        try:
            master.iconbitmap(get_resource_path('myicon.ico'))
        except Exception:
            pass

        self.settings = self._load_settings()
        self.keybinding_vars = {}
        self.current_key_to_set = None

        self._create_widgets()

        # Force Dark Theme for testing
        self.master.configure(bg='#2e2e2e') # Dark background for the main window
        style = ttk.Style(self.master)
        style.theme_use('clam') # 'clam' is a good base for custom styling

        # Configure dark theme styles
        style.configure('TLabel', background='#2e2e2e', foreground='#ffffff', font=("Arial", 10))
        style.configure('TFrame', background='#2e2e2e')
        style.configure('TEntry', fieldbackground='#4a4a4a', foreground='#ffffff', borderwidth=1, relief="solid")
        style.map('TEntry', fieldbackground=[('readonly', '#4a4a4a')]) # Ensure readonly entry is also dark
        style.configure('TCombobox', fieldbackground='#4a4a4a', background='#5c5c5c', foreground='#ffffff', font=("Arial", 10))
        style.configure('TButton', background='#5c5c5c', foreground='#ffffff', font=("Arial", 10, "bold"))
        style.map('TButton',
            background=[('active', '#7a7a7a')], # Darker on hover
            foreground=[('active', '#ffffff')]
        )
        style.configure('Header.TLabel', background='#2e2e2e', foreground='#ffffff', font=("Arial", 14, "bold"))

        # Bind global key listener for setting shortcuts
        master.bind("<KeyPress>", self._on_key_press)

    def _load_settings(self):
        """Loads settings from JSON file, with defaults for keybindings."""
        default_settings = {
            'zoom': 2.0,
            'radius': 0.15,
            'square': 0,
            'win_x': 0, 'win_y': 0, 'win_w': 0, 'win_h': 0,
            'msaa_samples': 4,
            'filter_mode': 'unsharp',
            'has_window_state': False,
            'keybindings': {
                "exit_key": "", # Set to nothing by default
                "zoom_in_key": "VK_PAGE_UP",
                "zoom_out_key": "VK_PAGE_DOWN",
                "radius_up_key": "VK_UP",
                "radius_down_key": "VK_DOWN",
                "toggle_shape_key_1": "VK_LEFT",
                "toggle_shape_key_2": "VK_RIGHT",
            }
        }
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'r') as f:
                loaded_settings = json.load(f)
                default_settings.update(loaded_settings)
                default_settings['keybindings'].update(loaded_settings.get('keybindings', {}))
                return default_settings
        except (FileNotFoundError, json.JSONDecodeError):
            return default_settings

    def _save_settings(self):
        """Saves current settings to JSON file."""
        try:
            # Map display name back to filter_mode code
            selected_label = self.filter_combobox.get()
            label_to_code = {
                "Standard (Unsharp)": "unsharp",
                "Bicubic Smooth": "bicubic",
                "Scale2x / EPX": "scale2x",
                "xBRZ / Vector Smooth": "xbrz",
                "AMD CAS (Adaptive Sharpen)": "cas"
            }
            self.settings['filter_mode'] = label_to_code.get(selected_label, "unsharp")

            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            messagebox.showinfo("MagPy Settings", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("MagPy Settings", f"Error saving settings: {e}")

    def _create_widgets(self):
        """Creates the GUI elements for keybinding configuration."""
        ttk.Label(self.master, text="Keyboard Shortcuts", style='Header.TLabel').pack(pady=10)

        keybinding_frame = ttk.Frame(self.master)
        keybinding_frame.pack(pady=5)

        row = 0
        for action, default_key_name in self.settings['keybindings'].items():
            ttk.Label(keybinding_frame, text=action.replace('_', ' ').title() + ":").grid(row=row, column=0, padx=5, pady=2, sticky="w")

            var = tk.StringVar(value=default_key_name)
            self.keybinding_vars[action] = var

            entry = ttk.Entry(keybinding_frame, textvariable=var, state="readonly", width=20)
            entry.grid(row=row, column=1, padx=5, pady=2)

            button = ttk.Button(keybinding_frame, text="Change", command=lambda a=action: self._start_key_listen(a))
            button.grid(row=row, column=2, padx=5, pady=2)
            row += 1

        # Smooth Edge Filter Dropdown Section
        filter_frame = ttk.Frame(self.master)
        filter_frame.pack(pady=15)

        ttk.Label(filter_frame, text="Smooth Filter Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="w")

        code_to_label = {
            "unsharp": "Standard (Unsharp)",
            "bicubic": "Bicubic Smooth",
            "scale2x": "Scale2x / EPX",
            "xbrz": "xBRZ / Vector Smooth",
            "cas": "AMD CAS (Adaptive Sharpen)"
        }
        current_filter_label = code_to_label.get(self.settings.get('filter_mode', 'unsharp'), "Standard (Unsharp)")

        self.filter_combobox = ttk.Combobox(
            filter_frame,
            values=["Standard (Unsharp)", "Bicubic Smooth", "Scale2x / EPX", "xBRZ / Vector Smooth", "AMD CAS (Adaptive Sharpen)"],
            state="readonly",
            width=26
        )
        self.filter_combobox.set(current_filter_label)
        self.filter_combobox.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(self.master, text="Save Settings", command=self._save_settings).pack(pady=10)

    def _start_key_listen(self, action):
        """Puts the app in a state to listen for the next key press."""
        self.current_key_to_set = action
        self.master.title(f"MagPy Settings - Press key for {action.replace('_', ' ').title()}...")
        messagebox.showinfo("Set Shortcut", f"Press the key you want to assign to '{action.replace('_', ' ').title()}'")

    def _on_key_press(self, event):
        """Handles a key press event to set a shortcut."""
        if self.current_key_to_set:
            vk_code = ctypes.windll.user32.VkKeyScanA(ord(event.char)) if event.char else event.keycode

            # Handle special keys that don't have a char or simple keycode mapping
            if vk_code == -1: # VkKeyScanA returns -1 if no direct mapping
                if event.keysym == "Escape": vk_code = VK_CODE_MAP["VK_ESCAPE"]
                elif event.keysym == "Prior": vk_code = VK_CODE_MAP["VK_PAGE_UP"] # Page Up
                elif event.keysym == "Next": vk_code = VK_CODE_MAP["VK_PAGE_DOWN"] # Page Down
                elif event.keysym == "Up": vk_code = VK_CODE_MAP["VK_UP"]
                elif event.keysym == "Down": vk_code = VK_CODE_MAP["VK_DOWN"]
                elif event.keysym == "Left": vk_code = VK_CODE_MAP["VK_LEFT"]
                elif event.keysym == "Right": vk_code = VK_CODE_MAP["VK_RIGHT"]
                elif event.keysym == "Alt_L" or event.keysym == "Alt_R": vk_code = VK_CODE_MAP["VK_ALT"]
                elif event.keysym == "Shift_L" or event.keysym == "Shift_R": vk_code = VK_CODE_MAP["VK_SHIFT"]
                elif event.keysym == "Control_L" or event.keysym == "Control_R": vk_code = VK_CODE_MAP["VK_CONTROL"]
                elif event.keysym == "space": vk_code = VK_CODE_MAP["VK_SPACE"]
                elif event.keysym == "Return": vk_code = VK_CODE_MAP["VK_RETURN"]
                elif event.keysym == "BackSpace": vk_code = VK_CODE_MAP["VK_BACK"]
                elif event.keysym == "Tab": vk_code = VK_CODE_MAP["VK_TAB"]
                # Add more keysym to VK_CODE_MAP mappings as needed

            if vk_code in REVERSE_VK_CODE_MAP:
                key_name = REVERSE_VK_CODE_MAP[vk_code]
                self.settings['keybindings'][self.current_key_to_set] = key_name
                self.keybinding_vars[self.current_key_to_set].set(key_name)
                self.current_key_to_set = None
                self.master.title("MagPy Settings")
            else:
                messagebox.showwarning("Invalid Key", f"Key '{event.keysym}' (VK Code: {vk_code}) is not supported or recognized.")
                self.current_key_to_set = None # Stop listening
                self.master.title("MagPy Settings")


if __name__ == "__main__":
    root = tk.Tk()
    app = SettingsApp(root)
    root.mainloop()
