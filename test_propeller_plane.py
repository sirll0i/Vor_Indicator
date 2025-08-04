import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import math

AIRPLANE_IMAGE_PATH = "airplane.png"

class AnimatedJetWithPropsDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Jet Silhouette with Animated Propellers")
        self.canvas = tk.Canvas(root, width=600, height=600, bg="black")
        self.canvas.pack()

        # Load and scale airplane image to fit the canvas nicely
        self.base_img = Image.open(AIRPLANE_IMAGE_PATH).convert("RGBA")
        # Optionally, scale to fit canvas (if image is not square)
        self.base_img = self.base_img.resize((400, 400), Image.LANCZOS)
        self.img_w, self.img_h = self.base_img.size

        self.propeller_angle = 0
        self.plane_item = None

        # Estimated positions for propellers on the wings
        # Adjust these if needed for perfect alignment
        self.left_prop_center = (int(self.img_w * 0.32), int(self.img_h * 0.37))
        self.right_prop_center = (int(self.img_w * 0.68), int(self.img_h * 0.37))
        self.prop_radius = int(self.img_w * 0.09)

        self.animate()

    def draw_propeller(self, img, center, angle_deg, color="#cccccc"):
        """Draws a two-blade spinning propeller at the given center."""
        img = img.copy()
        cx, cy = center
        length = self.prop_radius
        width = max(2, int(self.img_w * 0.02))
        draw = ImageDraw.Draw(img)

        # Two blades at 0 and 90 degrees, both rotated by angle
        for blade_angle in [0, 90]:
            theta = math.radians(angle_deg + blade_angle)
            x1 = cx + length * math.cos(theta)
            y1 = cy + length * math.sin(theta)
            x2 = cx - length * math.cos(theta)
            y2 = cy - length * math.sin(theta)
            draw.line([x1, y1, cx, cy, x2, y2], fill=color, width=width)
        # Hub (small light dot)
        hub_r = int(self.img_w * 0.025)
        draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill="#eeeeee", outline=None)
        return img

    def animate(self):
        self.propeller_angle = (self.propeller_angle + 20) % 360

        img = self.base_img.copy()
        img = self.draw_propeller(img, self.left_prop_center, self.propeller_angle)
        img = self.draw_propeller(img, self.right_prop_center, self.propeller_angle)

        tk_img = ImageTk.PhotoImage(img)
        self.tk_img = tk_img  # Prevent garbage collection

        # Center on canvas
        x, y = 300, 300
        if self.plane_item is not None:
            self.canvas.delete(self.plane_item)
        self.plane_item = self.canvas.create_image(x, y, image=self.tk_img, anchor="center")

        self.root.after(50, self.animate)

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimatedJetWithPropsDemo(root)
    root.mainloop()
