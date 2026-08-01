# 🔍 MagPy

MagPy is a lightweight, highly customizable screen magnification utility built with Python, Pygame, and OpenGL. It provides a seamless magnifying glass effect over your desktop, allowing you to zoom in on any detail while continuing to interact with the applications underneath.

## ✨ Features

- **Real-Time Magnification:** Instantly magnify any area of your screen following your mouse cursor.
- **Click-Through Desktop Mode:** By default, MagPy is transparent to mouse clicks, letting you work uninterrupted.
- **Interactive Magnifier Mode:** Hold `Alt` to capture mouse input for zooming and to access keyboard controls.
- **Customizable Lens:** Adjust the zoom level, change the lens size, and toggle between circular and square shapes.
- **Smooth Edge Filters:** Choose from 5 GPU-accelerated GLSL filters for better magnified image quality (see [Smooth Edge Filters](#-smooth-edge-filters)).
- **Always-on-Top Overlay:** MagPy stays above all other windows at all times — clicking on other applications will never push the magnifier behind them.
- **Visual Enhancements:** Configurable Multi-Sample Anti-Aliasing (MSAA) for smooth lens border edges.
- **Persistent Settings:** Automatically remembers your last used zoom, radius, shape, filter mode, and window position.
- **Live Settings Reload:** Change filters in `magpy_settings.exe` and MagPy applies them within ~0.6 seconds — no restart required.

## 🚀 Installation

### Option 1: Pre-built Binaries (Recommended)
You can download the ready-to-use executables without needing to install Python:
1. Go to the **Releases** page and download `MagPy.zip`.
2. Extract the ZIP file to your preferred location.
3. Run `MagPy.exe` to start the app, or `magpy_settings.exe` to configure your keyboard shortcuts and filter mode.

### Option 2: From Source (For Developers/Advanced Users)
Ensure you have Python 3.12 installed, then follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/MagPy.git
   cd MagPy
   ```
2. **Set up a virtual environment:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. **Install frozen dependencies:**
   ```bash
   pip install -r requirements.txt
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
| **Close MagPy** | `ESC` | Any Mode |
| **Zoom In/Out** | `Mouse Wheel` or `Page Up / Down` | Magnifier Mode (Hold `Alt`) |
| **Adjust Lens Size** | `Up / Down Arrows` (Hold to accelerate) | Magnifier Mode (Hold `Alt`) |
| **Toggle Lens Shape** | `Left / Right Arrows` | Magnifier Mode (Hold `Alt`) |

> All keyboard shortcuts are fully configurable via `magpy_settings.exe`.

## 🎨 Smooth Edge Filters

MagPy includes 5 GPU-accelerated GLSL filters that run inside the OpenGL fragment shader. Select your preferred filter in `magpy_settings.exe` under **Smooth Filter Mode**. Changes apply live without restarting.

| Filter | Description | Best For |
| :--- | :--- | :--- |
| **Standard (Unsharp)** | 5-tap Unsharp Mask — boosts center pixel, subtracts neighbors | Crisp text, general use |
| **Bicubic Smooth** | 16-tap Catmull-Rom cubic interpolation | Photos, icons, smooth gradients |
| **Scale2x / EPX** | Emulator-style pixel edge smoothing algorithm | Rounded pixel edges |
| **xBRZ / Vector Smooth** | Pattern-based diagonal edge detection and blending | Diagonal edge smoothing |
| **AMD CAS (Adaptive Sharpen)** | FidelityFX Contrast Adaptive Sharpening — sharpens low-contrast zones, gentle on bright edges | Best all-rounder: crisp text without halos |

> **Tip:** AMD CAS is recommended for everyday use — it produces the sharpest text at all zoom levels without the over-sharpening artifacts of the Unsharp filter.

## ⚙️ Configuration

MagPy automatically saves your preferences to a JSON file. You can also use `magpy_settings.exe` for a GUI configuration experience.

- **Windows Path:** `%APPDATA%\MagPy\settings.json`

### Available Settings (settings.json)

| Key | Default | Description |
| :--- | :--- | :--- |
| `zoom` | `2.0` | Current zoom level |
| `radius` | `0.15` | Lens radius (0.05 – 1.0) |
| `square` | `0` | Lens shape: `0` = Circle, `1` = Square |
| `msaa_samples` | `4` | MSAA sample count (`4`, `8`, or `16`) |
| `filter_mode` | `"unsharp"` | Active filter: `unsharp`, `bicubic`, `scale2x`, `xbrz`, `cas` |
| `win_x`, `win_y` | `0, 0` | Window position |
| `win_w`, `win_h` | screen size | Window dimensions |
| `keybindings` | see defaults | Configurable key bindings |

## 🛠️ Building the Executable (For Developers)

The easiest way to build both executables is to run the included `publish.ps1` script. It handles everything automatically:

```powershell
.\publish.ps1
```

`publish.ps1` will:
1. Detect your Python 3.12 installation.
2. Create or validate the `.venv` virtual environment (auto-recreates if dependencies are stale).
3. Install all dependencies from `requirements.txt` using frozen, pinned versions.
4. Freeze the current dependency state back to `requirements.txt`.
5. Build `MagPy.exe` and `magpy_settings.exe` using PyInstaller into the `dist/` folder.

### Manual Build (Advanced)

If you prefer to build manually:

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Clean previous builds
Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Build executables
python -m PyInstaller --onefile --noconsole --name "MagPy" --icon "myicon.ico" --add-data "myicon.ico;." magnifier.py
python -m PyInstaller --onefile --noconsole --name "magpy_settings" --icon "myicon.ico" --add-data "myicon.ico;." magpy_settings.py
```

*Executables are output to the `dist/` folder.*

## 📦 Dependencies

All runtime dependencies are pinned in `requirements.txt` for reproducible builds:

| Package | Version | Purpose |
| :--- | :--- | :--- |
| `pygame` | 2.6.1 | Window creation, event loop, display |
| `PyOpenGL` | 3.1.10 | OpenGL rendering & GLSL shader support |
| `PyOpenGL-accelerate` | 3.1.10 | C-accelerated OpenGL bindings |
| `numpy` | 2.4.4 | Vertex buffer & geometry data |
| `Pillow` | 12.2.0 | Screen capture (`ImageGrab`) |
| `pyinstaller` | 6.20.0 | Packaging into standalone `.exe` |

## 📄 License

This project is licensed under the MIT License.