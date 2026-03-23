# MagPy - A Python-based Magnifying Glass Utility

MagPy is a lightweight, customizable magnifying glass utility built with Python, Pygame, and OpenGL. It allows you to magnify any part of your screen with adjustable zoom, lens size, and shape, and features a unique "Desktop Mode" for seamless interaction.

## Features

- **Real-time Magnification:** Magnify any area of your screen instantly.
- **Adjustable Zoom:** Control the magnification level with the mouse wheel or Page Up/Down keys.
- **Variable Lens Size:** Change the size of the magnifying lens with Up/Down arrow keys, featuring incremental speed for quick adjustments.
- **Toggleable Lens Shape:** Switch between circular and square lens shapes using the Left/Right arrow keys.
- **Sharpening Filter:** Built-in unsharp mask filter to enhance details in the magnified area.
- **Multi-Sample Anti-Aliasing (MSAA):** Configurable MSAA for smoother edges.
- **Desktop Mode (Click-Through):** By default, the magnifier is click-through, allowing you to interact with applications beneath it.
- **Magnifier Mode:** Hold the `Alt` key to activate "Magnifier Mode," which captures mouse input for zooming and allows keyboard controls.
- **Context Menu Integration:** Launch MagPy quickly by right-clicking on your desktop or in a folder (requires installer).
- **Persistent Settings:** Saves your last used zoom, radius, shape, and window position.

## Installation

There are two primary ways to install and run MagPy:

### Option 1: Using the Installer (Recommended for Users)

If you have an installer (e.g., `MagPy_Setup_1.0.exe`) generated using Inno Setup, follow these steps:

1.  **Download the Installer:** Obtain the latest `MagPy_Setup_X.X.exe` from the project's distribution.
2.  **Run the Installer:** Double-click the installer executable.
3.  **Follow On-Screen Instructions:** The setup wizard will guide you through the installation process.
4.  **Start Menu Entry:** The installer will create a shortcut in your Start Menu under "MagPy".
5.  **Context Menu Integration:** The installer will also add a "Launch MagPy" option to your right-click context menu when you right-click on the desktop or in a folder background.

### Option 2: From Source (For Developers/Advanced Users)

To run MagPy directly from its Python source code, you'll need Python and the required libraries.

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-repo/MagPy.git
    cd MagPy
    ```
    (Replace `https://github.com/your-repo/MagPy.git` with the actual repository URL)

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Virtual Environment:**
    -   **Windows (Command Prompt):** `.\.venv\Scripts\activate.bat`
    -   **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
    -   **macOS/Linux:** `source ./.venv/bin/activate`

4.  **Install Dependencies:**
    ```bash
    pip install pygame PyOpenGL PyOpenGL_accelerate numpy Pillow
    ```

5.  **Run the Application:**
    ```bash
    python magnifier.py
    ```

## Usage

MagPy starts in a click-through **Desktop Mode** by default.

### Desktop Mode (Default)

- The magnifier window is transparent to mouse clicks, allowing you to interact with applications underneath.
- The magnifier follows your mouse cursor.
- **Exit:** Press `ESC` or `Middle-Click` to close MagPy.

### Keyboard Shortcuts (Active in Magnifier Mode - Hold `Alt` Key)

When you hold down the `Alt` key, MagPy enters "Magnifier Mode," which activates the following keyboard controls:

- The magnifier window becomes active and captures mouse input.
- The mouse cursor changes to a crosshair.

#### Arrow Keys

- **Up Arrow (`↑`)**: Increases the lens size (radius).
- **Down Arrow (`↓`)**: Decreases the lens size (radius).
    *(Note: Holding the arrow keys will incrementally increase the speed of size adjustment.)*
- **Left Arrow (`←`)**: Toggles the lens shape between circular and square.
- **Right Arrow (`→`)**: Toggles the lens shape between circular and square.

#### Page Up/Down Keys

- **Page Up**: Increases the zoom level.
- **Page Down**: Decreases the zoom level.

#### Mouse Controls (Active in Magnifier Mode - Hold `Alt` Key)

When you hold down the `Alt` key, MagPy enters "Magnifier Mode":

- **Mouse Wheel Up**: Zooms in.
- **Mouse Wheel Down**: Zooms out.

- **Exit:** Release the `Alt` key to return to Desktop Mode, or press `ESC` or `Middle-Click` to close MagPy.

### Configuration (`settings.json`)

MagPy saves its settings (last position, zoom, radius, shape, MSAA samples) to a `settings.json` file located in your user's AppData folder:

`%APPDATA%\MagPy\settings.json` (on Windows)

You can manually edit this file to change default values, for example, to set a higher `msaa_samples` value (e.g., 8 or 16) if your graphics card supports it for smoother visuals.

## Building an Executable (for Developers)

To create a standalone executable (`.exe`) for Windows, you can use PyInstaller:

1.  **Ensure PyInstaller is installed:** If you haven't already, install PyInstaller in your virtual environment:
    ```bash
    pip install pyinstaller
    ```
2.  **Activate your virtual environment:**
    ```bash
    . .venv\Scripts\Activate.ps1 # For PowerShell
    ```
3.  **Clean previous builds:**
    ```bash
    Remove-Item -Path "build", "dist" -Recurse -Force -ErrorAction SilentlyContinue
    pyinstaller --clean magnifier.py
    pyinstaller --clean magpy_settings.py
    ```
4.  **Build the executables:** (Replace `C:\PATH\TO\YOUR\ACTUAL\python313.dll` with the correct path on your system)
    ```bash
    $PYTHON_DLL_PATH = "C:\PATH\TO\YOUR\ACTUAL\python313.dll"
    pyinstaller --noconsole --add-binary "$PYTHON_DLL_PATH;." magnifier.py
    pyinstaller --noconsole --add-binary "$PYTHON_DLL_PATH;." magpy_settings.py
    ```
5.  The executables (`magnifier.exe` and `magpy_settings.exe`) will be found in their respective subfolders within the `dist` directory (e.g., `dist\magnifier\magnifier.exe`).

## Building an Installer (for Developers)

If you wish to create a full installer with Start Menu and Context Menu integration, you can use Inno Setup. This is a separate, manual step after building the executables. You will need the `installer_script.iss` file (provided in the project) and the PyInstaller output from the `dist` folder.

1.  **Install Inno Setup:** Download and install Inno Setup from jrsoftware.org.
2.  **Compile the Script:** Open `installer_script.iss` in Inno Setup Compiler and click "Compile".
3.  The installer executable will be generated in the specified output directory (e.g., `Output` folder).

---

Enjoy using MagPy!