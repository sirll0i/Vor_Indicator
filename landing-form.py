import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import pygame
import time

pygame.init()
pygame.joystick.init()

class LandingForm:
    def __init__(self, root):
        self.root = root
        self.root.title("VOR Navigation Simulator")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f2f5")
        
        # Set app icon if available
        try:
            self.root.iconbitmap("icon.ico")  # Add an actual icon file if available
        except:
            pass
        
        # Center the window
        self.center_window()
    
        # Button debounce tracking
        self.last_button_press = 0
        
        self.joystick = None
        self.check_joystick_connection()
        
        # Create main frame
        self.main_frame = tk.Frame(root, bg="#f0f2f5")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Show the main menu initially
        self.show_main_menu()
    
    def check_joystick_connection(self):
        """Check for joystick connection and initialize if found."""
        pygame.joystick.quit()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick connected: {self.joystick.get_name()}")
            print(f"Number of buttons: {self.joystick.get_numbuttons()}")
            print(f"Number of axes: {self.joystick.get_numaxes()}")
            self.poll_joystick_active = True
            if not hasattr(self, '_polling_started'):
                self._polling_started = True
                self.poll_joystick()
        else:
            print("No joystick detected. Please connect a controller and restart.")
            # Keep checking for joystick connection
            self.root.after(2000, self.check_joystick_connection)
      
    def poll_joystick(self):
        """Poll the joystick for button presses and right stick for scrolling."""
        if not self.joystick or not self.poll_joystick_active:
            self.root.after(100, self.poll_joystick)  # Keep polling even when inactive
            return
            
        # CODE TO TEST IF INDEX IS SELECTED CORRECTLY - Enable this to debug
        for i in range(self.joystick.get_numbuttons()):
            if self.joystick.get_button(i):
                print(f"Button {i} is pressed")
        try:
            pygame.event.pump()  # Needed to process joystick events
            
            current_time = time.time()
            
            # Debounce - prevent rapid button presses
            if current_time - self.last_button_press < 0.3:  # 300ms debounce
                self.root.after(100, self.poll_joystick)
                return

            # Y button (index 3) - Start Simulator
            if self.joystick.get_button(3):
                print("Y button pressed - Starting Simulator")
                self.last_button_press = current_time
                self.poll_joystick_active = False
                self.launch_simulator()
                return
          
            # A button (index 0) - About Projects
            if self.joystick.get_button(0):
                print("A button pressed - About Projects")
                self.last_button_press = current_time
                self.show_about_us()
                return
            
            # X button (index 2) - Exit
            if self.joystick.get_button(2):
                print("X button pressed - Exit")
                self.last_button_press = current_time
                self.root.destroy()
                return
            
            # B button (index 1) - Back (only works in About section)
            if self.joystick.get_button(1):
                print("B button pressed - Back")
                if hasattr(self, '_in_about_section') and self._in_about_section:
                    self.last_button_press = current_time
                    self._in_about_section = False  # Reset the flag
                    self.show_main_menu()
                    return
            
            # Right joystick (axis 3 = vertical) for scrolling
            if self.joystick.get_numaxes() > 3:
                right_stick_y = self.joystick.get_axis(3)  # Right stick vertical
                if abs(right_stick_y) > 0.3:  # Deadzone
                    self.handle_scroll(right_stick_y)
                                
            self.root.after(100, self.poll_joystick)  # Schedule next poll

        except pygame.error as e:
            print("Joystick error:", e)
            self.root.after(100, self.poll_joystick)  # Continue polling even after errors
    
    def handle_scroll(self, stick_value):
        """Handle scrolling with right joystick in About section."""
        if hasattr(self, '_about_canvas') and self._about_canvas:
            # Get current scroll position
            current_top, current_bottom = self._about_canvas.yview()
            
            # Calculate scroll amount (stick_value is between -1 and 1)
            scroll_amount = stick_value * 0.1  # Adjust sensitivity
            
            # Scroll the canvas
            if scroll_amount > 0:  # Scroll down
                self._about_canvas.yview_moveto(min(1.0, current_top + scroll_amount))
            else:  # Scroll up
                self._about_canvas.yview_moveto(max(0.0, current_top + scroll_amount))
           
  
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def clear_frame(self):
        """Clear all widgets from the main frame."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_main_menu(self):
        """Display the main menu with Start and About Us buttons."""
        self.clear_frame()
        self.poll_joystick_active = True
        self._in_about_section = False  # Track current section
        self._about_canvas = None  # Reset canvas reference
        
        # Ensure joystick polling is active
        if self.joystick and not hasattr(self, '_polling_started'):
            self._polling_started = True
            self.poll_joystick()
        
        # Header with logo
        header_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        # App logo (placeholder)
        logo_label = tk.Label(
            header_frame,
            text="✈️",
            font=("Arial", 48),
            bg="#f0f2f5",
            fg="#3498db"
        )
        logo_label.pack(pady=(0, 10))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="VOR Navigation Simulator",
            font=("Arial", 24, "bold"),
            fg="#2c3e50",
            bg="#f0f2f5"
        )
        title_label.pack(pady=(0, 5))
        
        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Flight Navigation Training System",
            font=("Arial", 14),
            fg="#7f8c8d",
            bg="#f0f2f5"
        )
        subtitle_label.pack(pady=(0, 30))
        
        # Button container
        button_container = tk.Frame(self.main_frame, bg="#f0f2f5")
        button_container.pack(expand=True, fill=tk.BOTH, padx=50)
        
        # Modern buttons with hover effects
        start_button = tk.Button(
            button_container,
            text="Start Simulator",
            font=("Arial", 16),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            padx=30,
            pady=15,
            border=0,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.launch_simulator
        )
        start_button.pack(fill=tk.X, pady=10)
        start_button.bind("<Enter>", lambda e: start_button.config(bg="#2980b9"))
        start_button.bind("<Leave>", lambda e: start_button.config(bg="#3498db"))
        
        about_button = tk.Button(
            button_container,
            text="About Project",
            font=("Arial", 16),
            bg="#2c3e50",
            fg="white",
            activebackground="#34495e",
            padx=30,
            pady=15,
            border=0,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_about_us
        )
        about_button.pack(fill=tk.X, pady=10)
        about_button.bind("<Enter>", lambda e: about_button.config(bg="#34495e"))
        about_button.bind("<Leave>", lambda e: about_button.config(bg="#2c3e50"))
        
        # Footer
        footer_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 10))
        
        footer_label = tk.Label(
            footer_frame,
            text="© 2025 VOR Navigation Simulator | Educational Software",
            font=("Arial", 10),
            fg="#95a5a6",
            bg="#f0f2f5"
        )
        footer_label.pack()
    
    def show_about_us(self):
        """Display the About Us information."""
        self._in_about_section = True  # Track that we're in about section
        self.clear_frame()
        
        # Restart joystick polling if it was stopped
        if not self.poll_joystick_active:
            self.poll_joystick_active = True
            self.poll_joystick()
        
        # Header with back button
        header_frame = tk.Frame(self.main_frame, bg="#f0f2f5")
        header_frame.pack(fill=tk.X, pady=(10, 20))
        
        back_button = tk.Button(
            header_frame,
            text="← Back",
            font=("Arial", 12),
            bg="#95a5a6",
            fg="white",
            activebackground="#7f8c8d",
            padx=15,
            pady=5,
            border=0,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_main_menu
        )
        back_button.pack(side=tk.LEFT, padx=(0, 10))
        back_button.bind("<Enter>", lambda e: back_button.config(bg="#7f8c8d"))
        back_button.bind("<Leave>", lambda e: back_button.config(bg="#95a5a6"))
        
        title_label = tk.Label(
            header_frame,
            text="About This Project",
            font=("Arial", 20, "bold"),
            fg="#2c3e50",
            bg="#f0f2f5"
        )
        title_label.pack(side=tk.LEFT)
        
        # Content container
        content_frame = tk.Frame(self.main_frame, bg="#ffffff", bd=0, highlightthickness=0, relief=tk.FLAT)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Create a canvas and scrollbar
        canvas = tk.Canvas(content_frame, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        
        # Store canvas reference for joystick scrolling
        self._about_canvas = canvas
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add content to the scrollable frame
        content_padding = 30
        content_width = 700
        
        # Project information
        sections = [
            ("THESIS TITLE", "Development of an Interactive VOR Navigation Simulator for Aviation Training"),
            ("PROJECT MEMBERS", "• [Student Name 1] - [Role/Responsibility]\n• [Student Name 2] - [Role/Responsibility]\n• [Student Name 3] - [Role/Responsibility]\n• [Student Name 4] - [Role/Responsibility]"),
            ("SUBMITTED TO", "[Professor/Advisor Name]\n[Department Name]\n[University/Institution Name]"),
            ("DATE SUBMITTED", "[Month Day, Year]"),
            ("PROJECT DESCRIPTION", 
             "This project aims to develop an interactive VOR (VHF Omnidirectional Range) Navigation "
             "Simulator designed for aviation training and education. The simulator provides a "
             "comprehensive learning environment for understanding VOR navigation principles and "
             "techniques used in modern aviation.\n\n"
             "The system features real-time aircraft simulation, interactive navigation instruments, "
             "and educational scenarios to enhance pilot training and aviation education programs.")
        ]
        
        for i, (heading, content) in enumerate(sections):
            # Section container
            section_frame = tk.Frame(
                scrollable_frame, 
                bg="#ffffff", 
                padx=content_padding, 
                pady=15
            )
            section_frame.pack(fill=tk.X, padx=content_padding, pady=(20 if i == 0 else 10))
            
            # Heading
            heading_label = tk.Label(
                section_frame,
                text=heading,
                font=("Arial", 14, "bold"),
                fg="#3498db",
                bg="#ffffff",
                anchor="w"
            )
            heading_label.pack(fill=tk.X, pady=(0, 5))
            
            # Content
            content_label = tk.Label(
                section_frame,
                text=content,
                font=("Arial", 12),
                fg="#2c3e50",
                bg="#ffffff",
                justify=tk.LEFT,
                wraplength=content_width - (content_padding * 2)
            )
            content_label.pack(fill=tk.X, anchor="w")
        
        # Back to main button at bottom
        button_frame = tk.Frame(scrollable_frame, bg="#ffffff", pady=30)
        button_frame.pack(fill=tk.X, padx=content_padding)
        
        main_button = tk.Button(
            button_frame,
            text="Back to Main Menu",
            font=("Arial", 14),
            bg="#2c3e50",
            fg="white",
            activebackground="#34495e",
            padx=30,
            pady=10,
            border=0,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.show_main_menu
        )
        main_button.pack()
        main_button.bind("<Enter>", lambda e: main_button.config(bg="#34495e"))
        main_button.bind("<Leave>", lambda e: main_button.config(bg="#2c3e50"))
    
    def launch_simulator(self):
        """Launch the VOR simulator application."""
        try:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            simulator_path = os.path.join(script_dir, "VOR_FINAL_UPDATED.py")
            
            if os.path.exists(simulator_path):
                # Launch the simulator with a special argument so it knows it was started from the landing form
                subprocess.Popen([sys.executable, simulator_path, "--from-landing-form"])
                # Close the landing form window immediately after launching the simulator
                self.root.destroy()
            else:
                messagebox.showerror(
                    "File Not Found", 
                    f"Could not find VOR_FINAL_UPDATED.py in:\n{script_dir}\n\n"
                    "Please ensure the simulator file is in the same directory as this launcher."
                )
                
        except Exception as e:
            messagebox.showerror(
                "Launch Error", 
                f"Failed to launch the VOR simulator:\n\n{str(e)}"
            )

def main():
    """Main function to run the landing form."""
    root = tk.Tk()
    app = LandingForm(root)
    
    # Make the window non-resizable for a cleaner look
    root.resizable(False, False)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()