import tkinter as tk
from tkinter import colorchooser
import random
import math
import threading
import time

class Particle:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)

    def move(self, gravity, mouse_x, mouse_y, mouse_push, mouse_distance_threshold):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

        dx = self.x - mouse_x
        dy = self.y - mouse_y
        distance = math.sqrt(dx**2 + dy**2)
        if distance < mouse_distance_threshold:
            force_x = dx / distance * mouse_push
            force_y = dy / distance * mouse_push
            self.vx += force_x
            self.vy += force_y

    def draw(self, canvas):
        x0 = self.x - self.size
        y0 = self.y - self.size
        x1 = self.x + self.size
        y1 = self.y + self.size
        canvas.create_oval(x0, y0, x1, y1, fill=self.color, outline=self.color)

class ParticleSimulator:
    def __init__(self, master):
        self.master = master
        self.master.title("Particle Simulator")

        self.color_cycle_thread = None
        self.stop_color_cycle = threading.Event()

        self.canvas = tk.Canvas(master, width=800, height=600, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.particles = []

        self.color_generator = self.cycle_rgb(50, 50, 50)

        self.gravity = 0.05
        self.particle_size = 5
        self.particle_color = "#FFFFFF"
        self.color_cycle_speed = 0
        self.cycle_colors = False
        self.rainbow_colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
        self.cycle_index = 0

        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_push = 5
        self.mouse_distance_threshold = 50

        self.create_gui()

        self.mouse_down = False
        self.master.bind("<Button-1>", self.on_mouse_down)
        self.master.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.master.bind("<Motion>", self.on_mouse_move)

        self.update()

    def check_and_resolve_collision(self, particle1, particle2):
        dx = particle1.x - particle2.x
        dy = particle1.y - particle2.y
        distance = math.sqrt(dx**2 + dy**2)
        min_dist = particle1.size + particle2.size

        if distance < min_dist and distance != 0:
            # Normalize the distance vector
            nx = dx / distance
            ny = dy / distance

            # Compute relative velocity
            vx = particle1.vx - particle2.vx
            vy = particle1.vy - particle2.vy

            # Compute relative velocity in terms of the normalized direction
            vel_along_normal = vx * nx + vy * ny

            # Do not resolve if velocities are separating
            if vel_along_normal > 0:
                return

            # Calculate restitution (elasticity of the collision)
            restitution = 0.8

            # Calculate impulse scalar
            impulse = -(1 + restitution) * vel_along_normal
            impulse /= (1 / particle1.size + 1 / particle2.size)

            # Apply impulse to the particle velocities
            particle1.vx -= impulse * nx / particle1.size
            particle1.vy -= impulse * ny / particle1.size
            particle2.vx += impulse * nx / particle2.size
            particle2.vy += impulse * ny / particle2.size

    def keep_particle_inside_canvas(self, particle):
        max_speed = 10 
        particle.vx = max(min(particle.vx, max_speed), -max_speed)
        particle.vy = max(min(particle.vy, max_speed), -max_speed)

        if particle.x - particle.size < 0:
            particle.x = particle.size
            particle.vx *= -1
        elif particle.x + particle.size > self.canvas.winfo_width():
            particle.x = self.canvas.winfo_width() - particle.size
            particle.vx *= -1

        if particle.y - particle.size < 0:
            particle.y = particle.size
            particle.vy *= -1
        elif particle.y + particle.size > self.canvas.winfo_height():
            particle.y = self.canvas.winfo_height() - particle.size
            particle.vy *= -1

    def cycle_rgb(self, start, end, step):
        if step == 0:
            raise ValueError("Step cannot be zero in cycle_rgb")

        while True:
            for r in range(start, end, step):
                for g in range(start, end, step):
                    for b in range(start, end, step):
                        yield (r, g, b)
            for r in range(end - step, start - step, -step):
                for g in range(end - step, start - step, -step):
                    for b in range(end - step, start - step, -step):
                        yield (r, g, b)

    def change_background(self):
        color_code = colorchooser.askcolor(title="Choose background color")[1]
        if color_code:
            self.canvas.config(bg=color_code)

    def change_particle_color(self):
        color_code = colorchooser.askcolor(title="Choose particle color")[1]
        if color_code:
            self.particle_color = color_code

    def toggle_color_cycle(self):
        if self.cycle_colors:
            self.cycle_colors = False
            self.stop_color_cycle.set()  # Signal to stop the color cycling thread
        else:
            self.cycle_colors = True
            self.stop_color_cycle.clear()
            self.color_cycle_thread = threading.Thread(target=self.cycle_colors_background)
            self.color_cycle_thread.start()

    def cycle_colors_background(self):
        for r, g, b in self.cycle_rgb(0, 255, 10):
            if self.stop_color_cycle.is_set():
                break
            self.next_color = f'#{r:02x}{g:02x}{b:02x}'
            time.sleep(0.05)

    def update_particle_color_from_thread(self):
        if self.cycle_colors:
            for particle in self.particles:
                particle.color = self.particle_color

    def toggle_fullscreen(self):
        is_fullscreen = self.master.attributes("-fullscreen")
        self.master.attributes("-fullscreen", not is_fullscreen)

    def move_particles(self):
        friction = 0.99  # Value close to 1 for slow deceleration
        for particle in self.particles:
            particle.vx *= friction
            particle.vy *= friction
            particle.move(self.gravity_scale.get(), self.mouse_x, self.mouse_y, self.mouse_push_scale.get(), self.mouse_distance_threshold)

    def is_particle_inside_canvas(self, particle):
        return (0 <= particle.x <= self.canvas.winfo_width() and
                0 <= particle.y <= self.canvas.winfo_height())

    def create_gui(self):
        self.control_frame = tk.Frame(self.master)
        self.control_frame.pack(side="top", fill="x")

        tk.Button(self.control_frame, text="Change Background", command=self.change_background).pack(side="left")

        self.gravity_scale = tk.Scale(self.control_frame, from_=0, to=0.2, resolution=0.01, orient="horizontal", label="Gravity")
        self.gravity_scale.set(self.gravity)
        self.gravity_scale.pack(side="left")

        self.size_scale = tk.Scale(self.control_frame, from_=1, to=20, orient="horizontal", label="Particle Size")
        self.size_scale.set(self.particle_size)
        self.size_scale.pack(side="left")

        tk.Button(self.control_frame, text="Change Particle Color", command=self.change_particle_color).pack(side="left")

        self.color_cycle_check = tk.Checkbutton(self.control_frame, text="Cycle Colors", command=self.toggle_color_cycle)
        self.color_cycle_check.pack(side="left")

        self.color_cycle_speed_scale = tk.Scale(self.control_frame, from_=0, to=10, orient="horizontal", label="Color Cycle Speed")
        self.color_cycle_speed_scale.pack(side="left")

        self.mouse_push_scale = tk.Scale(self.control_frame, from_=0.0, to=20.0, resolution=0.1, orient="horizontal", label="Mouse Push")
        self.mouse_push_scale.set(self.mouse_push)
        self.mouse_push_scale.pack(side="left")

        tk.Button(self.control_frame, text="Clear Particles", command=self.clear_particles).pack(side="left")

        self.fullscreen_check = tk.Checkbutton(self.control_frame, text="Fullscreen", command=self.toggle_fullscreen)
        self.fullscreen_check.pack(side="left")

    def on_mouse_down(self, event):
        self.mouse_down = True
        self.mouse_x = event.x
        self.mouse_y = event.y
        self.spawn_particle_loop()

    def on_mouse_up(self, event):
        self.mouse_down = False

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.mouse_down:
            new_particle = Particle(event.x, event.y, self.size_scale.get(), self.particle_color)
            self.particles.append(new_particle)

    def spawn_particle_loop(self):
        if self.mouse_down:
            new_particle = Particle(self.mouse_x, self.mouse_y, self.size_scale.get(), self.particle_color)
            self.particles.append(new_particle)
            self.master.after(1, self.spawn_particle_loop)

    def update(self):
        self.canvas.delete("all")

        self.update_particle_colors()

        for i, particle in enumerate(self.particles):
            for other in self.particles[i+1:]:
                self.check_and_resolve_collision(particle, other)

            self.keep_particle_inside_canvas(particle)
            particle.move(self.gravity_scale.get(), self.mouse_x, self.mouse_y, self.mouse_push_scale.get(), self.mouse_distance_threshold)
            particle.draw(self.canvas)

        self.particles = [p for p in self.particles if self.is_particle_inside_canvas(p)]

        self.master.after(10, self.update)

    def update_particle_colors(self):
        if self.cycle_colors and hasattr(self, 'next_color'):
            self.particle_color = self.next_color

    def clear_particles(self):
        self.particles.clear()

# Running the simulator
root = tk.Tk()
app = ParticleSimulator(root)
root.mainloop()
