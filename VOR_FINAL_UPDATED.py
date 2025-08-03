import tkinter as tk
from math import atan2, degrees, sqrt, sin, cos, radians
from PIL import Image, ImageTk, ImageDraw, UnidentifiedImageError
import os

# Try to import pygame for joystick support
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not available. Joystick support disabled. Install pygame with: pip install pygame")

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
        self.root.focus_set()  # Enable keyboard focus

        # Load background image
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "map_bg.png")
            if os.path.exists(image_path):
                self.bg_img = Image.open(image_path).resize((2000, 900))
                self.tk_img = ImageTk.PhotoImage(self.bg_img)
            else:
                self.tk_img = None
        except (FileNotFoundError, UnidentifiedImageError):
            print("Warning: 'map_bg.png' not found. Using blank background.")
            self.tk_img = None

        #self.canvas = tk.Canvas(root, width=1200, height=730, bg="lightblue")
        #self.canvas.pack()

        root.state('zoomed')  # This maximizes the window (works on Windows)
        self.canvas = tk.Canvas(root, bg="lightblue")
        self.canvas.pack(expand=True, fill="both")  # Fill entire window and center content
        if self.tk_img:
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        # Aircraft state
        self.air_x_val = 10
        self.air_y_val = 10
        self.airplane_marker = None
        self.airplane_img = None
        self.airplane_angle = 0
        self.obs_angle = 0
        self.speed = 0.7  # Default speed
        self.show_all_radials = True  # Toggle for showing all radials

        # VOR elements
        self.vor_x = 50 * 5  # VOR at grid position 50,50 (scaled for canvas)
        self.vor_y = 50 * 5
        self.radial_line = None  # Will hold the radial line object
        self.recip_radial_line = None  # Will hold the reciprocal radial line
        self.all_radials = []  # Will hold all radial lines (every 10 degrees)
        self.triangular_gradient = []
        self.radial_labels = []  # Will hold text labels for radials
        self.compass_rose_elements = []  # Will hold compass rose markings for rotation
        self.obs_rose_elements = []  # Will hold OBS rose markings for rotation

        # Initialize joystick support BEFORE control panel
        self.joystick = None
        self.joystick_enabled = False
        if PYGAME_AVAILABLE:
            try:
                pygame.init()
                pygame.joystick.init()
                joystick_count = pygame.joystick.get_count()
                print(f"Detected {joystick_count} joystick(s)")
                
                if joystick_count > 0:
                    self.joystick = pygame.joystick.Joystick(0)
                    self.joystick.init()
                    self.joystick_enabled = True
                    print(f"Joystick detected and initialized: {self.joystick.get_name()}")
                    print(f"Joystick has {self.joystick.get_numaxes()} axes")
                    print(f"Joystick has {self.joystick.get_numbuttons()} buttons")
                else:
                    print("No joystick detected")
            except Exception as e:
                print(f"Joystick initialization failed: {e}")
                self.joystick_enabled = False

        # Create control panel
        self.create_control_panel()

        # Draw VOR station and initial radials
        self.draw_vor_station()
        
        # Create output labels and indicators
        self.create_output_labels()
        self.create_indicators()

        # Load or create airplane image
        self.load_airplane_image()

        # Setup key bindings for continuous movement
        self.pressed_keys = set()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        
        # Mouse/trackpad control variables
        self.mouse_control_enabled = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_center_x = 0
        self.mouse_center_y = 0
        
        # Setup mouse bindings for aircraft control
        self.canvas.bind("<Button-1>", self.on_mouse_click)  # Left click to enable mouse control
        self.canvas.bind("<Button-3>", self.disable_mouse_control)  # Right click to disable
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        
        self.movement_loop()

        # Initial draw and update
        self.draw_airplane(self.air_x_val, self.air_y_val, self.airplane_angle)
        self.update_vor_output()

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
        """Draw labels for major radials."""
        vx, vy = self.vor_x, self.vor_y
        radius = 150  # Distance from VOR for labels
        
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

        def draw_single_cone(base_angle, center_color="red", side_color="green", cone_type="main"):
            """Draw a single triangular cone representing a VOR radial sector"""
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

            # Add flexible cone fill that extends to screen edges for better visualization
            if cone_type == "main":
                # Create a subtle filled triangle for the main cone with full screen coverage
                cone_fill = self.canvas.create_polygon(
                    vx, vy, left_end_x, left_end_y, right_end_x, right_end_y,
                    fill=center_color, stipple="gray25", outline="", tags="triangular_gradient"
                )
                self.triangular_gradient.append(cone_fill)
            else:
                # Create a different pattern for the reciprocal cone with full screen coverage
                cone_fill = self.canvas.create_polygon(
                    vx, vy, left_end_x, left_end_y, right_end_x, right_end_y,
                    fill=center_color, stipple="gray50", outline="", tags="triangular_gradient"
                )
                self.triangular_gradient.append(cone_fill)

            # Store all cone elements for later deletion
            self.triangular_gradient.extend([center_line, left_boundary, right_boundary])

        # Draw main cone (current OBS setting) - represents the selected radial
        draw_single_cone(obs_angle, center_color="red", side_color="green", cone_type="main")

        # Draw reciprocal cone (OBS + 180°) - represents the opposite radial
        # This creates symmetrical functionality for the other side of the VOR
        reciprocal_angle = (obs_angle + 180) % 360
        draw_single_cone(reciprocal_angle, center_color="blue", side_color="green", cone_type="reciprocal")


    
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
        """Creates the text display area for VOR data."""
        self.result_bg = self.canvas.create_rectangle(
            1300, 0, 2200, 130, fill="white", outline="black"
        )
        self.result_text = self.canvas.create_text(
            1490, 10, anchor="ne", text="VOR Simulator Ready",
            font=("Arial", 10, "bold"), fill="black"
        )

    def create_indicators(self):
        """Create all circular indicators with the same size."""
        self.indicator_radius = 80
        self.create_heading_indicator()
        self.create_cdi_indicator()
        self.create_obs_indicator()

    def create_heading_indicator(self):
        """Create the heading indicator (leftmost) with rotating compass rose."""
        x, y = 100, 580
        radius = self.indicator_radius
        
        # Create outer and inner circles (these stay fixed)
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="white", outline="black", width=3)
        self.canvas.create_oval(x-radius+10, y-radius+10, x+radius-10, y+radius-10, fill="#f8f8f8", outline="gray", width=1)
        
        # Store compass rose elements for rotation (these will move)
        self.compass_rose_elements = []
        
        # Create initial compass rose markings
        self.create_compass_rose_markings(x, y, radius, 0)
        
        # Create fixed heading needle (this stays pointing up - aircraft's perspective)
        self.hdg_needle = self.canvas.create_line(x, y, x, y-50, fill="red", width=3, arrow=tk.LAST)
        # Create fixed center dot
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")
        # Create fixed heading reference triangle at top
        self.canvas.create_polygon(x-5, y-radius+5, x+5, y-radius+5, x, y-radius-5, 
                                  fill="yellow", outline="black", width=1)
        
        self.canvas.create_text(x, y+radius+20, text="HDG Indicator", font=("Arial", 12, "bold"), fill="darkblue")

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
        """Create the HSI/CDI indicator (center)."""
        x, y = 300, 580
        radius = self.indicator_radius
        
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="black", outline="white", width=3)
        self.canvas.create_oval(x-radius+10, y-radius+10, x+radius-10, y+radius-10, fill="#1a1a1a", outline="gray", width=1)
        
        self.canvas.create_line(x, y-radius+20, x, y+radius-20, fill="white", width=2)
        self.canvas.create_line(x-radius+20, y, x+radius-20, y, fill="white", width=2)
        
        for i in range(-2, 3):
            if i != 0:
                dot_x = x + i * 25
                self.canvas.create_oval(dot_x-4, y-4, dot_x+4, y+4, fill="white", outline="white")
        
        self.cdi_needle = self.canvas.create_line(x, y-50, x, y+50, fill="yellow", width=5)
        self.to_from_indicator = self.canvas.create_polygon(x-10, y-65, x+10, y-65, x, y-45, fill="white", outline="white")
        
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="yellow")
        self.canvas.create_text(x, y+radius+20, text="HSI Indicator", font=("Arial", 12, "bold"), fill="darkblue")

    def create_obs_indicator(self):
        """Create the OBS indicator (rightmost) based on real VOR instrument design."""
        x, y = 500, 580
        radius = self.indicator_radius
        
        # Create main white face with black border (like real VOR instrument)
        self.canvas.create_oval(x-radius, y-radius, x+radius, y+radius, fill="white", outline="black", width=3)
        self.canvas.create_oval(x-radius+5, y-radius+5, x+radius-5, y+radius-5, fill="white", outline="gray", width=1)
        
        # Store OBS rose elements for rotation
        self.obs_rose_elements = []
        
        # Create initial OBS markings
        self.create_obs_rose_markings(x, y, radius, 0)
        
        # Create OBS arrow that points to bottom (6 o'clock position) - this stays fixed
        # The arrow points down to show the selected OBS setting on the bottom scale
        arrow_start_y = y + 10
        arrow_end_y = y + radius - 15
        self.obs_needle = self.canvas.create_line(x, arrow_start_y, x, arrow_end_y, 
                                                 fill="red", width=4, arrow=tk.LAST, 
                                                 arrowshape=(8, 10, 3))
        
        # Create center dot
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="black")
        
        # Add "OBS" label at the top of the indicator
        self.canvas.create_text(x, y-radius-15, text="OBS", font=("Arial", 10, "bold"), fill="black")
        
        # Add current OBS setting display at bottom
        self.obs_setting_display = self.canvas.create_text(x, y+radius+15, text="000°", 
                                                          font=("Arial", 12, "bold"), fill="darkblue")
        
        self.canvas.create_text(x, y+radius+35, text="OBS Indicator", font=("Arial", 12, "bold"), fill="darkblue")

    def create_obs_rose_markings(self, x, y, radius, rotation_offset):
        """Create or update OBS rose markings with rotation offset."""
        # Clear existing OBS rose elements
        for element in self.obs_rose_elements:
            self.canvas.delete(element)
        self.obs_rose_elements.clear()
        
        # Create tick marks and numbers around the compass rose
        for angle in range(0, 360, 10):
            # Apply rotation offset to make OBS rose rotate
            display_angle = (angle - rotation_offset) % 360
            angle_rad = radians(display_angle)
            
            # Create different tick sizes for different increments
            if angle % 30 == 0:  # Major ticks every 30 degrees
                inner_radius = radius - 25
                outer_radius = radius - 8
                tick_width = 2
            else:  # Minor ticks every 10 degrees
                inner_radius = radius - 18
                outer_radius = radius - 8
                tick_width = 1
            
            start_x = x + inner_radius * sin(angle_rad)
            start_y = y - inner_radius * cos(angle_rad)
            end_x = x + outer_radius * sin(angle_rad)
            end_y = y - outer_radius * cos(angle_rad)
            
            # Create tick mark
            tick = self.canvas.create_line(start_x, start_y, end_x, end_y, 
                                         width=tick_width, fill="black")
            self.obs_rose_elements.append(tick)
            
            # Add numbers every 30 degrees (like real VOR instrument)
            if angle % 30 == 0:
                text_radius = radius - 35
                text_x = x + text_radius * sin(angle_rad)
                text_y = y - text_radius * cos(angle_rad)
                
                # Format numbers like real VOR (0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33)
                if angle == 0:
                    number_text = "36"
                else:
                    number_text = str(angle // 10).zfill(1)
                
                number_label = self.canvas.create_text(text_x, text_y, text=number_text, 
                                                      font=("Arial", 12, "bold"), fill="black")
                self.obs_rose_elements.append(number_label)
        
        # Add cardinal directions at key positions (like real VOR)
        cardinal_positions = [
            (0, "N"), (90, "E"), (180, "S"), (270, "W")
        ]
        
        for cardinal_angle, cardinal_text in cardinal_positions:
            display_angle = (cardinal_angle - rotation_offset) % 360
            angle_rad = radians(display_angle)
            text_radius = radius - 50
            text_x = x + text_radius * sin(angle_rad)
            text_y = y - text_radius * cos(angle_rad)
            
            cardinal_label = self.canvas.create_text(text_x, text_y, text=cardinal_text, 
                                                   font=("Arial", 10, "bold"), fill="black")
            self.obs_rose_elements.append(cardinal_label)

    def update_heading_indicator(self, heading):
        """Update heading indicator by rotating the compass rose, not the needle."""
        x, y = 100, 580
        radius = self.indicator_radius
        
        # Recreate compass rose markings with rotation based on aircraft heading
        # The compass rose rotates opposite to aircraft heading so the needle appears to point to correct heading
        self.create_compass_rose_markings(x, y, radius, heading)
        
        # The needle stays fixed pointing up (representing aircraft's nose direction)
        # No need to update needle position as it represents the aircraft's reference

    def update_cdi_indicator(self, obs_angle, bearing_to_vor, to_from):
        """Update CDI needle and TO/FROM indicator based on VOR data."""
        x, y = 300, 585
        deflection = calculate_cdi_deflection(obs_angle, bearing_to_vor)
        
        # Horizontal movement of the CDI needle
        needle_x = x + (deflection * 5)
        needle_x = max(x - 50, min(x + 50, needle_x))
        self.canvas.coords(self.cdi_needle, needle_x, y - 50, needle_x, y + 50)
        
        # Update TO/FROM indicator
        if to_from == "TO":
            self.canvas.coords(self.to_from_indicator, x - 10, y - 65, x + 10, y - 65, x, y - 45)
            self.canvas.itemconfig(self.to_from_indicator, fill="green")
        else:
            self.canvas.coords(self.to_from_indicator, x - 10, y + 65, x + 10, y + 65, x, y + 45)
            self.canvas.itemconfig(self.to_from_indicator, fill="red")

    def update_obs_indicator(self, obs_angle):
        """Update the OBS indicator by rotating the compass rose, arrow stays fixed pointing down."""
        x, y = 500, 580
        radius = self.indicator_radius
        
        # Rotate the OBS compass rose to show the selected OBS setting
        # The arrow stays fixed pointing down (6 o'clock position)
        self.create_obs_rose_markings(x, y, radius, obs_angle)
        
        # Update the digital display of current OBS setting
        self.canvas.itemconfig(self.obs_setting_display, text=f"{int(obs_angle):03d}°")

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
        """Update all VOR-related displays and indicators."""
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
            
            self.canvas.itemconfig(self.result_text, text=result)
            
            self.update_heading_indicator(hdg)
            self.update_cdi_indicator(obs, bearing_to_vor, direction)
            self.update_obs_indicator(obs)
            
        except Exception as e:
            self.canvas.itemconfig(self.result_text, text=f"Error: {str(e)}")

# --- Run ---
if __name__ == "__main__":
    root = tk.Tk()
    app = VORSimulatorGUI(root)
    root.mainloop()