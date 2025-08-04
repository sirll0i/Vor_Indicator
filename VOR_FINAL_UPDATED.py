import tkinter as tk
from tkinter import messagebox
from math import atan2, degrees, sqrt, sin, cos, radians
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError
import os
import sys
import subprocess
import webbrowser
import tempfile

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
        self.vor_x = 50 * 5   # grid units scaled for canvas
        self.vor_y = 50 * 5
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

    def on_canvas_click(self, event):
        # Check hide button
        if self.vor_output_visible and hasattr(self, "vor_output_hide_area"):
            x1, y1, x2, y2 = self.vor_output_hide_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.vor_output_visible = False
                self.create_output_labels()
                return
        # Check show tab
        elif not self.vor_output_visible and hasattr(self, "vor_output_show_area"):
            x1, y1, x2, y2 = self.vor_output_show_area
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.vor_output_visible = True
                self.create_output_labels()
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
        self.labels_var = tk.IntVar(value=0)
        tk.Checkbutton(display_frame, text="Show Radial Labels", variable=self.labels_var, 
                      bg="#d0d0d0", command=self.toggle_labels).pack(side=tk.TOP, anchor=tk.W)
        
        # Background Options
        if MATPLOTLIB_AVAILABLE:
            background_frame = tk.Frame(control_frame, bg="#d0d0d0")
            background_frame.pack(side=tk.LEFT, padx=20, pady=5)
            tk.Label(background_frame, text="Background:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
            tk.Button(background_frame, text="Radar Style", command=lambda: self.apply_matplotlib_background('radar'), 
                     bg="#ff9999", font=("Arial", 9), width=12).pack(side=tk.TOP, pady=1)
            tk.Button(background_frame, text="Default Image", command=self.restore_default_background, 
                     bg="#ffff99", font=("Arial", 9), width=12).pack(side=tk.TOP, pady=1)
        
        # Compass Launch Button
        compass_frame = tk.Frame(control_frame, bg="#d0d0d0")
        compass_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(compass_frame, text="Navigation:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        
        # Real-World Map Button
        if FOLIUM_AVAILABLE:
            tk.Button(compass_frame, text="Open Real-World Map", command=self.open_real_world_map, bg="#66ff66", font=("Arial", 10, "bold"), width=18).pack(side=tk.TOP, pady=2)
            tk.Button(compass_frame, text="Load VOR Stations", command=self.show_vor_stations, bg="#66ccff", font=("Arial", 10, "bold"), width=18).pack(side=tk.TOP, pady=2)

        # Control Methods Info
        control_info_frame = tk.Frame(control_frame, bg="#d0d0d0")
        control_info_frame.pack(side=tk.LEFT, padx=20, pady=5)
        tk.Label(control_info_frame, text="Aircraft Controls:", bg="#d0d0d0", font=("Arial", 10, "bold")).pack(side=tk.TOP)
        
        # Create info text
        control_text = "Keyboard: Arrow Keys\n"
        if self.joystick_enabled:
            control_text += f"Joystick: {self.joystick.get_name()}\n"
        else:
            control_text += "Joystick: Not detected\n"
        control_text += "Mouse: Left-click map, then move"
        
        tk.Label(control_info_frame, text=control_text, bg="#d0d0d0", 
                font=("Arial", 8), justify=tk.LEFT).pack(side=tk.TOP, anchor=tk.W)
        
        # Reset Button
        reset_frame = tk.Frame(control_frame, bg="#d0d0d0")
        reset_frame.pack(side=tk.RIGHT, padx=20, pady=5)
        tk.Button(reset_frame, text="Reset Simulation", command=self.reset_simulation, 
                  bg="#ff9090", font=("Arial", 10, "bold"), width=15).pack(side=tk.TOP, pady=5)

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
            
            # Save and open the map
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
            map_path = temp_file.name
            temp_file.close()
            
            m.save(map_path)
            webbrowser.open(f'file://{map_path}')
            print(f"Real-world VOR map opened in browser: {map_path}")
            
        except Exception as e:
            print(f"Error creating real-world map: {e}")

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

    def toggle_labels(self):
        """Toggle display of radial labels."""
        show_labels = bool(self.labels_var.get())
        
        for label in self.radial_labels:
            self.canvas.delete(label)
        self.radial_labels.clear()
        
        if show_labels:
            self.draw_radial_labels()

    def draw_radial_labels(self):
        """Draw labels for major radials (responsive)."""
        # Convert grid units to canvas pixel units
        vx, vy = self.grid_to_canvas(self.vor_x, self.vor_y)
        
        # Use a radius that depends on the current canvas size
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        radius = min(width, height) * 0.08  # Example: 8% of smallest screen dimension

        for angle in range(0, 360, 30):
            label_x = vx + radius * sin(radians(angle))
            label_y = vy - radius * cos(radians(angle))

            radial_text = f"{angle:03d}\u00b0"
            label = self.canvas.create_text(
                label_x, label_y, 
                text=radial_text,
                font=("Arial", 8, "bold"),
                fill="darkblue",
                tags="radial_label"
            )
            self.radial_labels.append(label)

    def create_indicators(self):
        self.create_heading_indicator()
        self.create_cdi_indicator()
        self.create_obs_indicator()
        self.update_all_meters()

    def update_all_meters(self):
        ax = self.air_x_val
        ay = self.air_y_val
        vx, vy = 50, 50
        obs = self.obs_angle
        hdg = self.airplane_angle % 360
        bearing_to_vor = calculate_bearing(ax, ay, vx, vy)
        direction = calculate_vor_to_from(obs, bearing_to_vor)
        self.update_heading_indicator(hdg)
        self.update_cdi_indicator(obs, bearing_to_vor, direction)
        self.update_obs_indicator(obs)
        self.update_obs_cdi_needle(obs, bearing_to_vor)


    def redraw_all(self, event=None):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        self.indicator_radius = max(min(width, height) * 0.1, 60)
        self.canvas.delete("all")
        # Draw the correct background
        if hasattr(self, 'using_matplotlib_bg') and self.using_matplotlib_bg:
            if hasattr(self, 'bg_photo') and self.bg_photo:
                print("Drawing matplotlib background")
                self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo, tags="background")
            else:
                print("Matplotlib background flag set but no bg_photo available")
        elif self.tk_img:
            print("Drawing default background image")
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        else:
            print("No background available")
        self.draw_vor_station()
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.create_output_labels()
        self.create_indicators()
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
        
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.draw_radial_line(self.obs_angle)
        self.update_vor_output()
        self.obs_value_label.config(text=f"{int(self.obs_angle):03d}\u00b0")

    def draw_vor_station(self):
        """Draw VOR station at a fixed position on the map."""
        vx, vy = self.vor_x, self.vor_y
        
        # Clear existing radials
        for radial in self.all_radials:
            self.canvas.delete(radial)
        self.all_radials.clear()
        
        # Draw VOR symbol
        self.canvas.create_oval(vx-15, vy-15, vx+15, vy+15, 
                                fill="blue", outline="darkblue", width=3)
        self.canvas.create_text(vx, vy-25, text="VOR", 
                                font=("Arial", 12, "bold"), fill="darkblue")
        
        # Draw radials if enabled
        if self.show_all_radials:
            for angle in range(0, 360, 10):
                line_width = 2 if angle % 90 == 0 else 1
                dash_pattern = (5, 5) if angle % 30 != 0 else None
                
                end_x = vx + 800 * sin(radians(angle))
                end_y = vy - 800 * cos(radians(angle))
                
                radial = self.canvas.create_line(
                    vx, vy, end_x, end_y, 
                    fill="gray" if angle % 30 != 0 else "darkgray",
                    width=line_width,
                    dash=dash_pattern,
                    tags="background_radial"
                )
                self.all_radials.append(radial)
        
        # Initialize the OBS radial line
        self.draw_radial_line(self.obs_angle)
        
        # Draw labels if enabled
        if self.labels_var.get():
            self.draw_radial_labels()

    def draw_radial_line(self, obs_angle):
        """Draw a radial line from the VOR based on the OBS setting."""
        if self.radial_line:
            self.canvas.delete(self.radial_line)
        if self.recip_radial_line:
            self.canvas.delete(self.recip_radial_line)
        
        vx, vy = self.vor_x, self.vor_y
        
        # Calculate dynamic length based on screen size to ensure lines extend across entire screen
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Use the diagonal distance from VOR to screen corners to ensure full coverage
        max_distance = max(
            sqrt((canvas_width - vx)**2 + (canvas_height - vy)**2),  # Bottom-right corner
            sqrt(vx**2 + vy**2),  # Top-left corner
            sqrt((canvas_width - vx)**2 + vy**2),  # Top-right corner
            sqrt(vx**2 + (canvas_height - vy)**2)  # Bottom-left corner
        )
        
        # Add extra length to ensure complete screen coverage
        length = int(max_distance * 1.2)  # 20% extra for safety margin
        
        angle_rad = radians(obs_angle)
        
        end_x = vx + length * sin(angle_rad)
        end_y = vy - length * cos(angle_rad)
        
        self.radial_line = self.canvas.create_line(
            vx, vy, end_x, end_y,
            fill="Red", width=2, 
            tags="radial_line"
        )
        
        recip_end_x = vx - length * sin(angle_rad)
        recip_end_y = vy + length * cos(angle_rad)
        
        self.recip_radial_line = self.canvas.create_line(
            vx, vy, recip_end_x, recip_end_y,
            fill="Red", width=2, 
            tags="radial_line"
        )
        
        self.obs_value_label.config(text=f"{int(obs_angle):03d}\u00b0")

    def draw_triangular_gradient(self, obs_angle):
        """Draw triangular-shaped gradients to represent the radial cone and its reciprocal."""
        # Clear existing triangular gradient elements
        for item in self.triangular_gradient:
            self.canvas.delete(item)
        self.triangular_gradient.clear()

        vx, vy = self.vor_x, self.vor_y
        
        # Calculate dynamic length based on screen size to ensure cones extend across entire screen
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Use the diagonal distance from VOR to screen corners to ensure full coverage
        max_distance = max(
            sqrt((canvas_width - vx)**2 + (canvas_height - vy)**2),  # Bottom-right corner
            sqrt(vx**2 + vy**2),  # Top-left corner
            sqrt((canvas_width - vx)**2 + vy**2),  # Top-right corner
            sqrt(vx**2 + (canvas_height - vy)**2)  # Bottom-left corner
        )
        
        # Add extra length to ensure complete screen coverage
        length = int(max_distance * 1.2)  # 20% extra for safety margin
        
        spread_angle = 15  # half-width of the cone (15 degrees on each side)


        def draw_single_cone(base_angle, center_color="red", cone_type="main"):
            """Draw a single triangular cone representing a VOR radial sector"""
            side_color = "green"  # Always green for both cones
            center_angle = radians(base_angle)
            left_angle = radians(base_angle - spread_angle)
            right_angle = radians(base_angle + spread_angle)

            # Calculate end points for center line (main radial direction)
            center_end_x = vx + length * sin(center_angle)
            center_end_y = vy - length * cos(center_angle)
            center_line = self.canvas.create_line(vx, vy, center_end_x, center_end_y,
                                                fill=center_color, width=3, tags="triangular_gradient")

            # Calculate end points for left boundary of the cone
            left_end_x = vx + length * sin(left_angle)
            left_end_y = vy - length * cos(left_angle)
            left_boundary = self.canvas.create_line(vx, vy, left_end_x, left_end_y,
                                                    fill=side_color, width=2, tags="triangular_gradient")

            # Calculate end points for right boundary of the cone
            right_end_x = vx + length * sin(right_angle)
            right_end_y = vy - length * cos(right_angle)
            right_boundary = self.canvas.create_line(vx, vy, right_end_x, right_end_y,
                                                    fill=side_color, width=2, tags="triangular_gradient")

            # Draw only the cone outline (no fill), outline color is green
            cone_fill = self.canvas.create_polygon(
                vx, vy, left_end_x, left_end_y, right_end_x, right_end_y,
                fill="", outline=side_color, width=2, tags="triangular_gradient"
            )
            self.triangular_gradient.append(cone_fill)

            # Store all cone elements for later deletion
            self.triangular_gradient.extend([center_line, left_boundary, right_boundary])

        # Draw main cone (current OBS setting) - represents the selected radial
        draw_single_cone(obs_angle, center_color="red", cone_type="main")

        # Draw reciprocal cone (OBS + 180°) - represents the opposite radial
        # This creates symmetrical functionality for the other side of the VOR
        reciprocal_angle = (obs_angle + 180) % 360
        draw_single_cone(reciprocal_angle, center_color="blue", cone_type="reciprocal")

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
        """Loads or creates a bigger airplane image."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            airplane_path = os.path.join(script_dir, "airplane_icon.png")
            if os.path.exists(airplane_path):
                self.base_airplane_image = Image.open(airplane_path).resize((140, 140)).convert("RGBA")
            else:
                self.base_airplane_image = self.create_airplane_image()
        except Exception:
            self.base_airplane_image = self.create_airplane_image()

    def create_airplane_image(self):
        """Creates a bigger airplane icon if the image file is not found."""
        img = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        points = [(50, 20), (40, 60), (50, 70), (60, 80)]
        draw.polygon(points, fill='red', outline='darkred', width=2)
        draw.rectangle([30, 46, 70, 54], fill='red', outline='darkred')
        draw.rectangle([45, 75, 55, 85], fill='red', outline='darkred')
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
        panel_width = int(0.27 * width)
        panel_height = int(0.17 * height)
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


    def create_indicators(self):
        """Create all circular indicators with the same size."""
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
        
        self.draw_radial_line(self.obs_angle)
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
        """A continuous loop for handling aircraft movement from keyboard, mouse, and joystick."""
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

        # Apply movement if any input detected
        if dx != 0 or dy != 0:
            self.move_airplane(dx, dy)

        self.root.after(50, self.movement_loop)

    def update_vor_output(self):
        """Update all VOR-related displays and indicators, including responsive OBS meter."""
        try:
            ax = self.air_x_val
            ay = self.air_y_val
            vx, vy = 50, 50
            obs = self.obs_angle
            hdg = self.airplane_angle % 360

            bearing_to_vor = calculate_bearing(ax, ay, vx, vy)
            distance = calculate_distance(ax, ay, vx, vy)
            direction = calculate_vor_to_from(obs, bearing_to_vor)
            cdi_deflection = calculate_cdi_deflection(obs, bearing_to_vor)

            self.draw_triangular_gradient(obs)

            radial_from_vor = (bearing_to_vor + 180) % 360
            result = (f"Distance: {distance:.1f} NM\n"
                    f"Bearing to VOR: {bearing_to_vor:.1f}\u00b0\n"
                    f"Radial from VOR: {radial_from_vor:.1f}\u00b0\n"
                    f"OBS Setting: {obs:.1f}\u00b0\n"
                    f"TO/FROM: {direction}\n"
                    f"HSI Deflection: {cdi_deflection:.1f} dots\n"
                    f"Current HDG: {hdg:.1f}\u00b0")
            # Only update the text if panel is visible and result_text exists
            if getattr(self, 'vor_output_visible', True) and hasattr(self, 'result_text'):
                self.canvas.itemconfig(self.result_text, text=result)

            self.update_heading_indicator(hdg)
            self.update_cdi_indicator(obs, bearing_to_vor, direction)
            self.update_obs_indicator(obs)
            self.update_obs_cdi_needle(obs, bearing_to_vor)
        except Exception as e:
            # Only update error if panel is visible and result_text exists
            if getattr(self, 'vor_output_visible', True) and hasattr(self, 'result_text'):
                self.canvas.itemconfig(self.result_text, text=f"Error: {str(e)}")


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