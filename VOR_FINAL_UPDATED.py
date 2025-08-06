import tkinter as tk
from tkinter import messagebox
from math import atan2, degrees, sqrt, sin, cos, radians
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError
import os
import sys
import subprocess
import webbrowser
import tempfile
import urllib.parse
import urllib.request
import math
from controller_bindings import ControllerHandler


# Try to import pygame for joystick support
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not available. Joystick support disabled. Install pygame with: pip install pygame")

# Try to import folium for real-world mapping
try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Folium not available. Real-world mapping disabled. Install folium with: pip install folium")

# Try to import tkinterweb for embedded web view
try:
    import tkinterweb
    TKINTERWEB_AVAILABLE = True
except ImportError:
    TKINTERWEB_AVAILABLE = False
    print("tkinterweb not available. Embedded maps disabled. Install with: pip install tkinterweb")

# Try to import matplotlib for 2D simulation background
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("matplotlib not available. 2D simulation background disabled. Install with: pip install matplotlib")

# Real VOR stations database (Philippines focus with some international)
REAL_VOR_STATIONS = {
    # Philippines VOR Stations
    "MIA": {"name": "Manila VOR", "lat": 14.5086, "lon": 121.0198, "freq": "116.3", "country": "Philippines"},
    "CEB": {"name": "Cebu VOR", "lat": 10.3157, "lon": 123.8854, "freq": "114.5", "country": "Philippines"},
    "ILO": {"name": "Iloilo VOR", "lat": 10.7126, "lon": 122.5445, "freq": "112.9", "country": "Philippines"},
    "DVO": {"name": "Davao VOR", "lat": 7.1081, "lon": 125.6048, "freq": "113.3", "country": "Philippines"},
    "BAG": {"name": "Baguio VOR", "lat": 16.3759, "lon": 120.6200, "freq": "115.1", "country": "Philippines"},
    "TAC": {"name": "Tacloban VOR", "lat": 11.2279, "lon": 125.0278, "freq": "114.1", "country": "Philippines"},
    "ZAM": {"name": "Zamboanga VOR", "lat": 6.9066, "lon": 122.0586, "freq": "112.5", "country": "Philippines"},
    
    # International VOR Stations (nearby)
    "SGN": {"name": "Ho Chi Minh VOR", "lat": 10.8231, "lon": 106.6297, "freq": "117.7", "country": "Vietnam"},
    "BKK": {"name": "Bangkok VOR", "lat": 13.6900, "lon": 100.7501, "freq": "116.6", "country": "Thailand"},
    "SIN": {"name": "Singapore VOR", "lat": 1.3521, "lon": 103.8198, "freq": "115.8", "country": "Singapore"},
    "KUL": {"name": "Kuala Lumpur VOR", "lat": 3.1390, "lon": 101.6869, "freq": "114.9", "country": "Malaysia"},
    "CGK": {"name": "Jakarta VOR", "lat": -6.1256, "lon": 106.6558, "freq": "113.7", "country": "Indonesia"},
    
    # US VOR Stations (for reference)
    "LAX": {"name": "Los Angeles VOR", "lat": 33.9425, "lon": -118.4081, "freq": "113.6", "country": "USA"},
    "JFK": {"name": "Kennedy VOR", "lat": 40.6413, "lon": -73.7781, "freq": "115.9", "country": "USA"},
    "ORD": {"name": "Chicago VOR", "lat": 41.9742, "lon": -87.9073, "freq": "113.9", "country": "USA"},
}

def create_matplotlib_background(width=800, height=600, style='radar'):
    """Create a 2D simulation background using matplotlib."""
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    # Create figure with black background
    fig, ax = plt.subplots(figsize=(width/100, height/100), facecolor='black')
    ax.set_facecolor('black')
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis('off')
    
    if style == 'radar':
        # Create radar-style background
        # Draw concentric circles
        for radius in [0.2, 0.4, 0.6, 0.8, 1.0]:
            circle = patches.Circle((0, 0), radius, fill=False, 
                                  edgecolor='lime', linewidth=1, alpha=0.6)
            ax.add_patch(circle)
        
        # Draw range rings with labels
        for radius, label in [(0.2, '10nm'), (0.4, '20nm'), (0.6, '30nm'), (0.8, '40nm')]:
            ax.text(radius, 0.05, label, color='lime', fontsize=8, ha='center')
        
        # Draw radial lines (compass directions)
        angles = np.linspace(0, 2*np.pi, 36, endpoint=False)  # Every 10 degrees
        for angle in angles:
            x = [0, np.cos(angle)]
            y = [0, np.sin(angle)]
            ax.plot(x, y, 'lime', linewidth=0.5, alpha=0.3)
        
        # Draw cardinal directions
        directions = {'N': (0, 0.95), 'E': (0.95, 0), 'S': (0, -0.95), 'W': (-0.95, 0)}
        for direction, (x, y) in directions.items():
            ax.text(x, y, direction, color='lime', fontsize=14, ha='center', va='center', weight='bold')
        
        # Add heading markers every 30 degrees
        for heading in range(0, 360, 30):
            angle_rad = np.radians(90 - heading)  # Convert to math coordinates
            x = 0.85 * np.cos(angle_rad)
            y = 0.85 * np.sin(angle_rad)
            ax.text(x, y, str(heading).zfill(3), color='lime', fontsize=10, ha='center', va='center')
    
    elif style == 'navigation':
        # Create navigation chart style background
        # Grid lines
        for i in np.arange(-1, 1.1, 0.1):
            ax.axhline(y=i, color='darkblue', linewidth=0.5, alpha=0.3)
            ax.axvline(x=i, color='darkblue', linewidth=0.5, alpha=0.3)
        
        # Major grid lines
        for i in np.arange(-1, 1.1, 0.5):
            ax.axhline(y=i, color='blue', linewidth=1, alpha=0.6)
            ax.axvline(x=i, color='blue', linewidth=1, alpha=0.6)
        
        # Center crosshairs
        ax.axhline(y=0, color='white', linewidth=2)
        ax.axvline(x=0, color='white', linewidth=2)
        
        # Distance scale
        scale_text = "Scale: 1 unit = 50nm"
        ax.text(-0.9, -0.9, scale_text, color='white', fontsize=10)
    
    elif style == 'simple':
        # Simple crosshair background
        ax.axhline(y=0, color='white', linewidth=2, alpha=0.8)
        ax.axvline(x=0, color='white', linewidth=2, alpha=0.8)
        
        # Add some grid lines
        for i in np.arange(-0.8, 0.9, 0.4):
            ax.axhline(y=i, color='gray', linewidth=1, alpha=0.3)
            ax.axvline(x=i, color='gray', linewidth=1, alpha=0.3)
    
    # Convert to PIL Image
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.buffer_rgba()
    size = canvas.get_width_height()
    
    plt.close(fig)  # Clean up
    
    # Convert to PIL Image
    pil_image = Image.frombuffer("RGBA", size, raw_data).convert("RGB")
    return pil_image

def create_vor_simulation_background(width=800, height=600, vor_freq=None):
    """Create a VOR-specific simulation background with radials."""
    if not MATPLOTLIB_AVAILABLE:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(width/100, height/100), facecolor='black')
    ax.set_facecolor('black')
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.axis('off')
    
    # Draw VOR station at center
    station = patches.Circle((0, 0), 0.05, fill=True, facecolor='red', edgecolor='white', linewidth=2)
    ax.add_patch(station)
    
    # Draw radials every 10 degrees
    for radial in range(0, 360, 10):
        angle_rad = np.radians(90 - radial)
        
        # Different line styles for different radials
        if radial % 30 == 0:
            # Major radials
            linewidth = 2
            alpha = 0.8
            color = 'lime'
        elif radial % 10 == 0:
            # Minor radials
            linewidth = 1
            alpha = 0.6
            color = 'lime'
        
        # Draw radial line
        x = [0.1 * np.cos(angle_rad), 0.9 * np.cos(angle_rad)]
        y = [0.1 * np.sin(angle_rad), 0.9 * np.sin(angle_rad)]
        ax.plot(x, y, color=color, linewidth=linewidth, alpha=alpha)
        
        # Label major radials
        if radial % 30 == 0:
            label_x = 0.95 * np.cos(angle_rad)
            label_y = 0.95 * np.sin(angle_rad)
            ax.text(label_x, label_y, f"{radial:03d}°", color='lime', 
                   fontsize=10, ha='center', va='center', weight='bold')
    
    # Draw range rings
    for radius, distance in [(0.3, '15nm'), (0.6, '30nm'), (0.9, '45nm')]:
        circle = patches.Circle((0, 0), radius, fill=False, 
                              edgecolor='cyan', linewidth=1, alpha=0.5, linestyle='--')
        ax.add_patch(circle)
        ax.text(radius * 0.707, radius * 0.707, distance, color='cyan', fontsize=8)
    
    # Add VOR frequency if provided
    if vor_freq:
        ax.text(0, -0.15, f"VOR {vor_freq} MHz", color='white', 
               fontsize=12, ha='center', va='center', weight='bold')
    
    # Convert to PIL Image
    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    raw_data = renderer.buffer_rgba()
    size = canvas.get_width_height()
    
    plt.close(fig)
    
    pil_image = Image.frombuffer("RGBA", size, raw_data).convert("RGB")
    return pil_image

# --- VOR Logic ---
def calculate_bearing(x_aircraft, y_aircraft, x_vor, y_vor):
    """Calculates the bearing from the aircraft to the VOR station in degrees."""
    dx = x_vor - x_aircraft
    dy = y_vor - y_aircraft
    angle = degrees(atan2(dx, dy))
    return (angle + 360) % 360

def calculate_vor_to_from(obs, bearing):
    """
    Determines if the CDI should show a TO or FROM indication.
    Now works symmetrically for both the main radial and its reciprocal.
    """
    diff = (bearing - obs + 360) % 360
    
    # Check both the main radial and reciprocal radial
    reciprocal_diff = (diff + 180) % 360
    
    # Determine which radial we're closer to
    if min(diff, 360 - diff) <= min(reciprocal_diff, 360 - reciprocal_diff):
        # Closer to main radial
        # A difference of less than 90 or greater than 270 means "TO" the VOR
        return "TO" if diff < 90 or diff > 270 else "FROM"
    else:
        # Closer to reciprocal radial
        # For reciprocal radial, the TO/FROM logic is inverted
        return "FROM" if reciprocal_diff < 90 or reciprocal_diff > 270 else "TO"

def calculate_distance(x1, y1, x2, y2):
    """Calculates the straight-line distance between two points."""
    return round(sqrt((x2 - x1)**2 + (y2 - y1)**2), 2)

def calculate_cdi_deflection(obs, bearing_to_vor):
    """
    Calculates CDI needle deflection in dots, from -10 (full left) to +10 (full right).
    Each dot represents 2 degrees of deviation.
    This function now works symmetrically for both the main radial and its reciprocal.
    """
    # Calculate the difference between OBS setting and bearing TO the VOR
    diff = (bearing_to_vor - obs + 360) % 360
    
    # Normalize to -180 to +180
    if diff > 180:
        diff -= 360
    
    # Check if we're closer to the main radial or the reciprocal radial
    # The CDI should center when aircraft is on either the selected radial OR its reciprocal
    reciprocal_diff = diff + 180 if diff < 0 else diff - 180
    
    # Use whichever difference is smaller (closer to either radial line)
    if abs(reciprocal_diff) < abs(diff):
        # Aircraft is closer to the reciprocal radial
        # Invert the deflection for reciprocal side to maintain consistent left/right indication
        diff = reciprocal_diff
    
    # Convert to dots (each dot represents about 2 degrees)
    dots = diff / 2.0
    
    # Limit to ±10 dots (full scale deflection)
    return max(-10, min(10, dots))

# --- GUI ---
class VORSimulatorGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced VOR Simulator")
        self.root.focus_set()

        root.state('zoomed')
        
        self.vor_output_visible = True
        self.vor_output_panel_items = []
        self.vor_show_tab = None
        
        # Instruction box visibility
        self.instruction_visible = True
        self.instruction_panel_items = []
        self.instruction_show_tab = None
        # Load background image
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "vor_bg.png")
            if os.path.exists(image_path):
                self.bg_img = Image.open(image_path).resize((2000, 900))
                self.tk_img = ImageTk.PhotoImage(self.bg_img)
            else:
                self.tk_img = None
        except (FileNotFoundError, UnidentifiedImageError):
            print("Warning: 'map_bg.png' not found. Using blank background.")
            self.tk_img = None

        # Canvas setup (only once!)
        self.canvas = tk.Canvas(root, bg="lightblue")
        self.canvas.pack(expand=True, fill="both")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        if self.tk_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # --- Aircraft and VOR State ---
        self.air_x_val = 10   # grid units (0–100)
        self.air_y_val = 10
        # VOR POSITION
        self.vor1_x = 50 * 5   # Center-ish
        self.vor1_y = 50 * 5

        self.vor2_x = 241.0 * 5   # grid x to canvas x
        self.vor2_y = 88.4 * 5    # grid y to canvas y

        self.active_vor = 1    # 1 or 2, which VOR is used for CDI logic
        self.airplane_marker = None
        self.airplane_img = None
        self.airplane_angle = 0
        self.obs_angle = 0
        self.speed = 0.7  # Default speed
        self.show_all_radials = True

        # VOR graphical elements
        self.radial_line = None
        self.recip_radial_line = None
        self.all_radials = []
        self.triangular_gradient = []
        self.radial_labels = []
        self.compass_rose_elements = []
        self.obs_rose_elements = []

        # Set indicator radius *before* indicator creation
        width = self.canvas.winfo_width() or 1800
        height = self.canvas.winfo_height() or 900
        self.indicator_radius = max(min(width, height) * 0.1, 60)

        # Joystick support
        self.joystick = None
        self.joystick_enabled = False
        if PYGAME_AVAILABLE:
            try:
                pygame.init()
                pygame.joystick.init()
                joystick_count = pygame.joystick.get_count()
                if joystick_count > 0:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.joystick_enabled = True
                    print(f"Joystick detected: {self.joystick.get_name()}")
                else:
                    print("No joystick detected")
            except Exception as e:
                print(f"Joystick initialization failed: {e}")
                self.joystick_enabled = False

        # ---- GUI PANELS/INDICATORS ----
        self.create_control_panel()
        self.draw_vor_station()
        self.create_output_labels()
        self.create_instruction_box()
        self.create_indicators()
        

        # --- Airplane image
        self.load_airplane_image()

        # Keyboard control
        self.pressed_keys = set()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

        # Mouse control
        self.mouse_control_enabled = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_center_x = 0
        self.mouse_center_y = 0
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.disable_mouse_control)
        self.canvas.bind("<Motion>", self.on_mouse_motion)

        self.movement_loop()
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.update_vor_output()
        #control bind
        self.controller = ControllerHandler(
            button_map={
                0: self.joy_reset,            # A
                2: self.joy_rotate_obs_left,  # X
                3: self.joy_rotate_obs_right, # Y
            },
            axis_callback=self.joy_axes,
            hat_callback=self.joy_hat
        )

    def on_canvas_click(self, event):
        # Check VOR output hide button
        if self.vor_output_visible and hasattr(self, "vor_output_hide_area"):
            x1, y1, x2, y2 = self.vor_output_hide_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.vor_output_visible = False
                self.create_output_labels()
                return
        # Check VOR output show tab
        elif not self.vor_output_visible and hasattr(self, "vor_output_show_area"):
            x1, y1, x2, y2 = self.vor_output_show_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.vor_output_visible = True
                self.create_output_labels()
                return
        
        # Check instruction box hide button
        if self.instruction_visible and hasattr(self, "instruction_hide_area"):
            x1, y1, x2, y2 = self.instruction_hide_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.instruction_visible = False
                self.create_instruction_box()
                return
        # Check instruction box show tab
        elif not self.instruction_visible and hasattr(self, "instruction_show_area"):
            x1, y1, x2, y2 = self.instruction_show_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.instruction_visible = True
                self.create_instruction_box()
                return
        
        # Else: pass through to old mouse logic for aircraft control
        self.on_mouse_click(event)


    def grid_to_canvas(self, x_grid, y_grid):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        # Your grid goes from 0 to 100 (change if needed)
        canvas_x = x_grid / 100 * width
        canvas_y = y_grid / 100 * height
        return canvas_x, canvas_y


    def create_control_panel(self):
        """Create control panel with buttons and sliders."""
        control_frame = tk.Frame(self.root, bg="#d0d0d0", bd=2, relief=tk.RAISED)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        # OBS Control
        obs_frame = tk.Frame(control_frame, bg="#d0d0d0")
        obs_frame.pack(side=tk.LEFT, padx=10, pady=5)
        tk.Label(obs_frame, text="OBS Setting:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        obs_btn_frame = tk.Frame(obs_frame, bg="#d0d0d0")
        obs_btn_frame.pack(side=tk.TOP, pady=5)
        tk.Button(obs_btn_frame, text="\u25c4 CCW", command=lambda: self.rotate_obs(-5), 
                  bg="#a0a0ff", width=6).pack(side=tk.LEFT, padx=2)
        self.obs_value_label = tk.Label(obs_btn_frame, text="000\u00b0", bg="#d0d0d0", 
                                       font=("Arial", 12, "bold"), width=5)
        self.obs_value_label.pack(side=tk.LEFT, padx=5)
        tk.Button(obs_btn_frame, text="CW \u25ba", command=lambda: self.rotate_obs(5), 
                  bg="#a0a0ff", width=6).pack(side=tk.LEFT, padx=2)
        
        # Speed Control
        speed_frame = tk.Frame(control_frame, bg="#d0d0d0")
        speed_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(speed_frame, text="Aircraft Speed:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        self.speed_scale = tk.Scale(speed_frame, from_=0.1, to=2.0, resolution=0.1, orient=tk.HORIZONTAL, 
                                     length=150, bg="#d0d0d0", command=self.set_speed)
        self.speed_scale.set(self.speed)
        self.speed_scale.pack(side=tk.TOP)
        
        # Display Options
        display_frame = tk.Frame(control_frame, bg="#d0d0d0")
        display_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(display_frame, text="Display Options:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        self.radials_var = tk.IntVar(value=1)
        tk.Checkbutton(display_frame, text="Show All Radials", variable=self.radials_var, 
                      bg="#d0d0d0", command=self.toggle_radials).pack(side=tk.TOP, anchor=tk.W)
        
        # Background Options - Single Toggle Button
        if MATPLOTLIB_AVAILABLE:
            background_frame = tk.Frame(control_frame, bg="#d0d0d0")
            background_frame.pack(side=tk.LEFT, padx=20, pady=5)
            tk.Label(background_frame, text="Background:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
            
            # Initialize background state
            self.current_bg_mode = "default"  # default, radar, navigation, simple
            self.bg_toggle_button = tk.Button(background_frame, text="Switch to Radar", 
                                            command=self.toggle_background, 
                                            bg="#ff9999", font=("Arial", 10, "bold"), width=14)
            self.bg_toggle_button.pack(side=tk.TOP, pady=2)
        
        # Compass Launch Button
        compass_frame = tk.Frame(control_frame, bg="#d0d0d0")
        compass_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(compass_frame, text="Navigation:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        
        # Real-World Map Button
        if FOLIUM_AVAILABLE:
            tk.Button(compass_frame, text="Open Real-World Map", command=self.open_real_world_map, bg="#66ff66", font=("Arial", 10, "bold"), width=18).pack(side=tk.TOP, pady=2)
            tk.Button(compass_frame, text="Load VOR Stations", command=self.show_vor_stations, bg="#66ccff", font=("Arial", 10, "bold"), width=18).pack(side=tk.TOP, pady=2)
        
        # --- VOR SELECTOR ---
        vor_select_frame = tk.Frame(control_frame, bg="#d0d0d0")
        vor_select_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(vor_select_frame, text="Active VOR:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        self.active_vor_var = tk.IntVar(value=1)
        tk.Radiobutton(vor_select_frame, text="VOR 1", variable=self.active_vor_var, value=1, command=self.set_active_vor, bg="#d0d0d0").pack(anchor=tk.W)
        tk.Radiobutton(vor_select_frame, text="VOR 2", variable=self.active_vor_var, value=2, command=self.set_active_vor, bg="#d0d0d0").pack(anchor=tk.W)

        
        # Reset Button
        reset_frame = tk.Frame(control_frame, bg="#d0d0d0")
        reset_frame.pack(side=tk.RIGHT, padx=20, pady=5)
        tk.Button(reset_frame, text="Reset Simulation", command=self.reset_simulation, 
                  bg="#ff9090", font=("Arial", 10, "bold"), width=15).pack(side=tk.TOP, pady=5)

    def set_active_vor(self):
        self.active_vor = self.active_vor_var.get()
        self.redraw_all()

    def launch_compass_window(self):
        """Launch compass.py as a separate Pygame window."""
        script_path = os.path.join(os.path.dirname(__file__), "compass.py")
        if os.path.exists(script_path):
            try:
                subprocess.Popen([sys.executable, script_path])
            except Exception as e:
                print(f"Failed to launch compass.py: {e}")
        else:
            print("compass.py not found in the current directory.")

    def open_real_world_map(self):
        """Create and open a real-world interactive map with VOR stations."""
        if not FOLIUM_AVAILABLE:
            print("Folium not available. Cannot create real-world map.")
            return
        
        try:
            # Create a map centered on the Philippines
            m = folium.Map(
                location=[13.41, 122.56],  # Philippines center
                zoom_start=6,
                tiles='OpenStreetMap'
            )
            
            # Add VOR stations as markers
            for vor_id, station in REAL_VOR_STATIONS.items():
                # Different colors for different countries
                color = {
                    'Philippines': 'red',
                    'Vietnam': 'blue', 
                    'Thailand': 'green',
                    'Singapore': 'orange',
                    'Malaysia': 'purple',
                    'Indonesia': 'darkred',
                    'USA': 'darkblue'
                }.get(station['country'], 'gray')
                
                popup_text = f"""
                <b>{station['name']} ({vor_id})</b><br>
                Frequency: {station['freq']} MHz<br>
                Country: {station['country']}<br>
                Coordinates: {station['lat']:.4f}, {station['lon']:.4f}
                """
                
                folium.Marker(
                    location=[station['lat'], station['lon']],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=f"{vor_id} - {station['name']}",
                    icon=folium.Icon(color=color, icon='radio', prefix='fa')
                ).add_to(m)
            
            # Add a legend
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 150px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px">
            <p><b>VOR Stations Legend</b></p>
            <p><i class="fa fa-circle" style="color:red"></i> Philippines</p>
            <p><i class="fa fa-circle" style="color:blue"></i> Vietnam</p>
            <p><i class="fa fa-circle" style="color:green"></i> Thailand</p>
            <p><i class="fa fa-circle" style="color:orange"></i> Singapore</p>
            <p><i class="fa fa-circle" style="color:purple"></i> Malaysia</p>
            <p><i class="fa fa-circle" style="color:darkred"></i> Indonesia</p>
            </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Save the map to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            map_path = temp_file.name
            temp_file.close()
            m.save(map_path)
            
            # Try to open in embedded window first, fallback to browser
            if TKINTERWEB_AVAILABLE:
                self.open_embedded_map(map_path)
            else:
                # Show option dialog for users without tkinterweb
                choice = messagebox.askyesno(
                    "Map Display Option",
                    "The map will open in your web browser.\n\n"
                    "Would you like to install tkinterweb for embedded maps?\n"
                    "(You can install it later with: pip install tkinterweb)",
                    icon='question'
                )
                if choice:
                    messagebox.showinfo(
                        "Installation Instructions", 
                        "To install tkinterweb for embedded maps:\n\n"
                        "1. Open Command Prompt or Terminal\n"
                        "2. Run: pip install tkinterweb\n"
                        "3. Restart the simulator\n\n"
                        "For now, the map will open in your browser."
                    )
                
                # Open in browser
                webbrowser.open(f'file://{map_path}')
                print(f"Real-world VOR map opened in browser: {map_path}")
            
        except Exception as e:
            print(f"Error creating real-world map: {e}")

    def open_embedded_map(self, map_path):
        """Open the map in an embedded window with Python 3.12.4 compatibility fixes."""
        try:
            import tkinterweb
            print(f"tkinterweb version: {getattr(tkinterweb, '__version__', 'Unknown')}")
            
            # Create a new window for the embedded map
            map_window = tk.Toplevel(self.root)
            map_window.title("Real-World VOR Stations Map")
            map_window.geometry("1200x800")
            map_window.configure(bg="#2c3e50")
            
            # Make window modal and bring to front
            map_window.transient(self.root)
            map_window.grab_set()
            map_window.focus_force()
            
            # Center the window
            map_window.update_idletasks()
            x = (map_window.winfo_screenwidth() // 2) - (1200 // 2)
            y = (map_window.winfo_screenheight() // 2) - (800 // 2)
            map_window.geometry(f"1200x800+{x}+{y}")
            
            # Header frame with enhanced styling
            header_frame = tk.Frame(map_window, bg="#34495e", height=60)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            
            title_label = tk.Label(header_frame, text="🗺️ Real-World VOR Stations Map", 
                                 font=("Arial", 16, "bold"), fg="white", bg="#34495e")
            title_label.pack(pady=15)
            
            # Status frame
            status_frame = tk.Frame(map_window, bg="#ecf0f1", height=35)
            status_frame.pack(fill=tk.X)
            status_frame.pack_propagate(False)
            
            status_label = tk.Label(status_frame, text="Initializing map display for Python 3.12.4...", 
                                   font=("Arial", 10), fg="#7f8c8d", bg="#ecf0f1")
            status_label.pack(pady=8)
            
            # Control buttons frame
            button_frame = tk.Frame(map_window, bg="#bdc3c7", height=45)
            button_frame.pack(fill=tk.X)
            button_frame.pack_propagate(False)
            
            # Create buttons with better styling
            browser_btn = tk.Button(button_frame, text="🌐 Open in Browser", 
                                   command=lambda: webbrowser.open(f'file://{map_path}'), 
                                   bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                                   padx=15, pady=5, relief=tk.FLAT)
            browser_btn.pack(side=tk.LEFT, padx=10, pady=8)
            
            reload_btn = tk.Button(button_frame, text="🔄 Reload Map", 
                                  command=lambda: self.reload_embedded_map_v2(web_frame, map_path, status_label), 
                                  bg="#f39c12", fg="white", font=("Arial", 10, "bold"),
                                  padx=15, pady=5, relief=tk.FLAT)
            reload_btn.pack(side=tk.LEFT, padx=5, pady=8)
            
            close_btn = tk.Button(button_frame, text="❌ Close", command=map_window.destroy, 
                                 bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                                 padx=15, pady=5, relief=tk.FLAT)
            close_btn.pack(side=tk.RIGHT, padx=10, pady=8)
            
            # Info label
            info_label = tk.Label(button_frame, text="📋 Map may appear blank in embedded view - use Browser option for full functionality", 
                                 font=("Arial", 9), fg="#7f8c8d", bg="#bdc3c7")
            info_label.pack(side=tk.RIGHT, padx=20, pady=8)
            
            # Create web frame
            web_frame = tk.Frame(map_window, bg="white", relief=tk.SUNKEN, bd=1)
            web_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
            
            # Load the map with Python 3.12 compatibility
            self.load_map_python312_compatible(web_frame, map_path, status_label)
            
            print(f"Embedded map window created for: {map_path}")
            
        except ImportError as ie:
            print(f"tkinterweb not available: {ie}")
            # Fallback to browser
            webbrowser.open(f'file://{map_path}')
            messagebox.showinfo("Map Opened", "Map opened in your default browser.\n\nTo view maps embedded in the app, install: pip install tkinterweb")
            
        except Exception as e:
            print(f"Error opening embedded map: {e}")
            # Fallback to browser
            webbrowser.open(f'file://{map_path}')
            messagebox.showerror("Embedded Map Error", f"Could not open embedded map: {str(e)}\n\nMap opened in browser instead.")

    def load_map_python312_compatible(self, web_frame, map_path, status_label):
        """Load map with enhanced Python 3.12.4 and tkinterweb 4.4.4 compatibility."""
        import tkinterweb
        import urllib.parse
        import urllib.request
        import time
        
        success = False
        attempt = 1
        
        def try_loading_method(method_num, description):
            nonlocal success
            if success:
                return
                
            try:
                status_label.config(text=f"Attempt {method_num}: {description}...")
                web_frame.update()
                
                if method_num == 1:
                    # Method 1: Enhanced HtmlFrame with WebView2 backend
                    print("Trying Method 1: Enhanced HtmlFrame with WebView2")
                    web_view = tkinterweb.HtmlFrame(web_frame, messages_enabled=False)
                    web_view.pack(fill=tk.BOTH, expand=True)
                    
                    # Read HTML and modify for better compatibility
                    with open(map_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Enhance HTML for better rendering
                    enhanced_html = self.enhance_html_for_embedding(html_content)
                    
                    # Load with delay for better initialization
                    def delayed_load():
                        try:
                            web_view.load_html(enhanced_html)
                            status_label.config(text="Method 1: Map loaded successfully!")
                            print("Method 1 successful")
                        except Exception as inner_e:
                            print(f"Method 1 delayed load failed: {inner_e}")
                            web_frame.after(100, lambda: try_loading_method(2, "File URL loading"))
                    
                    web_frame.after(500, delayed_load)
                    success = True
                    
                elif method_num == 2:
                    # Method 2: File URL approach
                    print("Trying Method 2: File URL approach")
                    for widget in web_frame.winfo_children():
                        widget.destroy()
                    
                    web_view = tkinterweb.HtmlFrame(web_frame, messages_enabled=False)
                    web_view.pack(fill=tk.BOTH, expand=True)
                    
                    # Create proper file URL
                    file_url = 'file:///' + map_path.replace('\\', '/').replace(' ', '%20')
                    
                    def delayed_url_load():
                        try:
                            web_view.load_url(file_url)
                            status_label.config(text="Method 2: File URL loaded successfully!")
                            print("Method 2 successful")
                        except Exception as inner_e:
                            print(f"Method 2 failed: {inner_e}")
                            web_frame.after(100, lambda: try_loading_method(3, "Alternative HTML loading"))
                    
                    web_frame.after(500, delayed_url_load)
                    success = True
                    
                elif method_num == 3:
                    # Method 3: Simple HTML display with compatibility message
                    print("Trying Method 3: Compatibility fallback")
                    for widget in web_frame.winfo_children():
                        widget.destroy()
                    
                    # Create a simple message frame
                    message_frame = tk.Frame(web_frame, bg="#ffffff")
                    message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
                    
                    # Compatibility notice
                    title_label = tk.Label(message_frame, text="🔧 Embedded Display Compatibility Notice", 
                                         font=("Arial", 16, "bold"), fg="#e74c3c", bg="#ffffff")
                    title_label.pack(pady=(20, 15))
                    
                    msg_text = """The embedded map display is experiencing compatibility issues with:

• Python 3.12.4
• tkinterweb 4.4.4  
• Current Windows environment

This is a known limitation of the tkinterweb package.

WORKAROUND:
Click the "🌐 Open in Browser" button above to view the full interactive map.

The browser version includes:
✓ Interactive VOR station markers with detailed information
✓ Zoom and pan controls for easy navigation
✓ Station tooltips with frequencies and identifiers  
✓ Complete legend and layer controls
✓ Real-world mapping data"""
                    
                    message_label = tk.Label(message_frame, text=msg_text, font=("Arial", 11), 
                                           fg="#2c3e50", bg="#ffffff", justify=tk.LEFT)
                    message_label.pack(pady=15)
                    
                    # Recommendation box
                    rec_frame = tk.Frame(message_frame, bg="#d5f4e6", relief=tk.SOLID, bd=1)
                    rec_frame.pack(fill=tk.X, pady=(20, 10), padx=10)
                    
                    rec_label = tk.Label(rec_frame, text="💡 RECOMMENDED: Use the Browser option for optimal experience", 
                                       font=("Arial", 11, "bold"), fg="#27ae60", bg="#d5f4e6")
                    rec_label.pack(pady=12)
                    
                    status_label.config(text="Compatibility mode - Use browser option above")
                    success = True
                    print("Method 3 - compatibility message displayed")
                    
            except Exception as e:
                print(f"Method {method_num} failed: {e}")
                if method_num < 3:
                    web_frame.after(100, lambda: try_loading_method(method_num + 1, "Next method"))
                else:
                    status_label.config(text="All methods failed - Use browser option")
        
        # Start with method 1
        try_loading_method(1, "Enhanced HtmlFrame loading")

    def enhance_html_for_embedding(self, html_content):
        """Enhance HTML content for better embedded display compatibility."""
        # Add viewport and compatibility meta tags
        enhanced_html = html_content
        
        if '<head>' in enhanced_html:
            # Insert compatibility enhancements
            compatibility_tags = '''
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <style>
        body { margin: 0; padding: 0; overflow: hidden; }
        .folium-map { height: 100vh !important; width: 100vw !important; }
    </style>'''
            enhanced_html = enhanced_html.replace('<head>', f'<head>{compatibility_tags}')
        
        # Force map to fill container
        if 'leaflet' in enhanced_html.lower():
            map_resize_script = '''
    <script>
        window.addEventListener('load', function() {
            setTimeout(function() {
                if (typeof window.map !== 'undefined') {
                    window.map.invalidateSize();
                }
            }, 1000);
        });
    </script>'''
            enhanced_html = enhanced_html.replace('</body>', f'{map_resize_script}</body>')
        
        return enhanced_html

    def reload_embedded_map_v2(self, web_frame, map_path, status_label):
        """Enhanced reload function for embedded map."""
        print("Reloading embedded map...")
        status_label.config(text="Reloading map display...")
        
        # Clear existing content
        for widget in web_frame.winfo_children():
            widget.destroy()
        
        # Reload after brief delay
        web_frame.after(500, lambda: self.load_map_python312_compatible(web_frame, map_path, status_label))

    def show_vor_stations(self):
        """Display a window with VOR station information."""
        if not FOLIUM_AVAILABLE:
            print("Folium not available.")
            return
            
        # Create a new window for VOR station list
        vor_window = tk.Toplevel(self.root)
        vor_window.title("Real VOR Stations Database")
        vor_window.geometry("600x500")
        vor_window.configure(bg="#f0f0f0")
        
        # Create a scrollable text widget
        text_frame = tk.Frame(vor_window, bg="#f0f0f0")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set, 
                             font=("Courier", 10), bg="white")
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Format VOR station information
        vor_info = "REAL VOR STATIONS DATABASE\n"
        vor_info += "=" * 50 + "\n\n"
        
        # Group by country
        countries = {}
        for vor_id, station in REAL_VOR_STATIONS.items():
            country = station['country']
            if country not in countries:
                countries[country] = []
            countries[country].append((vor_id, station))
        
        for country in sorted(countries.keys()):
            vor_info += f"{country.upper()}\n"
            vor_info += "-" * len(country) + "\n"
            
            for vor_id, station in sorted(countries[country]):
                vor_info += f"{vor_id:4} - {station['name']:<25} "
                vor_info += f"Freq: {station['freq']:<6} MHz "
                vor_info += f"({station['lat']:8.4f}, {station['lon']:9.4f})\n"
            vor_info += "\n"
        
        # Add usage instructions
        vor_info += "\nUSAGE INSTRUCTIONS:\n"
        vor_info += "=" * 20 + "\n"
        vor_info += "1. Click 'Open Real-World Map' to view VOR stations on an interactive map\n"
        vor_info += "2. Each VOR station is color-coded by country\n"
        vor_info += "3. Click on any VOR marker to see detailed information\n"
        vor_info += "4. Use this data for realistic navigation planning\n"
        vor_info += "5. Frequencies are in MHz (VHF range 108-118 MHz)\n\n"
        vor_info += "Note: This simulator uses grid coordinates (0-100), but you can\n"
        vor_info += "reference real VOR stations for authentic navigation scenarios."
        
        text_widget.insert(tk.END, vor_info)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Add buttons
        button_frame = tk.Frame(vor_window, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(button_frame, text="Open Real-World Map", 
                 command=self.open_real_world_map, bg="#66ff66", 
                 font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_frame, text="Close", 
                 command=vor_window.destroy, bg="#ffaa66", 
                 font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=5)

    def load_vor_station(self, vor_id):
        """Load a real VOR station's data into the simulator."""
        if vor_id not in REAL_VOR_STATIONS:
            print(f"VOR station {vor_id} not found in database.")
            return
        
        station = REAL_VOR_STATIONS[vor_id]
        
        # For demonstration, we can show the VOR info and optionally
        # set the simulator to use this VOR's frequency/position conceptually
        print(f"Loaded VOR Station: {station['name']} ({vor_id})")
        print(f"Frequency: {station['freq']} MHz")
        print(f"Location: {station['lat']:.4f}, {station['lon']:.4f}")
        print(f"Country: {station['country']}")
        
        # Update the result text if visible to show current VOR
        if hasattr(self, 'result_text') and getattr(self, 'vor_output_visible', True):
            current_text = self.canvas.itemcget(self.result_text, 'text')
            updated_text = f"Using Real VOR: {station['name']} ({vor_id}) - {station['freq']} MHz\n" + current_text
            self.canvas.itemconfig(self.result_text, text=updated_text)

    def create_vor_selection_menu(self):
        """Create a dropdown menu for selecting real VOR stations."""
        # This could be added to the control panel if desired
        vor_frame = tk.Frame(self.root, bg="#d0d0d0")
        vor_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        tk.Label(vor_frame, text="Real VOR Station:", bg="#d0d0d0", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # Create dropdown with VOR stations
        self.vor_var = tk.StringVar()
        vor_options = [f"{vor_id} - {data['name']}" for vor_id, data in REAL_VOR_STATIONS.items()]
        vor_dropdown = tk.OptionMenu(vor_frame, self.vor_var, *vor_options, 
                                   command=self.on_vor_selection)
        vor_dropdown.config(bg="#e0e0e0", width=25)
        vor_dropdown.pack(side=tk.LEFT, padx=5)
    
    def on_vor_selection(self, selection):
        """Handle VOR station selection from dropdown."""
        vor_id = selection.split(' - ')[0]  # Extract VOR ID
        self.load_vor_station(vor_id)


    def toggle_background(self):
        """Toggle between radar and default background only."""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showinfo("Feature Unavailable", 
                              "Matplotlib is not available. Install with: pip install matplotlib")
            return
        
        # Toggle between only two modes: default and radar
        if self.current_bg_mode == "default":
            self.current_bg_mode = "radar"
            self.bg_toggle_button.config(text="Switch to Default", bg="#99ff99")
            self.apply_matplotlib_background('radar')
        else:
            self.current_bg_mode = "default"
            self.bg_toggle_button.config(text="Switch to Radar", bg="#ff9999")
            self.restore_default_background()

    def apply_matplotlib_background(self, style='simple'):
        """Apply a matplotlib-generated background to the canvas."""
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showinfo("Feature Unavailable", 
                              "Matplotlib is not available. Install with: pip install matplotlib")
            return
        try:
            # Get canvas dimensions
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width = 800
                canvas_height = 600
            bg_image = create_matplotlib_background(canvas_width, canvas_height, style)
            if bg_image:
                print(f"Successfully generated {style} matplotlib background: {canvas_width}x{canvas_height}")
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                self.using_matplotlib_bg = True
                # Clear existing backgrounds and redraw everything with new background
                self.redraw_all()
            else:
                print(f"Failed to generate matplotlib background with style: {style}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create matplotlib background: {str(e)}")

    def restore_default_background(self):
        """Restore the default background image."""
        try:
            self.using_matplotlib_bg = False
            # Redraw everything with default background
            self.redraw_all()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restore background: {str(e)}")


    def set_speed(self, val):
        """Set aircraft speed from the slider."""
        self.speed = float(val)

    def toggle_radials(self):
        """Toggle display of all background radials."""
        self.show_all_radials = bool(self.radials_var.get())
        self.draw_vor_station()  # Redraw VOR with updated radial settings

    def create_indicators(self):
        self.create_heading_indicator()
        self.create_cdi_indicator()
        self.create_obs_indicator()
        self.update_all_meters()

    def update_all_meters(self):
        ax = self.air_x_val
        ay = self.air_y_val
        # Use ACTIVE VOR coordinates
        if self.active_vor == 1:
            vx, vy = self.vor1_x / 5, self.vor1_y / 5
        else:
            vx, vy = self.vor2_x / 5, self.vor2_y / 5
        obs = self.obs_angle
        hdg = self.airplane_angle % 360
        bearing_to_vor = calculate_bearing(ax, ay, vx, vy)
        direction = calculate_vor_to_from(obs, bearing_to_vor)
        self.update_heading_indicator(hdg)
        self.update_cdi_indicator(obs, bearing_to_vor, direction)
        self.update_obs_indicator(obs)
        self.update_obs_cdi_needle(obs, bearing_to_vor)



    def redraw_all(self, event=None):
        """Redraw all main graphical elements, in the correct order."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.indicator_radius = max(min(width, height) * 0.1, 60)

        # Clear the canvas first
        self.canvas.delete("all")

        # Draw background image or matplotlib background
        if getattr(self, 'using_matplotlib_bg', False) and hasattr(self, 'bg_photo') and self.bg_photo:
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo, tags="background")
        elif self.tk_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # Draw triangular gradient cones for the active VOR (***must be before airplane/markers***)
        if self.active_vor == 1:
            self.draw_triangular_gradient(self.obs_angle, self.vor1_x, self.vor1_y, color="red")
        else:
            self.draw_triangular_gradient(self.obs_angle, self.vor2_x, self.vor2_y, color="magenta")

        # Draw both VOR stations (includes active VOR radials and labels)
        self.draw_vor_station()

        # Draw the airplane at its current position
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)

        # Redraw panels and overlays
        self.create_output_labels()
        self.create_instruction_box()

        # Redraw indicators/meters
        self.create_indicators()
        self.update_all_meters()  # Keep needles/arrows up-to-date

        # Update the VOR info panel and any dynamic overlays
        self.update_vor_output()




    def on_canvas_resize(self, event):
        self.redraw_all()



    def reset_simulation(self):
        """Reset simulation to initial state."""
        self.air_x_val = 10
        self.air_y_val = 10
        self.airplane_angle = 0
        self.obs_angle = 0
        self.speed = 0.5
        self.speed_scale.set(self.speed)

        # Get active VOR coordinates
        if self.active_vor == 1:
            active_x, active_y = self.vor1_x, self.vor1_y
        else:
            active_x, active_y = self.vor2_x, self.vor2_y

        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.draw_radial_line(self.obs_angle, active_x, active_y)
        self.update_vor_output()
        self.obs_value_label.config(text=f"{int(self.obs_angle):03d}\u00b0")


    def draw_vor_station(self):
        """Draw TWO VOR stations and the radials for the active VOR."""
        # Clear existing radials
        for radial in self.all_radials:
            self.canvas.delete(radial)
        self.all_radials.clear()

        # Draw VOR 1 (blue)
        self.canvas.create_oval(
            self.vor1_x - 15, self.vor1_y - 15, self.vor1_x + 15, self.vor1_y + 15,
            fill="blue", outline="darkblue", width=3
        )
        self.canvas.create_text(
            self.vor1_x, self.vor1_y - 25,
            text="VOR 1", font=("Arial", 12, "bold"), fill="darkblue"
        )

        # Draw VOR 2 (magenta)
        self.canvas.create_oval(
            self.vor2_x - 15, self.vor2_y - 15, self.vor2_x + 15, self.vor2_y + 15,
            fill="magenta", outline="purple", width=3
        )
        self.canvas.create_text(
            self.vor2_x, self.vor2_y - 25,
            text="VOR 2", font=("Arial", 12, "bold"), fill="purple"
        )

        # Set which VOR is active (1 or 2)
        if self.active_vor == 1:
            active_x, active_y = self.vor1_x, self.vor1_y
        else:
            active_x, active_y = self.vor2_x, self.vor2_y

        # Draw radials for the active VOR
        if self.show_all_radials:
            for angle in range(0, 360, 10):
                line_width = 2 if angle % 90 == 0 else 1
                dash_pattern = (5, 5) if angle % 30 != 0 else None
                end_x = active_x + 800 * sin(radians(angle))
                end_y = active_y - 800 * cos(radians(angle))
                color = "gray" if angle % 30 != 0 else "darkgray"
                radial = self.canvas.create_line(
                    active_x, active_y, end_x, end_y,
                    fill=color, width=line_width, dash=dash_pattern, tags="background_radial"
                )
                self.all_radials.append(radial)

        # Draw selected radial line for the active VOR
        self.draw_radial_line(self.obs_angle, active_x, active_y)
        # Draw cone for the selected radial and VOR
        self.draw_triangular_gradient(self.obs_angle, active_x, active_y)




    def draw_radial_line(self, obs_angle, vx, vy):
        # Remove old lines first
        if self.radial_line:
            self.canvas.delete(self.radial_line)
        if self.recip_radial_line:
            self.canvas.delete(self.recip_radial_line)

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        max_distance = max(
            sqrt((canvas_width - vx)**2 + (canvas_height - vy)**2),
            sqrt(vx**2 + vy**2),
            sqrt((canvas_width - vx)**2 + vy**2),
            sqrt(vx**2 + (canvas_height - vy)**2)
        )
        length = int(max_distance * 1.2)
        angle_rad = radians(obs_angle)

        end_x = vx + length * sin(angle_rad)
        end_y = vy - length * cos(angle_rad)
        self.radial_line = self.canvas.create_line(
            vx, vy, end_x, end_y, fill="Red", width=2, tags="radial_line"
        )

        recip_end_x = vx - length * sin(angle_rad)
        recip_end_y = vy + length * cos(angle_rad)
        self.recip_radial_line = self.canvas.create_line(
            vx, vy, recip_end_x, recip_end_y, fill="Red", width=2, tags="radial_line"
        )
        self.obs_value_label.config(text=f"{int(obs_angle):03d}\u00b0")



    def draw_triangular_gradient(self, obs_angle, vx, vy, color="red"):
        """Draws two radial cones (main and reciprocal) centered on (vx, vy) using the current OBS angle."""
        # Remove previous
        for item in self.triangular_gradient:
            self.canvas.delete(item)
        self.triangular_gradient.clear()

        # Canvas info
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        max_distance = max(
            sqrt((canvas_width - vx)**2 + (canvas_height - vy)**2),
            sqrt(vx**2 + vy**2),
            sqrt((canvas_width - vx)**2 + vy**2),
            sqrt(vx**2 + (canvas_height - vy)**2)
        )
        length = int(max_distance * 1.2)
        spread_angle = 15  # degrees, half width

        def draw_cone(center_deg, main_color):
            c = radians(center_deg)
            left = radians(center_deg - spread_angle)
            right = radians(center_deg + spread_angle)
            # Center, left, right lines
            center_end = (vx + length * sin(c), vy - length * cos(c))
            left_end = (vx + length * sin(left), vy - length * cos(left))
            right_end = (vx + length * sin(right), vy - length * cos(right))
            # Cone outline (just lines)
            l_center = self.canvas.create_line(vx, vy, *center_end, fill=main_color, width=3, tags="triangular_gradient")
            l_left = self.canvas.create_line(vx, vy, *left_end, fill="green", width=2, tags="triangular_gradient")
            l_right = self.canvas.create_line(vx, vy, *right_end, fill="green", width=2, tags="triangular_gradient")
            cone = self.canvas.create_polygon(
                vx, vy, left_end[0], left_end[1], right_end[0], right_end[1],
                fill="", outline="green", width=2, tags="triangular_gradient"
            )
            self.triangular_gradient.extend([l_center, l_left, l_right, cone])

        # Main radial cone (red)
        draw_cone(obs_angle, main_color=color)
        # Reciprocal cone (blue)
        draw_cone((obs_angle + 180) % 360, main_color="blue")




    def get_indicator_positions(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        margin = max(min(width, height) * 0.04, 20)
        radius = self.indicator_radius

        # Three meters, fixed at bottom left, with responsive spacing
        x0 = margin + radius      # HDG
        x1 = x0 + radius * 2.3    # CDI (space by 2.3 radii, adjust as needed)
        x2 = x1 + radius * 2.3    # OBS

        y = height - margin - radius  # Always near the bottom edge

        return [x0, x1, x2], y



    
    def load_airplane_image(self):
        """Loads a custom airplane image if available, otherwise creates a realistic top-down airplane."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            airplane_path = os.path.join(script_dir, "airplane_icon0.png")#change 
            if os.path.exists(airplane_path):
                img = Image.open(airplane_path)
                # Auto-resize to 140x140 (adjust if your drawing is a different size)
                self.base_airplane_image = img.resize((70, 70), Image.LANCZOS).convert("RGBA")
                print("Loaded custom airplane image from file.")
            else:
                self.base_airplane_image = self.create_airplane_image()
                print("No airplane_icon.png found; using generated airplane image.")
        except Exception as e:
            print(f"Error loading airplane image, using default. Reason: {e}")
            self.base_airplane_image = self.create_airplane_image()


    def create_airplane_image(self, propeller_angle=0):
        """
        Creates a more realistic top-down airplane icon with shading, windows, and twin propellers.
        propeller_angle: The angle of the propeller blades (for animation).
        Returns a PIL Image (RGBA).
        """
        size = 95
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Fuselage (main body, shaded silver/gray)
        body_width = size * 0.14
        body_length = size * 0.70
        body_x0 = (size - body_width) / 2
        body_y0 = size * 0.13
        body_x1 = (size + body_width) / 2
        body_y1 = body_y0 + body_length
        draw.rounded_rectangle([body_x0, body_y0, body_x1, body_y1], radius=body_width/2, fill="#d0d8dd", outline="#888", width=3)

        # Cockpit (front window, blue/gray ellipse)
        cockpit_y = body_y0 + size * 0.07
        cockpit_h = size * 0.11
        draw.ellipse([
            body_x0 + body_width * 0.1, 
            cockpit_y, 
            body_x1 - body_width * 0.1, 
            cockpit_y + cockpit_h
        ], fill="#7ec7e6", outline="#6ca0c9", width=2)

        # Wings (main, metallic gray)
        wing_span = size * 0.85
        wing_y = body_y0 + body_length * 0.36
        wing_h = size * 0.17
        wing_x0 = (size - wing_span) / 2
        wing_x1 = (size + wing_span) / 2
        draw.polygon([
            (wing_x0, wing_y + wing_h/2),
            (size/2, wing_y - wing_h/2),
            (wing_x1, wing_y + wing_h/2),
            (size/2, wing_y + wing_h),
        ], fill="#b3b7b9", outline="#888", width=3)

        # Engine pods (left/right under wings)
        engine_radius = size * 0.065
        engine_offset = size * 0.24
        engine_centers = []
        for side in [-1, 1]:
            ex = size/2 + side * engine_offset
            ey = wing_y + wing_h * 0.73
            draw.ellipse([
                ex - engine_radius, ey - engine_radius, ex + engine_radius, ey + engine_radius
            ], fill="#666", outline="#333", width=2)
            engine_centers.append((ex, ey))

        # Tail (vertical stabilizer)
        tail_y0 = body_y1 - size * 0.12
        tail_y1 = tail_y0 - size * 0.12
        tail_w = body_width * 0.9
        draw.polygon([
            (size/2 - tail_w/2, tail_y0),
            (size/2, tail_y1),
            (size/2 + tail_w/2, tail_y0)
        ], fill="#8ca6b3", outline="#455963", width=2)

        # Horizontal stabilizer (tail wings)
        stab_span = size * 0.37
        stab_y = tail_y0 + size * 0.04
        stab_h = size * 0.045
        draw.rectangle([
            size/2 - stab_span/2, stab_y,
            size/2 + stab_span/2, stab_y + stab_h
        ], fill="#b3b7b9", outline="#888", width=2)

        # Windows (dark gray, cockpit and passenger)
        win_w = size * 0.07
        win_h = size * 0.03
        win_gap = size * 0.09
        n_windows = 3
        for i in range(n_windows):
            win_y = body_y0 + size * 0.18 + i * win_gap
            draw.ellipse([
                size/2 - win_w/2, win_y,
                size/2 + win_w/2, win_y + win_h
            ], fill="#1a1a1a", outline="#1a1a1a")
        
        # Outline shadow (simulate drop shadow)
        shadow = Image.new('RGBA', img.size, (0,0,0,0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle([body_x0+4, body_y0+7, body_x1+4, body_y1+7], radius=body_width/2, fill=(0,0,0,50))
        img = Image.alpha_composite(shadow, img)

        # --- Twin minimalist propellers (on engine centers) ---
        for ex, ey in engine_centers:
            prop_len = size * 0.14
            prop_width = int(size * 0.028)
            # Draw two blades, 90deg apart, rotated by propeller_angle
            for blade_angle in [0, 90]:
                theta = math.radians(propeller_angle + blade_angle)
                x1 = ex + prop_len * math.cos(theta)
                y1 = ey + prop_len * math.sin(theta)
                x2 = ex - prop_len * math.cos(theta)
                y2 = ey - prop_len * math.sin(theta)
                draw.line([x1, y1, ex, ey, x2, y2], fill="#c7b170", width=prop_width)
            # Draw hub (silver circle)
            hub_r = size * 0.025
            draw.ellipse([ex - hub_r, ey - hub_r, ex + hub_r, ey + hub_r], fill="#ededed", outline="#aaa", width=1)

        return img



    def create_output_labels(self):
        # Remove existing panel items
        if hasattr(self, 'vor_output_panel_items'):
            for item in self.vor_output_panel_items:
                self.canvas.delete(item)
        self.vor_output_panel_items = []
        if hasattr(self, 'vor_show_tab') and self.vor_show_tab:
            self.canvas.delete(self.vor_show_tab)
            self.vor_show_tab = None

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        # Responsive placement: panel in upper right, margin from edges
        margin = 20
        panel_width = int(0.20 * width)
        panel_height = int(0.23 * height)
        x1 = width - panel_width - margin
        y1 = margin
        x2 = width - margin
        y2 = margin + panel_height

        self.vor_output_panel_geom = (x1, y1, x2, y2)  # For redrawing/resizing

        if getattr(self, 'vor_output_visible', True):
            # Main panel
            panel_bg = self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="white", outline="black", width=2
            )
            # "Hide" button on left edge, vertical
            hide_btn = self.canvas.create_rectangle(
                x1-35, y1, x1, y1+60, fill="#ffd4d4", outline="black"
            )
            hide_text = self.canvas.create_text(
                x1-18, y1+30, text="Hide", angle=90,
                font=("Arial", 12, "bold"), fill="red"
            )
            # Result text area
            result_text = self.canvas.create_text(
                x1+20, y1+15, anchor="nw", text="VOR Simulator Ready",
                font=("Arial", 10, "bold"), fill="black", width=(x2-x1-25)
            )
            self.result_text = result_text  # for dynamic updating
            self.vor_output_panel_items = [panel_bg, hide_btn, hide_text, result_text]
            self.vor_output_hide_area = (x1-35, y1, x1, y1+60)
        else:
            # "Show" tab, green, right edge
            tab_width = 45
            tab_height = 80
            tab_x1 = width - tab_width - 10
            tab_x2 = width - 10
            tab_y1 = margin
            tab_y2 = margin + tab_height
            self.vor_show_tab = self.canvas.create_rectangle(
                tab_x1, tab_y1, tab_x2, tab_y2, fill="#bbffbb", outline="black"
            )
            show_text = self.canvas.create_text(
                tab_x1 + tab_width // 2, tab_y1 + tab_height // 2,
                text="Show", angle=90, font=("Arial", 12, "bold"), fill="green"
            )
            self.vor_output_panel_items = [self.vor_show_tab, show_text]
            self.vor_output_show_area = (tab_x1, tab_y1, tab_x2, tab_y2)

    def create_instruction_box(self):
        """Create instruction box in upper right corner with hide/show functionality."""
        # Remove existing instruction panel items
        if hasattr(self, 'instruction_panel_items'):
            for item in self.instruction_panel_items:
                self.canvas.delete(item)
        self.instruction_panel_items = []
        if hasattr(self, 'instruction_show_tab') and self.instruction_show_tab:
            self.canvas.delete(self.instruction_show_tab)
            self.instruction_show_tab = None

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Position in upper right corner, below the VOR output panel
        margin = 20
        panel_width = int(0.20 * width)
        panel_height = int(0.25 * height)
        
        # Position below VOR output panel with extra spacing to avoid overlap
        vor_panel_bottom = margin + int(0.25 * height) + 24  # Match VOR panel height + extra margin
        x1 = width - panel_width - margin
        y1 = vor_panel_bottom
        x2 = width - margin
        y2 = vor_panel_bottom + panel_height

        self.instruction_panel_geom = (x1, y1, x2, y2)  # For redrawing/resizing

        if getattr(self, 'instruction_visible', True):
            # Main instruction panel
            panel_bg = self.canvas.create_rectangle(
                x1, y1, x2, y2, fill="#f0f8ff", outline="#4169e1", width=2
            )
            
            # Title bar
            title_bg = self.canvas.create_rectangle(
                x1, y1, x2, y1+25, fill="#4169e1", outline="#4169e1"
            )
            title_text = self.canvas.create_text(
                x1+10, y1+12, anchor="w", text="🎯 VOR Simulator Instructions",
                font=("Arial", 10, "bold"), fill="white"
            )
            
            # "Hide" button on left edge, vertical
            hide_btn = self.canvas.create_rectangle(
                x1-35, y1, x1, y1+60, fill="#ffe4e1", outline="#4169e1"
            )
            hide_text = self.canvas.create_text(
                x1-18, y1+30, text="Hide", angle=90,
                font=("Arial", 10, "bold"), fill="#4169e1"
            )
            
            # Instruction content
            instruction_content = """AIRCRAFT CONTROLS:
• Arrow Keys: Move aircraft
• Mouse: Click & drag to move
• A/D Keys: Rotate OBS (±5°)
• Q/E Keys: Fine OBS (±1°)
• R Key: Reset simulation

VOR NAVIGATION:
• Watch CDI needle deflection
• Center needle = on radial
• OBS sets selected radial
"""
            # Result text area
            instruction_text = self.canvas.create_text(
                x1+10, y1+35, anchor="nw", text=instruction_content,
                font=("Arial", 10, "bold"), fill="black", width=(x2-x1-20)
            )
            
            self.instruction_panel_items = [panel_bg, title_bg, title_text, hide_btn, hide_text, instruction_text]
            self.instruction_hide_area = (x1-35, y1, x1, y1+60)
        else:
            # "Show" tab, blue, right edge
            tab_width = 45
            tab_height = 80
            tab_x1 = width - tab_width - 10
            tab_x2 = width - 10
            # Position below VOR show tab if VOR panel is hidden
            vor_tab_bottom = margin + 80 + 15 if not getattr(self, 'vor_output_visible', True) else vor_panel_bottom
            tab_y1 = vor_tab_bottom
            tab_y2 = vor_tab_bottom + tab_height
            
            self.instruction_show_tab = self.canvas.create_rectangle(
                tab_x1, tab_y1, tab_x2, tab_y2, fill="#e6f3ff", outline="#4169e1"
            )
            show_text = self.canvas.create_text(
                tab_x1 + tab_width // 2, tab_y1 + tab_height // 2,
                text="Help", angle=90, font=("Arial", 10, "bold"), fill="#4169e1"
            )
            self.instruction_panel_items = [self.instruction_show_tab, show_text]
            self.instruction_show_area = (tab_x1, tab_y1, tab_x2, tab_y2)


    def create_indicators(self):
        """Create all circular indicators with the same size."""
        # Create all indicator widgets (heading, CDI, OBS)
        self.create_heading_indicator()
        self.create_cdi_indicator()
        self.create_obs_indicator()

        #self.indicator_radius = 80
        self.create_heading_indicator()
        self.create_cdi_indicator()
        self.create_obs_indicator()

    def create_heading_indicator(self):
        xs, y = self.get_indicator_positions()
        x = xs[0]
        radius = self.indicator_radius

        # Outer circles
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="white", outline="black", width=3)
        self.canvas.create_oval(x - radius + radius*0.125, y - radius + radius*0.125, x + radius - radius*0.125, y + radius - radius*0.125, fill="#f8f8f8", outline="gray", width=1)

        # Compass rose (tick marks and text, rotates with heading)
        self.compass_rose_elements = []
        self.create_compass_rose_markings(x, y, radius, 0)

        # Heading needle (always points up)
        self.hdg_needle = self.canvas.create_line(x, y, x, y - radius * 0.62, fill="red", width=3, arrow=tk.LAST)
        # Center dot
        self.canvas.create_oval(x - radius*0.025, y - radius*0.025, x + radius*0.025, y + radius*0.025, fill="black")
        # Yellow triangle at the top
        self.canvas.create_polygon(
            x - radius*0.035, y - radius + radius*0.035,
            x + radius*0.035, y - radius + radius*0.035,
            x, y - radius - radius*0.035,
            fill="yellow", outline="black", width=1
        )
        # Label
        self.canvas.create_text(x, y + radius + 0.22 * radius, text="HDG Indicator", font=("Arial", int(radius * 0.15), "bold"), fill="darkblue")




    def create_compass_rose_markings(self, x, y, radius, rotation_offset):
        """Create or update compass rose markings with rotation offset."""
        # Clear existing compass rose elements
        for element in self.compass_rose_elements:
            self.canvas.delete(element)
        self.compass_rose_elements.clear()
        
        # Create tick marks and labels that rotate with the compass rose
        for angle in range(0, 360, 30):
            # Apply rotation offset to make compass rose rotate opposite to aircraft heading
            display_angle = (angle - rotation_offset) % 360
            angle_rad = radians(display_angle)
            
            inner_radius = radius - 20
            outer_radius = radius - 10
            start_x = x + inner_radius * sin(angle_rad)
            start_y = y - inner_radius * cos(angle_rad)
            end_x = x + outer_radius * sin(angle_rad)
            end_y = y - outer_radius * cos(angle_rad)
            
            # Create tick mark
            tick = self.canvas.create_line(start_x, start_y, end_x, end_y, width=2)
            self.compass_rose_elements.append(tick)
            
            # Create cardinal direction labels
            if angle % 90 == 0:
                text_x = x + (radius - 30) * sin(angle_rad)
                text_y = y - (radius - 30) * cos(angle_rad)
                heading_text = ["N", "E", "S", "W"][angle // 90]
                label = self.canvas.create_text(text_x, text_y, text=heading_text, 
                                              font=("Arial", 14, "bold"))
                self.compass_rose_elements.append(label)
            
            # Create degree markings for major headings
            elif angle % 30 == 0:
                text_x = x + (radius - 25) * sin(angle_rad)
                text_y = y - (radius - 25) * cos(angle_rad)
                degree_text = str(angle).zfill(3)
                degree_label = self.canvas.create_text(text_x, text_y, text=degree_text, 
                                                     font=("Arial", 8, "bold"))
                self.compass_rose_elements.append(degree_label)

    def create_cdi_indicator(self):
        xs, y = self.get_indicator_positions()
        x = xs[1]
        radius = self.indicator_radius

        # Main circles
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="black", outline="white", width=3)
        self.canvas.create_oval(x - radius + radius*0.125, y - radius + radius*0.125, x + radius - radius*0.125, y + radius - radius*0.125, fill="#1a1a1a", outline="gray", width=1)

        # Vertical and horizontal lines
        self.canvas.create_line(x, y - radius * 0.75, x, y + radius * 0.75, fill="white", width=2)
        self.canvas.create_line(x - radius * 0.75, y, x + radius * 0.75, y, fill="white", width=2)

        # Dots (deviation marks)
        for i in range(-2, 3):
            if i != 0:
                dot_x = x + i * (radius * 0.31)
                self.canvas.create_oval(dot_x - radius*0.05, y - radius*0.05, dot_x + radius*0.05, y + radius*0.05, fill="white", outline="white")

        # CDI needle (vertical line)
        max_dev = radius * 0.62
        self.cdi_needle = self.canvas.create_line(x, y - max_dev, x, y + max_dev, fill="yellow", width=5)

        # TO/FROM triangle indicator (position will be updated in update_cdi_indicator)
        self.to_from_indicator = self.canvas.create_polygon(
            x - radius*0.13, y - 0.8 * radius, x + radius*0.13, y - 0.8 * radius, x, y - 0.56 * radius,
            fill="white", outline="white"
        )

        # Center dot
        self.canvas.create_oval(x - radius*0.037, y - radius*0.037, x + radius*0.037, y + radius*0.037, fill="yellow")
        # Label
        self.canvas.create_text(x, y + radius + 0.22 * radius, text="HSI Indicator", font=("Arial", int(radius * 0.15), "bold"), fill="darkblue")




    def create_obs_indicator(self):
        xs, y = self.get_indicator_positions()
        x = xs[2]
        radius = self.indicator_radius

        # Main black face with white border
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="black", outline="white", width=3)
        self.canvas.create_oval(x - radius + radius*0.06, y - radius + radius*0.06, x + radius - radius*0.06, y + radius - radius*0.06, fill="black", outline="gray", width=1)

        # Compass rose (tick marks and numbers), rotates with OBS
        self.obs_rose_elements = []
        self.create_obs_rose_markings(x, y, radius, 0)

        # Curved dotted deviation scale (responsive)
        arc_radius = radius * 0.5
        arc_angle_range = 60
        arc_center_angle = 270
        num_dots = 7
        arc_start_angle = arc_center_angle - arc_angle_range / 2
        arc_end_angle = arc_center_angle + arc_angle_range / 2
        import math
        for i in range(num_dots):
            angle_deg = arc_start_angle + (i / (num_dots - 1)) * (arc_end_angle - arc_start_angle)
            angle_rad = math.radians(angle_deg)
            dot_x = x + arc_radius * math.cos(angle_rad)
            dot_y = y - arc_radius * math.sin(angle_rad)
            self.canvas.create_oval(dot_x - radius*0.025, dot_y - radius*0.025, dot_x + radius*0.025, dot_y + radius*0.025, fill="white", outline="white")

        # Arrow settings (responsive)
        arrow_width = radius * 0.06
        arrow_height = radius * 0.10
        self.obs_center_x = x
        self.obs_center_y = y
        self.obs_arc_radius = arc_radius
        self.obs_arc_center_angle = arc_center_angle
        self.obs_arc_angle_range = arc_angle_range
        self.obs_num_dots = num_dots
        self.obs_arrow_width = arrow_width
        self.obs_arrow_height = arrow_height

        # Initial CDI needle and arrowhead (center to middle of arc)
        mid_angle_rad = math.radians(arc_center_angle)
        tip_x = x + arc_radius * math.cos(mid_angle_rad)
        tip_y = y - arc_radius * math.sin(mid_angle_rad)
        # Draw the CDI needle only in yellow (no extra white line)
        self.obs_cdi_needle = self.canvas.create_line(x, y, tip_x, tip_y, fill="yellow", width=int(radius*0.06))
        perp_angle = mid_angle_rad + math.pi / 2
        left_x = tip_x + arrow_width * math.cos(perp_angle)
        left_y = tip_y - arrow_width * math.sin(perp_angle)
        right_x = tip_x - arrow_width * math.cos(perp_angle)
        right_y = tip_y + arrow_width * math.sin(perp_angle)
        arrow_tip_x = tip_x + arrow_height * math.cos(mid_angle_rad)
        arrow_tip_y = tip_y - arrow_height * math.sin(mid_angle_rad)
        self.obs_cdi_arrow = self.canvas.create_polygon(left_x, left_y, right_x, right_y, arrow_tip_x, arrow_tip_y, fill="yellow", outline="yellow")

        # Center dot and labels (no white line above dot)
        self.canvas.create_oval(x - radius*0.03, y - radius*0.03, x + radius*0.03, y + radius*0.03, fill="white", outline="white")
        self.obs_setting_display = self.canvas.create_text(
            x, y + radius + 0.18 * radius,
            text="000°",
            font=("Arial", int(radius * 0.14), "bold"),
            fill="darkblue",
            state="hidden"  # Hide visually, but keep functional
        )
        self.canvas.create_text(x, y + radius + 0.24 * radius, text="OBS Indicator", font=("Arial", int(radius * 0.13), "bold"), fill="darkblue")

    def create_obs_rose_markings(self, x, y, radius, rotation_offset):
        # Responsive OBS rose: all elements scale and position with the parent
        for element in self.obs_rose_elements:
            self.canvas.delete(element)
        self.obs_rose_elements.clear()
        for angle in range(0, 360, 10):
            display_angle = (angle - rotation_offset) % 360
            angle_rad = radians(display_angle)
            if angle % 30 == 0:
                inner_radius = radius - radius * 0.32
                outer_radius = radius - radius * 0.1
                tick_width = 2
            else:
                inner_radius = radius - radius * 0.21
                outer_radius = radius - radius * 0.1
                tick_width = 1
            start_x = x + inner_radius * sin(angle_rad)
            start_y = y - inner_radius * cos(angle_rad)
            end_x = x + outer_radius * sin(angle_rad)
            end_y = y - outer_radius * cos(angle_rad)
            tick = self.canvas.create_line(start_x, start_y, end_x, end_y, width=tick_width, fill="white")
            self.obs_rose_elements.append(tick)
            if angle % 30 == 0:
                text_radius = radius - radius * 0.41
                text_x = x + text_radius * sin(angle_rad)
                text_y = y - text_radius * cos(angle_rad)
                heading_number = angle
                number_text = "36" if heading_number == 0 else f"{heading_number // 10:02d}"
                number_label = self.canvas.create_text(text_x, text_y, text=number_text, font=("Arial", int(radius*0.13)), fill="white")
                self.obs_rose_elements.append(number_label)
        for cardinal_angle, cardinal_text in [(0, "N"), (90, "E"), (180, "S"), (270, "W")]:
            display_angle = (cardinal_angle - rotation_offset) % 360
            angle_rad = radians(display_angle)
            text_radius = radius - radius * 0.56
            text_x = x + text_radius * sin(angle_rad)
            text_y = y - text_radius * cos(angle_rad)
            cardinal_label = self.canvas.create_text(text_x, text_y, text=cardinal_text, font=("Arial", int(radius*0.11), "bold"), fill="white")
            self.obs_rose_elements.append(cardinal_label)

    def update_heading_indicator(self, hdg):
        # Redraw the compass rose and rotate it based on current heading
        xs, y = self.get_indicator_positions()
        x = xs[0]
        radius = self.indicator_radius
        self.create_compass_rose_markings(x, y, radius, hdg)  # Rotate rose
        # The heading needle (self.hdg_needle) always points up, so nothing more is needed.

    def update_cdi_indicator(self, obs_angle, bearing_to_vor, direction):
        # Move the CDI needle and TO/FROM indicator
        xs, y = self.get_indicator_positions()
        x = xs[1]
        radius = self.indicator_radius
        deflection = calculate_cdi_deflection(obs_angle, bearing_to_vor)
        max_dev = radius * 0.62
        # Map -10...0...+10 to -max_dev...0...+max_dev
        offset = max(-10, min(10, deflection)) / 10.0 * max_dev
        self.canvas.coords(self.cdi_needle, x + offset, y - max_dev, x + offset, y + max_dev)
        # Move the TO/FROM triangle above/below the gauge based on direction
        if direction == "TO":
            tri_y = y - 0.8 * radius
        else:
            tri_y = y + 0.8 * radius
        # Keep the triangle horizontal
        self.canvas.coords(self.to_from_indicator,
                        x - radius*0.13, tri_y,
                        x + radius*0.13, tri_y,
                        x, tri_y + (0.24 * radius if direction == "TO" else -0.24 * radius))


    def update_obs_indicator(self, obs_angle):
        xs, y = self.get_indicator_positions()
        x = xs[2]
        radius = self.indicator_radius
        self.create_obs_rose_markings(x, y, radius, obs_angle)
        self.canvas.itemconfig(self.obs_setting_display, text=f"{int(obs_angle):03d}°")


    def update_obs_cdi_needle(self, obs_angle, bearing_to_vor):
        """Update the CDI needle position in the OBS indicator based on course deviation."""
        import math
        # Calculate course deviation (same as CDI deflection)
        deflection = calculate_cdi_deflection(obs_angle, bearing_to_vor)
        # Map deflection (-10 to +10) to arc angle
        normalized_deflection = deflection / 10.0
        normalized_deflection = max(-1.0, min(1.0, normalized_deflection))
        # Arc parameters
        arc_center_angle = self.obs_arc_center_angle
        arc_angle_range = self.obs_arc_angle_range
        arc_radius = self.obs_arc_radius
        x, y = self.obs_center_x, self.obs_center_y
        # Calculate angle for tip (like a clock hand)
        angle_deg = arc_center_angle - (arc_angle_range/2) + (normalized_deflection + 1) * (arc_angle_range/2)
        angle_rad = math.radians(angle_deg)
        tip_x = x + arc_radius * math.cos(angle_rad)
        tip_y = y - arc_radius * math.sin(angle_rad)
        # Needle always from center to tip
        self.canvas.coords(self.obs_cdi_needle, x, y, tip_x, tip_y)
        # Arrowhead at tip
        arrow_width = self.obs_arrow_width
        arrow_height = self.obs_arrow_height
        perp_angle = angle_rad + math.pi/2
        left_x = tip_x + arrow_width * math.cos(perp_angle)
        left_y = tip_y - arrow_width * math.sin(perp_angle)
        right_x = tip_x - arrow_width * math.cos(perp_angle)
        right_y = tip_y + arrow_width * math.sin(perp_angle)
        arrow_tip_x = tip_x + arrow_height * math.cos(angle_rad)
        arrow_tip_y = tip_y - arrow_height * math.sin(angle_rad)
        self.canvas.coords(self.obs_cdi_arrow,
                          left_x, left_y,
                          right_x, right_y,
                          arrow_tip_x, arrow_tip_y)

    def draw_airplane(self, x, y, angle):
        """Draw the airplane marker at its current position and heading."""
        cx = x * 5
        cy = y * 5

        if self.airplane_marker:
            self.canvas.delete(self.airplane_marker)

        rotated = self.base_airplane_image.rotate(-angle, expand=True)
        self.airplane_img = ImageTk.PhotoImage(rotated)
        self.airplane_marker = self.canvas.create_image(cx, cy, image=self.airplane_img)

    def move_airplane(self, dx, dy):
        """Move the airplane and update its heading."""
        if dx == 0 and dy == 0:
            return

        new_angle = degrees(atan2(dx, -dy)) % 360
        self.airplane_angle = new_angle
        
        self.air_x_val += dx * self.speed
        self.air_y_val += dy * self.speed
        
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.update_vor_output()

    def rotate_obs(self, delta):
        """Rotate the OBS setting."""
        self.obs_angle = (self.obs_angle + delta) % 360

        # Get active VOR coordinates
        if self.active_vor == 1:
            active_x, active_y = self.vor1_x, self.vor1_y
        else:
            active_x, active_y = self.vor2_x, self.vor2_y

        self.draw_radial_line(self.obs_angle, active_x, active_y)
        self.update_vor_output()


    def on_key_press(self, event):
        """Handle key press events for continuous movement and OBS adjustment."""
        self.pressed_keys.add(event.keysym)
        if event.keysym.lower() == "a":
            self.rotate_obs(-5)
        elif event.keysym.lower() == "d":
            self.rotate_obs(5)
        elif event.keysym.lower() == "q":
            self.rotate_obs(-1)  # Fine adjustment
        elif event.keysym.lower() == "e":
            self.rotate_obs(1)   # Fine adjustment
        elif event.keysym.lower() == "r":
            self.reset_simulation()

    def on_key_release(self, event):
        """Handle key release events."""
        self.pressed_keys.discard(event.keysym)

    def on_mouse_click(self, event):
        """Enable mouse control and set center point."""
        self.mouse_control_enabled = True
        self.mouse_center_x = event.x
        self.mouse_center_y = event.y
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        print("Mouse control enabled! Right-click to disable.")

    def disable_mouse_control(self, event):
        """Disable mouse control."""
        self.mouse_control_enabled = False
        print("Mouse control disabled.")

    def on_mouse_motion(self, event):
        """Handle mouse movement for aircraft control."""
        if not self.mouse_control_enabled:
            return
        
        # Calculate movement delta from center point
        dx = (event.x - self.mouse_center_x) * 0.02  # Scale factor for sensitivity
        dy = (event.y - self.mouse_center_y) * 0.02
        
        # Apply movement if significant enough
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            self.move_airplane(dx, dy)

    def get_joystick_input(self):
        """Get joystick input for aircraft movement."""
        if not self.joystick_enabled:
            return 0, 0
        
        try:
            pygame.event.pump()  # Update joystick state
            
            # Get axis values (typically axis 0 = left/right, axis 1 = up/down)
            dx = self.joystick.get_axis(0) if self.joystick.get_numaxes() > 0 else 0
            dy = self.joystick.get_axis(1) if self.joystick.get_numaxes() > 1 else 0
            
            # Apply deadzone to avoid drift
            deadzone = 0.15
            if abs(dx) < deadzone:
                dx = 0
            if abs(dy) < deadzone:
                dy = 0
            
            # Debug output to see if joystick is working
            if dx != 0 or dy != 0:
                print(f"Joystick input: dx={dx:.3f}, dy={dy:.3f}")
            
            return dx, dy
        except Exception as e:
            print(f"Joystick error: {e}")
            self.joystick_enabled = False  # Disable if error occurs
            return 0, 0

    def movement_loop(self):
        """A continuous loop for handling aircraft movement from keyboard, mouse, joystick, and controller bindings."""
        dx = dy = 0

        # Keyboard input (existing functionality)
        if "Left" in self.pressed_keys:
            dx -= 1
        if "Right" in self.pressed_keys:
            dx += 1
        if "Up" in self.pressed_keys:
            dy -= 1
        if "Down" in self.pressed_keys:
            dy += 1

        # Joystick input (if available and no keyboard input)
        if self.joystick_enabled and dx == 0 and dy == 0:
            joy_dx, joy_dy = self.get_joystick_input()
            if joy_dx != 0 or joy_dy != 0:  # Only apply if there's actual joystick input
                dx += joy_dx * 0.8  # Slightly increased sensitivity for better control
                dy += joy_dy * 0.8
                print(f"Moving airplane with joystick: dx={dx:.3f}, dy={dy:.3f}")

        # Controller bindings: poll for button/hat/axis events
        if hasattr(self, 'controller'):
            self.controller.poll()

        # Apply movement if any input detected
        if dx != 0 or dy != 0:
            self.move_airplane(dx, dy)

        self.root.after(50, self.movement_loop)


    def update_vor_output(self):
        try:
            ax = self.air_x_val
            ay = self.air_y_val
            # Convert VOR canvas coords to grid for math
            vx1, vy1 = self.vor1_x / 5, self.vor1_y / 5
            vx2, vy2 = self.vor2_x / 5, self.vor2_y / 5
            obs = self.obs_angle
            hdg = self.airplane_angle % 360

            bearing1 = calculate_bearing(ax, ay, vx1, vy1)
            distance1 = calculate_distance(ax, ay, vx1, vy1)
            bearing2 = calculate_bearing(ax, ay, vx2, vy2)
            distance2 = calculate_distance(ax, ay, vx2, vy2)

            # Use selected VOR for CDI, TO/FROM, etc
            if self.active_vor == 1:
                vx, vy = self.vor1_x, self.vor1_y  # pixel coordinates for drawing
                vx_grid, vy_grid = vx1, vy1        # grid coordinates for calculation
                vor_label = "VOR 1"
            else:
                vx, vy = self.vor2_x, self.vor2_y
                vx_grid, vy_grid = vx2, vy2
                vor_label = "VOR 2"

            bearing_to_vor = calculate_bearing(ax, ay, vx_grid, vy_grid)
            distance = calculate_distance(ax, ay, vx_grid, vy_grid)
            direction = calculate_vor_to_from(obs, bearing_to_vor)
            cdi_deflection = calculate_cdi_deflection(obs, bearing_to_vor)
            radial_from_vor = (bearing_to_vor + 180) % 360

            # *** ROTATE THE TRIANGULAR CONE WITH THE RADIAL/OBS ***
            self.draw_triangular_gradient(obs, vx, vy)

            result = (
                f"Aircraft Grid Position: ({ax:.1f}, {ay:.1f})\n"
                f"Distance to VOR 1: {distance1:.1f} NM  Bearing: {bearing1:.1f}°\n"
                f"Distance to VOR 2: {distance2:.1f} NM  Bearing: {bearing2:.1f}°\n"
                f"[Active: {vor_label}]\n"
                f"Distance: {distance:.1f} NM\n"
                f"Bearing to VOR: {bearing_to_vor:.1f}°\n"
                f"Radial from VOR: {radial_from_vor:.1f}°\n"
                f"OBS Setting: {obs:.1f}°\n"
                f"TO/FROM: {direction}\n"
                f"HSI Deflection: {cdi_deflection:.1f} dots\n"
                f"Current HDG: {hdg:.1f}°"
            )
            if getattr(self, 'vor_output_visible', True) and hasattr(self, 'result_text'):
                self.canvas.itemconfig(self.result_text, text=result)

            self.update_heading_indicator(hdg)
            self.update_cdi_indicator(obs, bearing_to_vor, direction)
            self.update_obs_indicator(obs)
            self.update_obs_cdi_needle(obs, bearing_to_vor)
        except Exception as e:
            if getattr(self, 'vor_output_visible', True) and hasattr(self, 'result_text'):
                self.canvas.itemconfig(self.result_text, text=f"Error: {str(e)}")

    def joy_reset(self):
        self.reset_simulation()

    def joy_rotate_obs_left(self):
        self.rotate_obs(-5)

    def joy_rotate_obs_right(self):
        self.rotate_obs(5)

    def joy_axes(self, axes):
        deadzone = 0.15
        dx = axes[0] if abs(axes[0]) > deadzone else 0
        dy = axes[1] if abs(axes[1]) > deadzone else 0
        if dx != 0 or dy != 0:
            self.move_airplane(dx * 0.8, dy * 0.8)

    def joy_hat(self, hat):
        if hat[0] == -1:
            self.rotate_obs(-1)
        if hat[0] == 1:
            self.rotate_obs(1)



# --- Run ---
if __name__ == "__main__":
    if "--from-landing-form" in sys.argv:
        root = tk.Tk()
        app = VORSimulatorGUI(root)
        root.mainloop()
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Start from Landing Form",
            "Please start the VOR Navigation Simulator using the landing form (landing_form.py).\n\nDo not run this file directly."
        )
        root.destroy()