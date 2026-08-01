import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import numpy as np
import pygame.image
import ctypes # Keep ctypes for Windows API calls
from PIL import ImageGrab # Keep ImageGrab for screenshots
import os
import sys
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

# Fragment Shader: Handles magnifying glass logic & smooth edge filtering
FRAGMENT_SHADER = """
#version 330
uniform sampler2D texture1;
uniform vec2 mouse_pos;
uniform vec2 resolution;
uniform float zoom_level;
uniform float lens_radius;
uniform int is_square;   // 0 = Circle, 1 = Square
uniform int filter_mode; // 0 = Unsharp, 1 = Bicubic, 2 = Scale2x, 3 = xBRZ, 4 = AMD CAS

in vec2 v_texcoord;
out vec4 f_color;

// 1. Bicubic Catmull-Rom 16-tap Interpolation for ultra-smooth text curves
vec4 cubic(float v) {
    vec4 n = vec4(1.0, 2.0, 3.0, 4.0) - v;
    vec4 s = n * n * n;
    float x = s.x;
    float y = s.y - 4.0 * s.x;
    float z = s.z - 4.0 * s.y + 6.0 * s.x;
    float w = 6.0 - x - y - z;
    return vec4(x, y, z, w) * (1.0 / 6.0);
}

vec4 sample_bicubic(sampler2D tex, vec2 uv, vec2 tex_size) {
    vec2 sample_pos = uv * tex_size - 0.5;
    vec2 f = fract(sample_pos);
    vec2 tc = (floor(sample_pos) + 0.5) / tex_size;

    vec4 x_weights = cubic(f.x);
    vec4 y_weights = cubic(f.y);

    vec4 c = vec4(0.0);
    for (int y = -1; y <= 2; y++) {
        for (int x = -1; x <= 2; x++) {
            vec2 offset = vec2(float(x), float(y)) / tex_size;
            vec4 sample_col = texture(tex, tc + offset);
            float weight = x_weights[x + 1] * y_weights[y + 1];
            c += sample_col * weight;
        }
    }
    return c;
}

// 2. Scale2x / EPX Pixel Edge Smoothing Algorithm
vec4 sample_scale2x(sampler2D tex, vec2 uv, vec2 tex_size) {
    vec2 delta = 1.0 / tex_size;
    vec4 P = texture(tex, uv);
    vec4 A = texture(tex, uv + vec2(0.0, -delta.y));
    vec4 B = texture(tex, uv + vec2(delta.x, 0.0));
    vec4 C = texture(tex, uv + vec2(-delta.x, 0.0));
    vec4 D = texture(tex, uv + vec2(0.0, delta.y));

    if (distance(C, A) < 0.15 && distance(C, D) > 0.15 && distance(A, B) > 0.15) {
        P = mix(P, (C + A) * 0.5, 0.5);
    } else if (distance(A, B) < 0.15 && distance(A, C) > 0.15 && distance(B, D) > 0.15) {
        P = mix(P, (A + B) * 0.5, 0.5);
    } else if (distance(B, D) < 0.15 && distance(B, A) > 0.15 && distance(D, C) > 0.15) {
        P = mix(P, (B + D) * 0.5, 0.5);
    } else if (distance(D, C) < 0.15 && distance(D, B) > 0.15 && distance(C, A) > 0.15) {
        P = mix(P, (D + C) * 0.5, 0.5);
    }
    return P;
}

// 3. xBRZ / Vector Pattern Edge Detection & Corner Smoothing
vec4 sample_xbrz(sampler2D tex, vec2 uv, vec2 tex_size) {
    vec2 dx = vec2(1.0 / tex_size.x, 0.0);
    vec2 dy = vec2(0.0, 1.0 / tex_size.y);

    vec4 src = texture(tex, uv);
    vec4 src_u = texture(tex, uv - dy);
    vec4 src_d = texture(tex, uv + dy);
    vec4 src_l = texture(tex, uv - dx);
    vec4 src_r = texture(tex, uv + dx);

    float d_u_r = distance(src_u, src_r);
    float d_d_l = distance(src_d, src_l);

    if (d_u_r < d_d_l) {
        src = mix(src, (src_u + src_r) * 0.5, 0.4);
    } else if (d_d_l < d_u_r) {
        src = mix(src, (src_d + src_l) * 0.5, 0.4);
    }
    return src;
}

// 4. AMD FidelityFX Contrast Adaptive Sharpening (CAS)
// Analyzes local contrast and sharpens edges adaptively without over-brightening
vec4 sample_cas(sampler2D tex, vec2 uv, vec2 tex_size) {
    vec2 d = 1.0 / tex_size;

    // Sample 3x3 neighbourhood
    vec4 a = texture(tex, uv + vec2(-d.x, -d.y)); // TL
    vec4 b = texture(tex, uv + vec2( 0.0, -d.y)); // T
    vec4 c = texture(tex, uv + vec2( d.x, -d.y)); // TR
    vec4 d1= texture(tex, uv + vec2(-d.x,  0.0)); // L
    vec4 e = texture(tex, uv);                     // Centre
    vec4 f = texture(tex, uv + vec2( d.x,  0.0)); // R
    vec4 g = texture(tex, uv + vec2(-d.x,  d.y)); // BL
    vec4 h = texture(tex, uv + vec2( 0.0,  d.y)); // B
    vec4 i = texture(tex, uv + vec2( d.x,  d.y)); // BR

    // Compute local min/max using cross neighbours only (b, d, f, h)
    vec4 mn = min(min(min(b, d1), min(f, h)), e);
    vec4 mx = max(max(max(b, d1), max(f, h)), e);

    // Adaptive sharpening weight: stronger in low-contrast areas, gentle in bright edges
    vec4 rng = mx - mn;
    // Avoid division by zero; amp is the CAS sharpening kernel weight
    vec4 amp = clamp(min(mn, 2.0 - mx) / rng, 0.0, 1.0);
    amp = sqrt(amp);
    float peak = -1.0 / mix(8.0, 5.0, amp.r); // tune sharpness: -1/8 soft .. -1/5 sharp

    // 5-tap sharpening kernel: sharp centre, negative cross neighbours
    vec4 result = (b + d1 + f + h) * peak + e * (1.0 - 4.0 * peak);
    return clamp(result, 0.0, 1.0);
}

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
        vec2 diff = uv - mouse_pos;
        vec2 zoomed_uv = mouse_pos + (diff / zoom_level);

        if (filter_mode == 1) {
            // Bicubic Smooth Filter
            f_color = sample_bicubic(texture1, zoomed_uv, resolution);
        } else if (filter_mode == 2) {
            // Scale2x / EPX Pixel Smooth Filter
            f_color = sample_scale2x(texture1, zoomed_uv, resolution);
        } else if (filter_mode == 3) {
            // xBRZ Vector Smooth Filter
            f_color = sample_xbrz(texture1, zoomed_uv, resolution);
        } else if (filter_mode == 4) {
            // AMD FidelityFX CAS - Contrast Adaptive Sharpening
            f_color = sample_cas(texture1, zoomed_uv, resolution);
        } else {
            // Standard Unsharp Mask Filter (filter_mode == 0)
            vec2 texel_size = 1.0 / resolution;
            float s = 0.25;

            vec4 center_color = texture(texture1, zoomed_uv) * (1.0 + 4.0 * s);
            vec4 top_color    = texture(texture1, zoomed_uv + vec2(0.0, texel_size.y / zoom_level)) * -s;
            vec4 bottom_color = texture(texture1, zoomed_uv - vec2(0.0, texel_size.y / zoom_level)) * -s;
            vec4 left_color   = texture(texture1, zoomed_uv - vec2(texel_size.x / zoom_level, 0.0)) * -s;
            vec4 right_color  = texture(texture1, zoomed_uv + vec2(texel_size.x / zoom_level, 0.0)) * -s;

            f_color = center_color + top_color + bottom_color + left_color + right_color;
        }

        // Add a black border around the lens
        float border_thickness = 0.003;
        if (is_square == 0) {
            if (distance(uv * aspect_correction, mouse_pos * aspect_correction) > lens_radius - border_thickness) {
                f_color = vec4(0.2, 0.2, 0.2, 1.0);
            }
        } else {
            vec2 diff = abs(uv - mouse_pos);
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
        self.filter_mode = "unsharp" # Default filter mode
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
                self.filter_mode = data.get('filter_mode', self.filter_mode)
                self.has_window_state = data.get('has_window_state', False)
        except (FileNotFoundError, json.JSONDecodeError):
            pass # Use defaults if file is missing or corrupt

    def load_filter_mode(self, path):
        """Reloads only filter_mode from settings without touching zoom/radius/etc."""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.filter_mode = data.get('filter_mode', self.filter_mode)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

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
                'filter_mode': self.filter_mode,
                'has_window_state': True
            }
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass # Don't crash if saving fails

app_state = AppState()

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

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
        icon_path = get_resource_path('myicon.ico')
        icon_surface = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_surface)
    except Exception:
        print("Warning: myicon.ico not found. Using default pygame icon.")

    # Show the system cursor by default for Desktop mode.
    pygame.mouse.set_visible(True)

    # Load system cursor handles once
    from ctypes import wintypes
    user32 = ctypes.windll.user32

    # Declare Win32 API signatures for 64-bit Windows handle precision
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long

    user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    user32.SetWindowLongW.restype = ctypes.c_long

    HWND_TOPMOST = wintypes.HWND(-1)

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
    loc_mouse  = glGetUniformLocation(shader, "mouse_pos")
    loc_res    = glGetUniformLocation(shader, "resolution")
    loc_zoom   = glGetUniformLocation(shader, "zoom_level")
    loc_radius = glGetUniformLocation(shader, "lens_radius")
    loc_shape  = glGetUniformLocation(shader, "is_square")
    loc_filter = glGetUniformLocation(shader, "filter_mode")

    # Map filter_mode name -> int for shader
    FILTER_MODE_MAP = {"unsharp": 0, "bicubic": 1, "scale2x": 2, "xbrz": 3, "cas": 4}

    # Set static uniforms
    glUniform2f(loc_res, WIDTH, HEIGHT)
    glUniform1i(glGetUniformLocation(shader, "texture1"), 0)

    # Hide the magnifier window from screenshots so we don't capture the overlay itself
    # 0x00000011 is WDA_EXCLUDEFROMCAPTURE (Windows 10/11)
    user32.SetWindowDisplayAffinity(hwnd, 0x00000011)

    # --- ENABLE DESKTOP MODE (CLICK-THROUGH) BY DEFAULT ---
    # Windows Extended Style Flags:
    # WS_EX_TOPMOST     = 0x00000008
    # WS_EX_TRANSPARENT = 0x00000020
    # WS_EX_APPWINDOW   = 0x00040000 (Forces taskbar icon to be visible)
    # WS_EX_LAYERED     = 0x00080000
    WS_EX_TOPMOST     = 0x00000008
    WS_EX_TRANSPARENT = 0x00000020
    WS_EX_APPWINDOW   = 0x00040000
    WS_EX_LAYERED     = 0x00080000

    BASE_EX_STYLE = WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_APPWINDOW

    # Apply base styles + WS_EX_TRANSPARENT (click-through) initially
    user32.SetWindowLongW(hwnd, -20, BASE_EX_STYLE | WS_EX_TRANSPARENT)

    # HWND_TOPMOST (-1), SWP_NOMOVE (0x0002) | SWP_NOSIZE (0x0001) | SWP_NOACTIVATE (0x0010) | SWP_FRAMECHANGED (0x0020) = 0x0033
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0033)

    # 6. Main Loop
    running = True
    shape_key_was_down = False  # For toggling shape
    was_alt_down = False       # For toggling click-through
    frame_count = 0            # Used for periodic settings reload

    # For incremental scaling speed
    up_key_press_time = None
    down_key_press_time = None

    while running:
        # Re-assert HWND_TOPMOST continuously so clicking other windows never pushes magnifier behind
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0013)

        # Live reload filter_mode from settings every 60 frames so magpy_settings.exe changes apply instantly
        frame_count += 1
        if frame_count % 60 == 0:
            app_state.load_filter_mode(SETTINGS_FILE)

        # --- TOGGLE INTERACTION MODE WITH ALT KEY ---
        # Default: Desktop Mode (Click-Through)
        # Hold Alt: Magnifier Mode (Captures Mouse, Scroll Zooms)

        # Process Alt key state
        is_alt_down = user32.GetAsyncKeyState(0x12) & 0x8000  # VK_MENU (Alt key)
        if is_alt_down and not was_alt_down:
            # Hold Alt -> Enable Magnifier Mode (Capture Mouse for Zoom)
            user32.SetWindowLongW(hwnd, -20, BASE_EX_STYLE) # Remove WS_EX_TRANSPARENT
            user32.SetCursor(h_cross_cursor) # Set system cursor to crosshair
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0033)
        elif not is_alt_down and was_alt_down:
            # Release Alt -> Re-enable Desktop Mode (Click-Through)
            user32.SetWindowLongW(hwnd, -20, BASE_EX_STYLE | WS_EX_TRANSPARENT)
            user32.SetCursor(h_arrow_cursor) # Set system cursor to arrow
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, 0x0033)
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
        glUniform1i(loc_filter, FILTER_MODE_MAP.get(app_state.filter_mode, 0))

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
