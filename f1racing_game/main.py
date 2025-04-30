import pygame
import sys
import os
import math
import random
from track import Track
from car import Car
from menu import MainMenu
from game import Game
import time

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.load_assets()
        
    def load_assets(self):
        """Load all game assets"""
        # Load images
        image_dir = os.path.join(os.path.dirname(__file__), "assets", "images")
        if os.path.exists(image_dir):
            for filename in os.listdir(image_dir):
                if filename.endswith((".png", ".jpg", ".bmp")):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(image_dir, filename)
                    try:
                        self.images[name] = pygame.image.load(path).convert_alpha()
                    except pygame.error:
                        print(f"Could not load image: {path}")
        else:
            # Create the directory if it doesn't exist
            os.makedirs(image_dir, exist_ok=True)
            print(f"Created image directory: {image_dir}")
        
        # Load sounds
        sound_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        if os.path.exists(sound_dir):
            for filename in os.listdir(sound_dir):
                if filename.endswith((".wav", ".mp3", ".ogg")):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(sound_dir, filename)
                    try:
                        self.sounds[name] = pygame.mixer.Sound(path)
                    except pygame.error:
                        print(f"Could not load sound: {path}")
        else:
            # Create the directory if it doesn't exist
            os.makedirs(sound_dir, exist_ok=True)
            print(f"Created sound directory: {sound_dir}")
    
    def get_image(self, name):
        """Get an image by name"""
        return self.images.get(name)
    
    def play_sound(self, name):
        """Play a sound by name"""
        sound = self.sounds.get(name)
        if sound:
            sound.play()

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Create screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racing Game")
        
        # Set up clock
        self.clock = pygame.time.Clock()
        
        # Game state
        self.running = True
        self.paused = False
        
        # Sparkling effect particles
        self.particles = []
        
        # Load car image based on driver selection
        config_path = os.path.join(os.path.dirname(__file__), "config", "car_selection.txt")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                car_image = f.read().strip()
        else:
            car_image = "car.png"  # Default to Max Verstappen's car
        
        # Determine AI car image (opposite of player's choice)
        if car_image == "car.png":
            ai_car_image = "car2.png"
        else:
            ai_car_image = "car.png"
            
        # Load car images
        car_path = os.path.join(os.path.dirname(__file__), "assets", "images", car_image)
        ai_car_path = os.path.join(os.path.dirname(__file__), "assets", "images", ai_car_image)
        
        # Load car image
        car_path = os.path.join(os.path.dirname(__file__), "assets", "images", car_image)
        if os.path.exists(car_path):
            self.car_image = pygame.image.load(car_path).convert_alpha()
        else:
            # Create a default car if image not found
            self.car_image = pygame.Surface((50, 100), pygame.SRCALPHA)
            pygame.draw.rect(self.car_image, (255, 0, 0), (0, 0, 50, 100))
        
        # Rest of your initialization code...
        self.assets = AssetManager()
        
        # Create track
        self.track = Track(self.assets)
        
        # Create car
        # In the Game class __init__ method:
        # Create car - adjusted position to be on the start line
        start_x, start_y = self.track.start_line[0]
        self.car = Car(start_x, start_y + 20, self.assets)  # Adjusted Y position to be on the track
        self.car.angle = 270  # Set angle to 270 degrees to face right
        
        # Create AI car (slightly offset from player)
        self.ai_car = Car(start_x, start_y - 20, self.assets)  # Position AI car above player
        self.ai_car.angle = 270  # Same starting angle
        self.ai_car.image = pygame.image.load(ai_car_path).convert_alpha() if os.path.exists(ai_car_path) else self.car.image
        
        # AI state
        self.ai_current_lap = 1
        self.ai_waypoint_index = 0
        self.ai_difficulty = 0.7  # Medium difficulty (0.0 to 1.0 scale)
        
        # Game state
        self.current_lap = 1
        self.total_laps = 5
        self.race_complete = False
        self.race_time = 0
        self.best_lap_time = float('inf')
        self.current_lap_time = 0
        self.lap_times = []
        
        # Font for UI
        self.font = pygame.font.SysFont(None, 36)
        
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.race_complete:
                        self.running = False
                    else:
                        if self.paused:
                            # If already paused, exit to menu
                            self.running = False
                        else:
                            # If not paused, pause the game
                            self.paused = True
                elif event.key == pygame.K_r:
                    self.reset_race()
                elif event.key == pygame.K_RETURN and self.paused:
                    # Resume game when Enter is pressed in pause menu
                    self.paused = False
    
    def update(self):
        """Update game state"""
        if self.race_complete or self.paused:
            return
            
        # Get pressed keys
        keys = pygame.key.get_pressed()
        
        # Update player car
        self.car.update(keys, self.track)
        
        # Update AI car
        self.update_ai_car()
        
        # Create sparkling effect when DRS is active
        if self.car.drs_active and self.car.speed > 0:
            # Create new particles behind the car
            for _ in range(2):  # Add 2 particles per frame
                # Calculate position behind the car based on car's angle
                angle_rad = math.radians(self.car.angle)
                offset_x = -math.cos(angle_rad) * 30  # 30 pixels behind the car
                offset_y = -math.sin(angle_rad) * 30
                
                # Create particle with random properties
                particle = {
                    'x': self.car.x + offset_x + random.uniform(-10, 10),
                    'y': self.car.y + offset_y + random.uniform(-10, 10),
                    'size': random.uniform(2, 5),
                    'color': (random.randint(200, 255), random.randint(100, 200), 0),  # Yellow-orange
                    'life': random.uniform(0.3, 0.8),  # Seconds
                    'alpha': 255  # Start fully opaque
                }
                self.particles.append(particle)
        
        # Update existing particles
        for particle in self.particles[:]:
            # Decrease life
            particle['life'] -= 1 / FPS
            # Decrease alpha based on remaining life
            particle['alpha'] = int(255 * (particle['life'] / 0.8))
            
            # Remove dead particles
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # Update lap time
        self.current_lap_time += 1 / FPS
        self.race_time += 1 / FPS
        
        # Check if player lap completed
        if self.track.check_lap_completion(self.car):
            # Record lap time
            self.lap_times.append(self.current_lap_time)
            
            # Update best lap time
            if self.current_lap_time < self.best_lap_time:
                self.best_lap_time = self.current_lap_time
            
            # Reset lap timer
            self.current_lap_time = 0
            
            # Increment lap counter
            self.current_lap += 1
            
            # Check if race is complete
            if self.current_lap > self.total_laps:
                self.race_complete = True
        
        # Check if AI lap completed
        if self.track.check_lap_completion(self.ai_car):
            # Increment AI lap counter
            self.ai_current_lap += 1
            
            # Reset AI waypoint index
            self.ai_waypoint_index = 0
    
    def render(self):
        """Render the game"""
        # Draw track
        self.track.render(self.screen)
        
        # Draw particles (behind the car)
        for particle in self.particles:
            # Create a surface for the particle with alpha channel
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            # Draw the particle with its current alpha
            pygame.draw.circle(
                particle_surface, 
                (*particle['color'], particle['alpha']),  # RGBA color
                (particle['size'], particle['size']),  # Center of the surface
                particle['size']  # Radius
            )
            # Draw the particle on the screen
            self.screen.blit(
                particle_surface, 
                (particle['x'] - particle['size'], particle['y'] - particle['size'])
            )
        
        # Draw AI car
        self.ai_car.render(self.screen)
        
        # Draw player car
        self.car.render(self.screen)
        
        # Draw UI
        self.render_ui()
        
        # Draw F1-style speed display
        self.render_speed_ui()
        
        # Draw pause menu if game is paused
        if self.paused:
            self.render_pause_menu()
        
        # Update display
        pygame.display.flip()
    
    def render_pause_menu(self):
        """Render the pause menu"""
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
        self.screen.blit(overlay, (0, 0))
        
        # Create pause menu title
        title_font = pygame.font.SysFont(None, 72)
        title_text = title_font.render("GAME PAUSED", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
        
        # Create menu options
        menu_font = pygame.font.SysFont(None, 48)
        
        # Resume option
        resume_text = menu_font.render("Press ENTER to Resume", True, WHITE)
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(resume_text, resume_rect)
        
        # Restart option
        restart_text = menu_font.render("Press R to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60))
        self.screen.blit(restart_text, restart_rect)
        
        # Quit option
        quit_text = menu_font.render("Press ESC again to Quit", True, WHITE)
        quit_rect = quit_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120))
        self.screen.blit(quit_text, quit_rect)
        
        # Update display
        pygame.display.flip()
    
    def render_ui(self):
        """Render UI elements"""
        # Lap counter
        lap_text = f"Lap: {self.current_lap}/{self.total_laps}"
        lap_surface = self.font.render(lap_text, True, WHITE)
        self.screen.blit(lap_surface, (20, 20))
        
        # Current lap time
        time_text = f"Time: {self.current_lap_time:.2f}"
        time_surface = self.font.render(time_text, True, WHITE)
        self.screen.blit(time_surface, (20, 60))
        
        # Best lap time
        if self.best_lap_time < float('inf'):
            best_text = f"Best: {self.best_lap_time:.2f}"
            best_surface = self.font.render(best_text, True, WHITE)
            self.screen.blit(best_surface, (20, 100))
        
        # DRS status indicator
        drs_color = (0, 255, 0) if self.car.drs_active else (255, 0, 0)
        drs_text = "DRS: ACTIVE" if self.car.drs_active else "DRS: READY" if self.car.drs_cooldown <= 0 else f"DRS: {self.car.drs_cooldown:.1f}s"
        drs_surface = self.font.render(drs_text, True, drs_color)
        self.screen.blit(drs_surface, (20, 140))
        
        # Race complete message
        if self.race_complete:
            complete_text = "Race Complete!"
            complete_surface = self.font.render(complete_text, True, WHITE)
            text_rect = complete_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(complete_surface, text_rect)
            
            time_text = f"Total Time: {self.race_time:.2f}"
            time_surface = self.font.render(time_text, True, WHITE)
            time_rect = time_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(time_surface, time_rect)
            
            restart_text = "Press 'R' to restart"
            restart_surface = self.font.render(restart_text, True, WHITE)
            restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            self.screen.blit(restart_surface, restart_rect)
    
    def render_speed_ui(self):
        """Render F1-style speed display"""
        # Get current speed in km/h (with higher conversion factor for F1-like speeds)
        speed_kmh = int(abs(self.car.speed) * 30)  # Increased multiplier for much higher speeds
        
        # Cap the maximum speed at 325 km/h
        speed_kmh = min(speed_kmh, 325)
        
        # Create speed display background
        ui_width = 200
        ui_height = 100
        ui_x = SCREEN_WIDTH - ui_width - 20
        ui_y = 20
        
        # Draw semi-transparent background
        speed_bg = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)
        speed_bg.fill((0, 0, 0, 180))  # Black with transparency
        self.screen.blit(speed_bg, (ui_x, ui_y))
        
        # Draw border
        pygame.draw.rect(self.screen, (255, 0, 0), (ui_x, ui_y, ui_width, ui_height), 2)
        
        # Draw "SPEED" label
        label_font = pygame.font.SysFont(None, 24)
        label_text = label_font.render("SPEED", True, (255, 0, 0))
        self.screen.blit(label_text, (ui_x + 10, ui_y + 10))
        
        # Draw speed value
        speed_font = pygame.font.SysFont(None, 60)
        speed_text = speed_font.render(f"{speed_kmh}", True, (255, 255, 255))
        speed_rect = speed_text.get_rect(center=(ui_x + ui_width//2, ui_y + ui_height//2 + 10))
        self.screen.blit(speed_text, speed_rect)
        
        # Draw "km/h" label
        unit_font = pygame.font.SysFont(None, 20)
        unit_text = unit_font.render("km/h", True, (200, 200, 200))
        self.screen.blit(unit_text, (ui_x + ui_width - 50, ui_y + ui_height - 25))
        
        # Draw gear indicator if available
        if hasattr(self.car, 'gear'):
            gear_font = pygame.font.SysFont(None, 36)
            gear_text = gear_font.render(f"GEAR: {self.car.gear}", True, (255, 255, 255))
            self.screen.blit(gear_text, (ui_x + 10, ui_y + ui_height + 10))
    
    def reset_race(self):
        """Reset the race"""
        # Reset player car position
        start_x, start_y = self.track.start_line[0]
        self.car.x = start_x
        self.car.y = start_y + 20  # Adjusted Y position to be on the track
        self.car.angle = 270  # Set angle to 270 degrees to face right
        self.car.speed = 0
        self.car.velocity_x = 0
        self.car.velocity_y = 0
        
        # Reset AI car position
        self.ai_car.x = start_x
        self.ai_car.y = start_y - 20  # Position AI car above player
        self.ai_car.angle = 270
        self.ai_car.speed = 0
        self.ai_car.velocity_x = 0
        self.ai_car.velocity_y = 0
        self.ai_waypoint_index = 0
        self.ai_current_lap = 1
        
        # Reset race state
        self.current_lap = 1
        self.race_complete = False
        self.race_time = 0
        self.current_lap_time = 0
        self.lap_times = []
        
        # Reset DRS if needed
        if hasattr(self.car, 'drs_active'):
            self.car.drs_active = False
        if hasattr(self.car, 'drs_cooldown'):
            self.car.drs_cooldown = 0
        
        # Clear particles
        self.particles = []
    
    def update_ai_car(self):
        """Update AI car movement"""
        # Get track waypoints or create them if they don't exist
        if not hasattr(self.track, 'waypoints'):
            # Check what attributes are available on the track
            if hasattr(self.track, 'path'):
                # If track has a path attribute, use it to create waypoints
                self.track.waypoints = self.track.path[::20]  # Take every 20th point as a waypoint
            elif hasattr(self.track, 'inner_boundary') and hasattr(self.track, 'outer_boundary'):
                # If track has boundaries, create waypoints from the middle of the track
                waypoints = []
                # Use the shorter of the two boundaries to avoid index errors
                boundary_length = min(len(self.track.inner_boundary), len(self.track.outer_boundary))
                step = max(1, boundary_length // 50)  # Create about 50 waypoints
                
                for i in range(0, boundary_length, step):
                    # Calculate middle point between inner and outer boundary
                    inner_x, inner_y = self.track.inner_boundary[i]
                    outer_x, outer_y = self.track.outer_boundary[i]
                    mid_x = (inner_x + outer_x) / 2
                    mid_y = (inner_y + outer_y) / 2
                    waypoints.append((mid_x, mid_y))
                
                self.track.waypoints = waypoints
            elif hasattr(self.track, 'center_line'):
                # If track has a center line, use it for waypoints
                self.track.waypoints = self.track.center_line[::10]  # Take every 10th point
            else:
                # Fallback: create a simple oval track as waypoints
                print("Creating default waypoints for AI")
                center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                radius_x, radius_y = SCREEN_WIDTH // 3, SCREEN_HEIGHT // 3
                waypoints = []
                
                for angle in range(0, 360, 10):
                    rad = math.radians(angle)
                    x = center_x + radius_x * math.cos(rad)
                    y = center_y + radius_y * math.sin(rad)
                    waypoints.append((x, y))
                
                self.track.waypoints = waypoints
        
        # Get current target waypoint
        if self.ai_waypoint_index >= len(self.track.waypoints):
            self.ai_waypoint_index = 0
        
        target_x, target_y = self.track.waypoints[self.ai_waypoint_index]
        
        # Calculate direction to waypoint
        dx = target_x - self.ai_car.x
        dy = target_y - self.ai_car.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # If close to waypoint, move to next one
        if distance < 50:
            self.ai_waypoint_index = (self.ai_waypoint_index + 1) % len(self.track.waypoints)
        
        # Calculate target angle
        target_angle = math.degrees(math.atan2(dy, dx))
        
        # Normalize angle to 0-360
        while target_angle < 0:
            target_angle += 360
        
        # Calculate angle difference
        angle_diff = (target_angle - self.ai_car.angle) % 360
        if angle_diff > 180:
            angle_diff -= 360
        
        # Steer towards target
        if abs(angle_diff) > 5:
            if angle_diff > 0:
                self.ai_car.angle += min(angle_diff, 3)  # Turn right
            else:
                self.ai_car.angle -= min(abs(angle_diff), 3)  # Turn left
        
        # Normalize angle
        self.ai_car.angle %= 360
        
        # Accelerate/brake based on conditions
        max_speed = 10 * self.ai_difficulty  # Medium difficulty
        
        # Slow down for sharp turns
        if abs(angle_diff) > 30:
            max_speed *= 0.5
        
        # Accelerate or brake
        if self.ai_car.speed < max_speed:
            self.ai_car.speed += 0.1 * self.ai_difficulty
        else:
            self.ai_car.speed -= 0.1
        
        # Add some randomness to make AI less perfect
        self.ai_car.speed += random.uniform(-0.05, 0.05)
        
        # Update AI car position
        angle_rad = math.radians(self.ai_car.angle)
        self.ai_car.velocity_x = math.cos(angle_rad) * self.ai_car.speed
        self.ai_car.velocity_y = math.sin(angle_rad) * self.ai_car.speed
        self.ai_car.x += self.ai_car.velocity_x
        self.ai_car.y += self.ai_car.velocity_y
        
        # Check collision with track boundaries - safely check if method exists
        collision_detected = False
        
        if hasattr(self.track, 'is_on_track'):
            if not self.track.is_on_track(self.ai_car.x, self.ai_car.y):
                collision_detected = True
        elif hasattr(self.track, 'check_collision'):
            # Check the signature of check_collision method
            import inspect
            sig = inspect.signature(self.track.check_collision)
            param_count = len(sig.parameters)
            
            if param_count == 3:  # Including self
                # Method expects x, y coordinates
                if self.track.check_collision(self.ai_car.x, self.ai_car.y):
                    collision_detected = True
            else:
                # Method might expect a car object or different parameters
                # Try passing just the AI car
                if self.track.check_collision(self.ai_car):
                    collision_detected = True
        else:
            # No collision detection available, implement a simple boundary check
            # Keep AI car within screen bounds
            margin = 50
            if (self.ai_car.x < margin or self.ai_car.x > SCREEN_WIDTH - margin or 
                self.ai_car.y < margin or self.ai_car.y > SCREEN_HEIGHT - margin):
                collision_detected = True
        
        # Handle collision response
        if collision_detected:
            # Track how long the AI has been stuck
            if not hasattr(self.ai_car, 'stuck_time'):
                self.ai_car.stuck_time = 0
                self.ai_car.stuck_attempts = 0
                self.ai_car.last_good_position = (self.ai_car.x, self.ai_car.y)
                self.ai_car.last_good_angle = self.ai_car.angle
            
            # First try backing up
            self.ai_car.x -= self.ai_car.velocity_x * 2
            self.ai_car.y -= self.ai_car.velocity_y * 2
            self.ai_car.speed *= 0.3
            
            # Increment stuck time
            self.ai_car.stuck_time += 1/FPS
            
            # Special handling for beginning of race (first lap and near start line)
            start_x, start_y = self.track.start_line[0]
            distance_to_start = math.sqrt((self.ai_car.x - start_x)**2 + (self.ai_car.y - start_y)**2)
            
            if self.ai_current_lap == 1 and distance_to_start < 200:
                # If stuck at the beginning of the race, respawn next to player car
                # Position AI car at the same line as player car but with a small horizontal offset
                offset_x = 20  # Smaller horizontal offset from player car
                
                # Match player car's position and angle exactly
                self.ai_car.x = self.car.x + offset_x
                self.ai_car.y = self.car.y  # Same vertical position as player
                self.ai_car.angle = 270  # Face right (270 degrees is downward in pygame)
                
                # Set initial speed slightly higher than player to prevent immediate stalling
                self.ai_car.speed = max(self.car.speed * 0.9, 3)  # Ensure minimum speed
                angle_rad = math.radians(self.ai_car.angle)
                self.ai_car.velocity_x = math.cos(angle_rad) * self.ai_car.speed
                self.ai_car.velocity_y = math.sin(angle_rad) * self.ai_car.speed
                
                # Reset stuck counters
                self.ai_car.stuck_time = 0
                self.ai_car.stuck_attempts = 0
                print("AI car respawned beside player car")
                return
            
            # If stuck for more than 1 second, try more aggressive recovery
            if self.ai_car.stuck_time > 1:
                self.ai_car.stuck_attempts += 1
                
                # More intelligent recovery strategies based on number of attempts
                if self.ai_car.stuck_attempts % 4 == 0:
                    # Reverse direction with increasing speed based on attempts
                    reverse_speed = min(3 + (self.ai_car.stuck_attempts // 4), 6)
                    self.ai_car.angle = (self.ai_car.angle + 180) % 360
                    self.ai_car.speed = -reverse_speed  # Reverse at increasing speed
                    print(f"AI attempting reverse maneuver at speed {reverse_speed}")
                elif self.ai_car.stuck_attempts % 4 == 1:
                    # Turn right and try to get out with increasing angle
                    turn_angle = min(45 + (self.ai_car.stuck_attempts // 4) * 5, 90)
                    self.ai_car.angle = (self.ai_car.angle + turn_angle) % 360
                    self.ai_car.speed = 2.5
                    print(f"AI attempting right turn at {turn_angle} degrees")
                elif self.ai_car.stuck_attempts % 4 == 2:
                    # Turn left and try to get out with increasing angle
                    turn_angle = min(45 + (self.ai_car.stuck_attempts // 4) * 5, 90)
                    self.ai_car.angle = (self.ai_car.angle - turn_angle) % 360
                    self.ai_car.speed = 2.5
                    print(f"AI attempting left turn at {turn_angle} degrees")
                else:
                    # Try to find open space by looking at waypoints
                    # Find nearest waypoint
                    min_dist = float('inf')
                    nearest_wp_idx = 0
                    
                    for i, (wp_x, wp_y) in enumerate(self.track.waypoints):
                        dist = math.sqrt((wp_x - self.ai_car.x)**2 + (wp_y - self.ai_car.y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_wp_idx = i
                    
                    # Get direction to nearest waypoint
                    wp_x, wp_y = self.track.waypoints[nearest_wp_idx]
                    dx = wp_x - self.ai_car.x
                    dy = wp_y - self.ai_car.y
                    escape_angle = math.degrees(math.atan2(dy, dx))
                    
                    # Set angle toward waypoint and apply burst of speed
                    self.ai_car.angle = escape_angle
                    self.ai_car.speed = 3.5
                    print(f"AI attempting to escape toward waypoint at angle {escape_angle:.1f}")
                
                # Apply a small random adjustment to avoid repetitive behavior
                self.ai_car.angle += random.uniform(-5, 5)
                
                # Update velocity based on new angle
                angle_rad = math.radians(self.ai_car.angle)
                self.ai_car.velocity_x = math.cos(angle_rad) * self.ai_car.speed
                self.ai_car.velocity_y = math.sin(angle_rad) * self.ai_car.speed
                
                # Reset stuck time for next attempt but keep track of total stuck duration
                if not hasattr(self.ai_car, 'total_stuck_time'):
                    self.ai_car.total_stuck_time = 0
                self.ai_car.total_stuck_time += self.ai_car.stuck_time
                self.ai_car.stuck_time = 0
                
                # If we've tried too many times (15 attempts = ~5 seconds of being stuck)
                # and we're not in the first lap, find the nearest waypoint and teleport there
                if self.ai_car.stuck_attempts > 15 and self.ai_current_lap > 1:
                    # Find the nearest waypoint
                    min_dist = float('inf')
                    nearest_wp_idx = 0
                    
                    for i, (wp_x, wp_y) in enumerate(self.track.waypoints):
                        dist = math.sqrt((wp_x - self.ai_car.x)**2 + (wp_y - self.ai_car.y)**2)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_wp_idx = i
                    
                    # Get the next few waypoints to determine direction
                    next_wp_idx = (nearest_wp_idx + 1) % len(self.track.waypoints)
                    next_wp_x, next_wp_y = self.track.waypoints[next_wp_idx]
                    
                    # Calculate angle to next waypoint
                    dx = next_wp_x - self.track.waypoints[nearest_wp_idx][0]
                    dy = next_wp_y - self.track.waypoints[nearest_wp_idx][1]
                    target_angle = math.degrees(math.atan2(dy, dx))
                    
                    # Teleport to nearest waypoint
                    self.ai_car.x = self.track.waypoints[nearest_wp_idx][0]
                    self.ai_car.y = self.track.waypoints[nearest_wp_idx][1]
                    self.ai_car.angle = target_angle
                    self.ai_car.speed = 5  # Moderate speed
                    
                    # Reset stuck counters
                    self.ai_car.stuck_time = 0
                    self.ai_car.stuck_attempts = 0
                    
                    print("AI car recovered to nearest waypoint")
        else:
            # Not colliding, reset stuck counters and store good position
            if hasattr(self.ai_car, 'stuck_time'):
                self.ai_car.stuck_time = 0
                self.ai_car.stuck_attempts = 0
            
            # Store last good position every second for potential recovery
            if not hasattr(self.ai_car, 'last_pos_update') or time.time() - self.ai_car.last_pos_update > 1:
                self.ai_car.last_good_position = (self.ai_car.x, self.ai_car.y)
                self.ai_car.last_good_angle = self.ai_car.angle
                self.ai_car.last_pos_update = time.time()

class SplashScreen:
    def __init__(self, screen):
        self.screen = screen
        self.finished = False
        self.start_time = time.time()
        
        # Try to load and play intro video
        self.video_path = os.path.join(os.path.dirname(__file__), "assets", "videos", "intro.mp4")
        self.load_video()
    
    def load_video(self):
        """Load and prepare video for playback"""
        # Initialize video variables
        self.movie = None
        self.cap = None
        self.cv2 = None
        self.current_frame = None
        self.frame_rect = None
        self.last_frame_time = 0
        self.frame_time = 1/30  # Assume 30 FPS
        self.has_audio = False
        
        # Try to use pygame.movie if available (for hardware acceleration)
        try:
            import pygame_ce.movie
            self.movie = pygame_ce.movie.Movie(self.video_path)
            self.movie_screen = pygame.Surface(self.movie.get_size()).convert()
            self.movie.set_display(self.movie_screen)
            self.movie.play()
            print("Using pygame movie for video playback")
            return
        except (ImportError, AttributeError, pygame.error) as e:
            print(f"Pygame movie not available: {e}")
        
        # Fallback to OpenCV for video playback
        try:
            import cv2
            self.cv2 = cv2
            self.cap = cv2.VideoCapture(self.video_path)
            
            if not self.cap.isOpened():
                print(f"Could not open video: {self.video_path}")
                self.create_fallback_splash()
                return
                
            # Get video properties
            self.frame_time = 1 / self.cap.get(cv2.CAP_PROP_FPS)
            self.last_frame_time = time.time()
            
            # Try to extract audio with FFmpeg and play it
            try:
                import subprocess
                audio_path = os.path.join(os.path.dirname(__file__), "assets", "temp_audio.wav")
                
                # Extract audio with FFmpeg
                ffmpeg_cmd = f'ffmpeg -y -i "{self.video_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{audio_path}"'
                print(f"Extracting audio with FFmpeg: {ffmpeg_cmd}")
                subprocess.call(ffmpeg_cmd, shell=True)
                
                # Play audio if extraction was successful
                if os.path.exists(audio_path):
                    print(f"Audio extracted to: {audio_path}")
                    pygame.mixer.music.load(audio_path)
                    pygame.mixer.music.play()
                    self.has_audio = True
                    print("Audio playback started with FFmpeg extraction")
            except Exception as e:
                print(f"Could not extract audio: {e}")
            
            print("Video loaded successfully with OpenCV!")
            return
        except ImportError:
            print("OpenCV not available for video playback")
        
        # If all video methods fail, create a static splash screen
        self.create_fallback_splash()
    
    def create_fallback_splash(self):
        """Create a static splash screen as fallback"""
        # Try to load splash image
        splash_path = os.path.join(os.path.dirname(__file__), "assets", "images", "splash.png")
        if os.path.exists(splash_path):
            try:
                self.splash_image = pygame.image.load(splash_path).convert_alpha()
                # Scale image to fit screen
                img_width, img_height = self.splash_image.get_size()
                scale = min(SCREEN_WIDTH / img_width, SCREEN_HEIGHT / img_height)
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                self.splash_image = pygame.transform.scale(self.splash_image, (new_width, new_height))
                self.image_rect = self.splash_image.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                print(f"Using static splash image: {splash_path}")
                return
            except pygame.error:
                print(f"Could not load splash image: {splash_path}")
        
        # If no image, create a text splash
        font = pygame.font.SysFont(None, 72)
        self.title_text = font.render("Racing Game", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        print("Using text splash screen")
        
        # Set a shorter duration for text splash
        self.duration = 3.0
    
    def update(self):
        """Update splash screen state"""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                # Skip splash on any key press
                self.finished = True
                # Stop audio if playing
                if hasattr(self, 'has_audio') and self.has_audio:
                    pygame.mixer.music.stop()
                # Release video if using OpenCV
                if hasattr(self, 'cap') and self.cap:
                    self.cap.release()
                return
        
        current_time = time.time()
        
        # Handle pygame movie if available
        if hasattr(self, 'movie') and self.movie is not None:
            if not self.movie.get_busy():
                self.finished = True
            return
        
        # Update video frame if needed
        if hasattr(self, 'cap') and hasattr(self, 'cv2') and self.cap is not None:
            # Check if it's time to advance to the next frame
            if current_time - self.last_frame_time > self.frame_time:
                # Read the next frame
                ret, frame = self.cap.read()
                if ret:
                    # Convert frame to pygame surface
                    frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
                    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                    
                    # Scale frame to fit screen
                    frame_width, frame_height = frame.get_size()
                    scale = min(SCREEN_WIDTH / frame_width, SCREEN_HEIGHT / frame_height)
                    new_width = int(frame_width * scale)
                    new_height = int(frame_height * scale)
                    self.current_frame = pygame.transform.scale(frame, (new_width, new_height))
                    self.frame_rect = self.current_frame.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    
                    # Update last frame time
                    self.last_frame_time = current_time
                else:
                    # End of video
                    print("End of video reached")
                    self.cap.release()
                    if hasattr(self, 'has_audio') and self.has_audio:
                        pygame.mixer.music.stop()
                    self.finished = True
        
        # Check if duration has passed for fallback options
        if not hasattr(self, 'cap') and not hasattr(self, 'movie') and current_time - self.start_time > getattr(self, 'duration', 3.0):
            self.finished = True
    
    def render(self):
        """Render the splash screen"""
        self.screen.fill(BLACK)
        
        # Draw current content
        if hasattr(self, 'movie') and hasattr(self, 'movie_screen') and self.movie is not None:
            # Render movie frame
            movie_rect = self.movie_screen.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(self.movie_screen, movie_rect)
        elif hasattr(self, 'current_frame') and hasattr(self, 'frame_rect'):
            self.screen.blit(self.current_frame, self.frame_rect)
        elif hasattr(self, 'splash_image') and hasattr(self, 'image_rect'):
            self.screen.blit(self.splash_image, self.image_rect)
        elif hasattr(self, 'title_text') and hasattr(self, 'title_rect'):
            self.screen.blit(self.title_text, self.title_rect)
        
        # Display "Press any key to skip" text
        font = pygame.font.SysFont(None, 24)
        skip_text = font.render("Press any key to skip", True, WHITE)
        self.screen.blit(skip_text, (SCREEN_WIDTH - skip_text.get_width() - 20, SCREEN_HEIGHT - 30))
        
        pygame.display.flip()

def main():
    """Main game loop"""
    try:
        # Create screen
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Racing Game")
        clock = pygame.time.Clock()
        
        # Show splash screen - only once when the game starts
        splash = SplashScreen(screen)
        while not splash.finished:
            splash.update()
            splash.render()
            clock.tick(FPS)
        
        # Main menu loop - keep returning to menu until exit
        running = True
        while running:
            # Define a change state callback
            def change_state_callback(new_state):
                print(f"Changing state to: {new_state}")
                pass
            
            # Show main menu
            menu = MainMenu(screen, change_state_callback)
            menu_result = menu.run()
            
            # Handle menu result
            if menu_result == "exit":
                running = False
            elif menu_result == "singleplayer":
                # Create game instance
                game = Game()
                
                # Game loop
                while game.running:
                    game.handle_events()
                    game.update()
                    game.render()
                    game.clock.tick(FPS)
    except Exception as e:
        # Print any errors to help with debugging
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        # Keep the window open for a few seconds to see the error
        pygame.time.delay(5000)
    finally:
        # Clean up
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()