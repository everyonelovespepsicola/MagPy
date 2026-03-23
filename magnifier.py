import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pygame.image
import ctypes # Keep ctypes for Windows API calls
from PIL import ImageGrab # Keep ImageGrab for screenshots
import os
import json

# Structure for querying mouse position globally
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# Structure for querying window rectangle
class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), 
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

# Global mapping for Virtual Key Codes (Windows specific)
VK_CODE_MAP = {
    "VK_ESCAPE": 0x1B,
    "VK_PAGE_UP": 0x21,
    "VK_PAGE_DOWN": 0x22,
    "VK_UP": 0x26,
    "VK_DOWN": 0x28,
    "VK_LEFT": 0x25,
    "VK_RIGHT": 0x27,
    "VK_ALT": 0x12, # Alt key for Magnifier Mode
    # Add other common keys if needed for future shortcuts
    "VK_F1": 0x70, "VK_F2": 0x71, "VK_F3": 0x72, "VK_F4": 0x73, "VK_F5": 0x74,
    "VK_F6": 0x75, "VK_F7": 0x76, "VK_F8": 0x77, "VK_F9": 0x78, "VK_F10": 0x79,
    "VK_F11": 0x7A, "VK_F12": 0x7B,
    "VK_SPACE": 0x20, "VK_RETURN": 0x0D, "VK_BACK": 0x08, "VK_TAB": 0x09,
    "VK_SHIFT": 0x10, "VK_CONTROL": 0x11,
}
REVERSE_VK_CODE_MAP = {v: k for k, v in VK_CODE_MAP.items()}

# Vertex Shader: Handles the position of our full-screen rectangle
VERTEX_SHADER = """
#version 330
in vec2 position;
in vec2 texcoord;
out vec2 v_texcoord;
void main() {
    gl_Position = vec4(position, 0.0, 1.0);
    v_texcoord = texcoord;
}
"""

# Fragment Shader: Handles the magnifying glass logic
FRAGMENT_SHADER = """
#version 330
uniform sampler2D texture1;
uniform vec2 mouse_pos;
uniform vec2 resolution;
uniform float zoom_level;
uniform float lens_radius;
uniform int is_square; // 0 = Circle, 1 = Square

in vec2 v_texcoord;
out vec4 f_color;

void main() {
    // Use interpolated texture coordinates from vertex shader to handle orientation
    vec2 uv = v_texcoord;
    
    // Adjust aspect ratio so the lens is a perfect circle, not an oval
    float aspect = resolution.x / resolution.y;
    vec2 aspect_correction = vec2(aspect, 1.0);
    
    // Calculate distance from mouse to current pixel (corrected for aspect ratio)
    bool in_lens = false;
    
    if (is_square == 1) {
        vec2 diff = abs(uv - mouse_pos);
        // Check bounds. X bound needs aspect correction (lens_radius is vertical size)
        if (diff.x < lens_radius / aspect && diff.y < lens_radius) {
            in_lens = true;
        }
    } else {
        float dist = distance(uv * aspect_correction, mouse_pos * aspect_correction);
        if (dist < lens_radius) {
            in_lens = true;
        }
    }

    if (in_lens) {
        // --- INSIDE THE LENS ---
        
        // Calculate the vector from mouse to this pixel
        vec2 diff = uv - mouse_pos; 
        
        // Scale that vector down by the zoom factor to sample closer to the center
        vec2 zoomed_uv = mouse_pos + (diff / zoom_level);
        
        // --- SHARPENING / "SUPER RESOLUTION" ---
        // Get the size of one pixel in the texture's coordinate system
        vec2 texel_size = 1.0 / resolution;
        
        // Dynamic sharpening strength that increases with zoom level
        float s = 0.25; // Reduced sharpening strength for a more subtle effect

        vec4 center_color = texture(texture1, zoomed_uv) * (1.0 + 4.0 * s);
        vec4 top_color    = texture(texture1, zoomed_uv + vec2(0.0, texel_size.y / zoom_level)) * -s;
        vec4 bottom_color = texture(texture1, zoomed_uv - vec2(0.0, texel_size.y / zoom_level)) * -s;
        vec4 left_color   = texture(texture1, zoomed_uv - vec2(texel_size.x / zoom_level, 0.0)) * -s;
        vec4 right_color  = texture(texture1, zoomed_uv + vec2(texel_size.x / zoom_level, 0.0)) * -s;
        
        f_color = center_color + top_color + bottom_color + left_color + right_color;
        
        // Add a black border around the lens
        float border_thickness = 0.003;
        if (is_square == 0) {
            // Circular border
            if (distance(uv * aspect_correction, mouse_pos * aspect_correction) > lens_radius - border_thickness) {
                f_color = vec4(0.2, 0.2, 0.2, 1.0); 
            }
        } else {
            // Square border
            vec2 diff = abs(uv - mouse_pos);
            // Check if it's within the outer 'border_thickness' band of the square
            if (diff.x >= (lens_radius / aspect) - border_thickness || diff.y >= lens_radius - border_thickness) {
                f_color = vec4(0.2, 0.2, 0.2, 1.0); 
            }
        }
    } else {
        // --- OUTSIDE THE LENS ---
        f_color = texture(texture1, uv);
    }
}
"""

# Global App State to share between Main Loop and Window Hook
class AppState:
    def __init__(self):
        self.zoom = 2.0
        self.radius = 0.15
        self.square = 0 # 0 = Round, 1 = Square
        self.win_x = 0
        self.win_y = 0
        self.win_w = 0
        self.win_h = 0
        self.msaa_samples = 4 # Default MSAA samples
        self.keybindings = {
            "exit_key": "VK_ESCAPE",
            "zoom_in_key": "VK_PAGE_UP",
            "zoom_out_key": "VK_PAGE_DOWN",
            "radius_up_key": "VK_UP",
            "radius_down_key": "VK_DOWN",
            "toggle_shape_key_1": "VK_LEFT",
            "toggle_shape_key_2": "VK_RIGHT",
        }
        self.has_window_state = False

    def load(self, path):
        """Loads state from a JSON file."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.zoom = data.get('zoom', self.zoom)
                self.radius = data.get('radius', self.radius)
                self.square = data.get('square', self.square)
                self.win_x = data.get('win_x', 0)
                self.win_y = data.get('win_y', 0)
                self.win_w = data.get('win_w', 0)
                self.win_h = data.get('win_h', 0)
                self.keybindings = data.get('keybindings', self.keybindings)
                self.msaa_samples = data.get('msaa_samples', self.msaa_samples)
                self.has_window_state = data.get('has_window_state', False)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # Use defaults if file is missing or corrupt

    def save(self, path):
        """Saves state to a JSON file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {
                'zoom': self.zoom,
                'radius': self.radius,
                'square': self.square,
                'win_x': self.win_x,
                'win_y': self.win_y,
                'win_w': self.win_w,
                'win_h': self.win_h,
                'keybindings': self.keybindings,
                'msaa_samples': self.msaa_samples,
                'has_window_state': True
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass # Don't crash if saving fails

app_state = AppState()

# Define cache path in the AppData folder
SETTINGS_FILE = os.path.join(os.getenv('APPDATA'), 'MagPy', 'settings.json')

# Windows System Cursor Constants
IDC_ARROW = 32512
IDC_CROSS = 32515

# Windows ShowWindow commands
SW_HIDE = 0
SW_SHOW = 5
SW_RESTORE = 9

def main():
    # 1. Initialize Pygame
    pygame.init()

    # Set the application icon
    try:
        icon_surface = pygame.image.load('magpy_icon.ico') # Ensure magpy_icon.ico is in your project directory
        pygame.display.set_icon(icon_surface)
    except FileNotFoundError:
        print("Warning: magpy_icon.ico not found. Using default pygame icon.")

    # Show the system cursor by default for Desktop mode.
    pygame.mouse.set_visible(True)
    
    # Load system cursor handles once
    user32 = ctypes.windll.user32
    h_arrow_cursor = user32.LoadCursorW(None, IDC_ARROW)
    h_cross_cursor = user32.LoadCursorW(None, IDC_CROSS)

    # Give the app a unique ID so the Taskbar treats it as a standalone program
    # This prevents it from grouping with other Python scripts and helps the custom menu work.
    myappid = 'mycompany.magpy.magnifier.1_0' # Updated for MagPy
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    # Load previous settings from cache
    app_state.load(SETTINGS_FILE)

    # Determine Window Geometry
    if app_state.has_window_state:
        WIDTH, HEIGHT = app_state.win_w, app_state.win_h
        x, y = app_state.win_x, app_state.win_y
    else:
        # Default to full primary screen
        screenshot = ImageGrab.grab()
        WIDTH, HEIGHT = screenshot.size
        x, y = 0, 0

    # Configure OpenGL for MSAA before creating the display surface
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, app_state.msaa_samples)

    # Set window position before creation
    os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

    # Use NOFRAME instead of FULLSCREEN to avoid monitor mode switching (flashes)
    pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL | NOFRAME)
    
    hwnd = pygame.display.get_wm_info()["window"]

    # Clear to black immediately to hide any initial white window background
    glClear(GL_COLOR_BUFFER_BIT)
    pygame.display.flip()

    pygame.display.set_caption("MagPy Magnifier")

    # 2. Compile Shaders
    shader = compileProgram(
        compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
        compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    )

    # 3. Create a Full-Screen Quad
    # Format: [x, y, u, v] 
    # Note: V-coordinates are flipped (1.0 -> 0.0) to handle the inverted texture 
    # orientation, so we don't have to CPU flip the screenshot every frame.
    vertices = np.array([
        -1.0, -1.0, 0.0, 1.0, # Bottom Left
         1.0, -1.0, 1.0, 1.0, # Bottom Right
         1.0,  1.0, 1.0, 0.0, # Top Right
        -1.0,  1.0, 0.0, 0.0  # Top Left
    ], dtype=np.float32)
    
    indices = np.array([0, 1, 2, 2, 3, 0], dtype=np.uint32)

    # Generate Buffers
    VBO = glGenBuffers(1)
    EBO = glGenBuffers(1)
    VAO = glGenVertexArrays(1)

    glBindVertexArray(VAO)

    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    # Position Attribute
    glEnableVertexAttribArray(0)
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(0))
    # Texture Coord Attribute
    glEnableVertexAttribArray(1)
    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 16, ctypes.c_void_p(8))

    # 4. Create and Load Texture
    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    
    # Texture Parameters
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR) # Linear for smooth zoom
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

    # 5. Get Uniform Locations
    glUseProgram(shader)
    loc_mouse = glGetUniformLocation(shader, "mouse_pos")
    loc_res = glGetUniformLocation(shader, "resolution")
    loc_zoom = glGetUniformLocation(shader, "zoom_level")
    loc_radius = glGetUniformLocation(shader, "lens_radius")
    loc_shape = glGetUniformLocation(shader, "is_square")
    
    # Set static uniforms
    glUniform2f(loc_res, WIDTH, HEIGHT)
    glUniform1i(glGetUniformLocation(shader, "texture1"), 0)

    # Hide the magnifier window from screenshots so we don't capture the overlay itself
    # 0x00000011 is WDA_EXCLUDEFROMCAPTURE (Windows 10/11)
    user32.SetWindowDisplayAffinity(hwnd, 0x00000011)

    # --- ENABLE DESKTOP MODE (CLICK-THROUGH) BY DEFAULT ---
    # We enable WS_EX_LAYERED (0x80000) AND WS_EX_TRANSPARENT (0x20) initially.
    # This means the window is click-through by default.
    # GWL_EXSTYLE = -20
    # We apply these styles even when hidden, so they are active when shown.
    current_styles = user32.GetWindowLongW(hwnd, -20)
    user32.SetWindowLongW(hwnd, -20, current_styles | 0x80000 | 0x20)

    # Keep Topmost: HWND_TOPMOST (-1), SWP_NOMOVE | SWP_NOSIZE (0x03)
    user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 3)

    # 6. Main Loop
    running = True
    shape_key_was_down = False  # For toggling shape
    was_alt_down = False       # For toggling click-through
    
    # For incremental scaling speed
    up_key_press_time = None
    down_key_press_time = None

    while running:
        # --- TOGGLE INTERACTION MODE WITH ALT KEY ---
        # Default: Desktop Mode (Click-Through)
        # Hold Alt: Magnifier Mode (Captures Mouse, Scroll Zooms)
        
        # Process Alt key state
        is_alt_down = user32.GetAsyncKeyState(0x12) & 0x8000  # VK_MENU (Alt key)
        if is_alt_down and not was_alt_down:
            # Hold Alt -> Enable Magnifier Mode (Capture Mouse for Zoom)
            styles = user32.GetWindowLongW(hwnd, -20)
            user32.SetWindowLongW(hwnd, -20, styles & ~0x20) # Remove WS_EX_TRANSPARENT
            user32.SetCursor(h_cross_cursor) # Set system cursor to crosshair
        elif not is_alt_down and was_alt_down:
            # Release Alt -> Re-enable Desktop Mode (Click-Through)
            styles = user32.GetWindowLongW(hwnd, -20)
            user32.SetWindowLongW(hwnd, -20, styles | 0x20) # Add WS_EX_TRANSPARENT
            user32.SetCursor(h_arrow_cursor) # Set system cursor to arrow
        was_alt_down = is_alt_down

        # Pygame event loop (Receives events when Alt is held)
        for event in pygame.event.get():
            if event.type == MOUSEWHEEL:
                app_state.zoom += event.y * 0.1
                if app_state.zoom < 1.0: app_state.zoom = 1.0
        
        # --- GLOBAL INPUT POLLING (Always active) ---            
        # Use the configurable exit key, but keep middle click hardcoded for convenience
        if app_state.keybindings["exit_key"] and user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["exit_key"]]) & 0x8000:
            running = False

        # Zoom using PageUp/PageDown (VK_PRIOR=0x21, VK_NEXT=0x22)
        if user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["zoom_in_key"]]) & 0x8000:
            app_state.zoom += 0.05
        if user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["zoom_out_key"]]) & 0x8000:
            app_state.zoom -= 0.05
        if app_state.zoom < 1.0: app_state.zoom = 1.0

        # Size using Up/Down arrows (VK_UP=0x26, VK_DOWN=0x28) with incremental speed
        current_time = pygame.time.get_ticks() # Milliseconds since pygame.init()
        
        BASE_RADIUS_SPEED = 0.004
        RADIUS_ACCELERATION = 0.00004
        MAX_RADIUS_SPEED = 0.04

        if user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["radius_up_key"]]) & 0x8000:
            if up_key_press_time is None:
                up_key_press_time = current_time
            duration = (current_time - up_key_press_time)
            radius_change_speed = min(BASE_RADIUS_SPEED + (duration * RADIUS_ACCELERATION), MAX_RADIUS_SPEED)
            app_state.radius += radius_change_speed
            down_key_press_time = None # Reset other key's timer
        else:
            up_key_press_time = None

        if user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["radius_down_key"]]) & 0x8000: # Down arrow is pressed
            if down_key_press_time is None:
                down_key_press_time = current_time
            duration = (current_time - down_key_press_time)
            radius_change_speed = min(BASE_RADIUS_SPEED + (duration * RADIUS_ACCELERATION), MAX_RADIUS_SPEED)
            app_state.radius -= radius_change_speed
            up_key_press_time = None # Reset other key's timer
        else:
            down_key_press_time = None

        # Ensure radius doesn't go below a minimum
        app_state.radius = max(0.05, app_state.radius)

        # Shape using Left/Right arrows (VK_LEFT=0x25, VK_RIGHT=0x27)
        shape_key_is_down = (user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["toggle_shape_key_1"]]) & 0x8000) or \
                            (user32.GetAsyncKeyState(VK_CODE_MAP[app_state.keybindings["toggle_shape_key_2"]]) & 0x8000)
        if shape_key_is_down and not shape_key_was_down:
            app_state.square = 1 - app_state.square # Toggle 0 and 1
        shape_key_was_down = shape_key_is_down

        # --- REAL-TIME CAPTURE ---
        try:
            # Grab the screen (The magnifier window is invisible to this grab)
            # Grab only the area under the window to ensure texture matches 1:1
            current_screen = ImageGrab.grab(bbox=(x, y, x+WIDTH, y+HEIGHT))
            img_data = current_screen.tobytes("raw", "RGB")
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, WIDTH, HEIGHT, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        except Exception:
            pass

        # Update Mouse Position
        # Use GetCursorPos for global coordinates since window ignores mouse
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        mx, my = pt.x, pt.y
        
        # Normalize mouse to 0.0 - 1.0
        # Relative to window position (mx - x)
        norm_mx = (mx - x) / WIDTH
        norm_my = (my - y) / HEIGHT
        
        # Render
        glClear(GL_COLOR_BUFFER_BIT)
        glUseProgram(shader)
        
        # Send dynamic uniforms
        glUniform2f(loc_mouse, norm_mx, norm_my)
        glUniform1f(loc_zoom, app_state.zoom)
        glUniform1f(loc_radius, app_state.radius)
        glUniform1i(loc_shape, app_state.square)

        glBindVertexArray(VAO)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        pygame.display.flip()
        pygame.time.wait(10)

    # Get final window position from OS to save (in case it moved)
    rect = RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    app_state.win_x = rect.left
    app_state.win_y = rect.top
    app_state.win_w = rect.right - rect.left
    app_state.win_h = rect.bottom - rect.top

    # Ensure the system cursor is restored to the arrow on exit
    user32.SetCursor(h_arrow_cursor)

    # Save settings to cache on exit
    app_state.has_window_state = True # Window is always visible now
    app_state.save(SETTINGS_FILE)

    pygame.quit()

if __name__ == "__main__":
    main()
