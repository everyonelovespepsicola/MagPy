# 🔍 MagPy

MagPy is a lightweight, highly customizable screen magnification utility built with Python, Pygame, and OpenGL. It provides a seamless magnifying glass effect over your desktop, allowing you to zoom in on any detail while continuing to interact with the applications underneath.

## ✨ Features

- **Real-Time Magnification:** Instantly magnify any area of your screen following your mouse cursor.
- **Click-Through Desktop Mode:** By default, MagPy is transparent to mouse clicks, letting you work uninterrupted.
- **Interactive Magnifier Mode:** Hold `Alt` to capture mouse input for zooming and to access keyboard controls.
- **Customizable Lens:** Adjust the zoom level, change the lens size, and toggle between circular and square shapes.
- **Visual Enhancements:** Features a built-in unsharp mask filter to enhance details and configurable Multi-Sample Anti-Aliasing (MSAA) for smooth edges.
- **Persistent Settings:** Automatically remembers your last used zoom, radius, shape, and window position.

## 🚀 Installation

### Option 1: Pre-built Binaries (Recommended)
You can download the ready-to-use executables without needing to install Python:
1. Go to the **Releases** page and download `MagPy.zip`.
2. Extract the ZIP file to your preferred location.
3. Run `magnifier.exe` to start the app, or `magpy_settings.exe` to configure your keyboard shortcuts.

### Option 2: From Source (For Developers/Advanced Users)
Ensure you have Python 3 installed, then follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/MagPy.git
   cd MagPy
   ```
2. **Set up a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows Command Prompt:
   .\.venv\Scripts\activate.bat
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. **Install dependencies:**
   ```bash
   pip install pygame PyOpenGL PyOpenGL_accelerate numpy Pillow
   ```
4. **Run MagPy:**
   ```bash
   python magnifier.py
   ```

## 🎮 Usage & Controls

MagPy operates in two primary modes:
- **Desktop Mode (Default):** The magnifier follows your cursor but ignores clicks, allowing you to use your computer normally.
- **Magnifier Mode:** Activated by holding down the `Alt` key. This mode captures your mouse and keyboard for adjusting the magnifier settings.

| Action | Key / Input | Mode Required |
| :--- | :--- | :--- |
| **Activate Controls** | Hold `Alt` | Desktop Mode |
| **Close MagPy** | `ESC` or `Middle-Click` | Any Mode |
| **Zoom In/Out** | `Mouse Wheel` or `Page Up / Down` | Magnifier Mode (Hold `Alt`) |
| **Adjust Lens Size** | `Up / Down Arrows` (Hold to accelerate) | Magnifier Mode (Hold `Alt`) |
| **Toggle Lens Shape** | `Left / Right Arrows` | Magnifier Mode (Hold `Alt`) |

## ⚙️ Configuration

MagPy automatically saves your preferences to a JSON file. You can manually edit this file to tweak advanced settings like MSAA sample count (e.g., 8 or 16 for smoother visuals).
- **Windows Path:** `%APPDATA%\MagPy\settings.json`

## 🛠️ Building the Executable (For Developers)

To create a standalone `.exe` for Windows using PyInstaller:

1. **Install PyInstaller:** 
   ```bash
   pip install pyinstaller
   ```
2. **Activate your virtual environment:** (e.g., `.\.venv\Scripts\Activate.ps1`).
3. **Clean previous builds:**
   ```powershell
   Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue
   pyinstaller --clean magnifier.py
   pyinstaller --clean magpy_settings.py
   ```
4. **Build the executables:** *(Ensure you update the `$PYTHON_DLL_PATH` to match your local system)*
   ```powershell
   $PYTHON_DLL_PATH = "C:\PATH\TO\YOUR\ACTUAL\python313.dll"
   pyinstaller --noconsole --add-binary "$PYTHON_DLL_PATH;." magnifier.py
   pyinstaller --noconsole --add-binary "$PYTHON_DLL_PATH;." magpy_settings.py
   ```
*The executables (`magnifier.exe` and `magpy_settings.exe`) will be output into their respective folders in the `dist/` directory.*

## 📄 License

This project is licensed under the MIT License.