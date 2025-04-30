import pygame
import math
import os

class Car:
    def __init__(self, x, y, assets=None):
        self.x = x
        self.y = y
        self.angle = 0  # Angle in degrees
        self.speed = 0
        self.max_speed = 8.0
        self.acceleration = 0.1
        self.deceleration = 0.05
        self.turning_speed = 3.0
        self.drift_factor = 0.9  # Higher values = less drift
        
        # Physics properties
        self.velocity_x = 0
        self.velocity_y = 0
        self.angular_velocity = 0
        self.friction = 0.98
        self.drift_threshold = 3.0  # Speed threshold for drifting
        
        # Car dimensions - updated to match sprite size
        self.width = 60
        self.height = 30
        
        # DRS (speed boost) properties
        self.drs_active = False
        self.drs_boost = 4.0  # Increased from 2.0 for more noticeable effect
        self.drs_cooldown = 0
        self.drs_max_duration = 3.0  # DRS lasts for 3 seconds
        self.drs_duration = 0
        
        # Sprite handling
        self.assets = assets
        self.current_sprite = None
        self.sprite_directions = {
            "up": None,
            "down": None,
            "left": None,
            "right": None,
            "up_right": None,
            "up_left": None,
            "down_right": None,
            "down_left": None
        }
        
        # Load sprites if assets are available
        if assets:
            self.load_sprites()
        
        # For skid marks
        self.is_drifting = False
        self.skid_counter = 0
        
    def load_sprites(self):
        """Load car sprites for different directions"""
        # Check for driver selection
        config_path = os.path.join(os.path.dirname(__file__), "config", "car_selection.txt")
        car_image_name = "car"  # Default to Max Verstappen
        
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                selected_car = f.read().strip()
                # Remove .png extension if present
                car_image_name = selected_car.replace(".png", "")
        
        # Try to load the selected car sprite
        base_car = self.assets.get_image(car_image_name)
        
        if base_car:
            # Resize the car image to appropriate dimensions - increased size
            target_width = 120  # Increased from 40
            target_height = 90  # Increased from 20
            base_car = pygame.transform.scale(base_car, (target_width, target_height))
            
            # Store the original sprite
            self.sprite_directions["up"] = base_car
            
            # Create rotated versions for other directions
            self.sprite_directions["down"] = pygame.transform.rotate(base_car, 180)
            self.sprite_directions["left"] = pygame.transform.rotate(base_car, 90)
            self.sprite_directions["right"] = pygame.transform.rotate(base_car, 270)
            self.sprite_directions["up_right"] = pygame.transform.rotate(base_car, 315)
            self.sprite_directions["up_left"] = pygame.transform.rotate(base_car, 45)
            self.sprite_directions["down_right"] = pygame.transform.rotate(base_car, 225)
            self.sprite_directions["down_left"] = pygame.transform.rotate(base_car, 135)
            
            # Set default sprite
            self.current_sprite = self.sprite_directions["up"]
        else:
            print(f"Could not load car image: {car_image_name}")
            # Try to load the default car as fallback
            if car_image_name != "car":
                fallback_car = self.assets.get_image("car")
                if fallback_car:
                    print("Using default car as fallback")
                    # Resize and set up sprites with the fallback car
                    target_width = 120
                    target_height = 90
                    fallback_car = pygame.transform.scale(fallback_car, (target_width, target_height))
                    
                    self.sprite_directions["up"] = fallback_car
                    self.sprite_directions["down"] = pygame.transform.rotate(fallback_car, 180)
                    self.sprite_directions["left"] = pygame.transform.rotate(fallback_car, 90)
                    self.sprite_directions["right"] = pygame.transform.rotate(fallback_car, 270)
                    self.sprite_directions["up_right"] = pygame.transform.rotate(fallback_car, 315)
                    self.sprite_directions["up_left"] = pygame.transform.rotate(fallback_car, 45)
                    self.sprite_directions["down_right"] = pygame.transform.rotate(fallback_car, 225)
                    self.sprite_directions["down_left"] = pygame.transform.rotate(fallback_car, 135)
                    
                    self.current_sprite = self.sprite_directions["up"]
    
    def update(self, keys, track):
        """Update car position and state based on input"""
        # Store previous position for collision detection
        prev_x, prev_y = self.x, self.y
        
        # Handle DRS (speed boost)
        if keys[pygame.K_SPACE] and self.drs_cooldown <= 0:
            self.drs_active = True
            self.drs_duration = 0
        
        # Update DRS status
        if self.drs_active:
            self.drs_duration += 1 / 60  # Assuming 60 FPS
            if self.drs_duration >= self.drs_max_duration:
                self.drs_active = False
                self.drs_cooldown = 5.0  # 5 second cooldown
        
        # Update DRS cooldown
        if self.drs_cooldown > 0:
            self.drs_cooldown -= 1 / 60  # Assuming 60 FPS
        
        # Calculate effective max speed with DRS
        effective_max_speed = self.max_speed + (self.drs_boost if self.drs_active else 0)
        
        # Handle acceleration and steering with more intuitive controls
        if keys[pygame.K_UP]:
            # Accelerate forward in the direction the car is facing
            # Use the effective max speed that includes DRS boost
            self.speed = min(self.speed + self.acceleration, effective_max_speed)
        elif keys[pygame.K_DOWN]:
            # Brake or reverse
            if self.speed > 0:
                # Braking
                self.speed = max(0, self.speed - self.deceleration * 3)  # Faster braking
            else:
                # Reverse
                self.speed = max(self.speed - self.acceleration, -effective_max_speed / 2)
        else:
            # Apply deceleration when no keys are pressed
            if self.speed > 0:
                self.speed = max(0, self.speed - self.deceleration)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.deceleration)
        
        # Handle turning - only turn the wheels when left/right is pressed
        turning_factor = 1.0
        if abs(self.speed) < 0.5:
            # Sharper turning at low speeds
            turning_factor = 2.0
        elif abs(self.speed) > self.max_speed * 0.7:
            # Less responsive turning at high speeds
            turning_factor = 0.7
        
        if keys[pygame.K_LEFT]:
            # Turn wheels left
            self.angle += self.turning_speed * turning_factor
            self.angular_velocity = self.turning_speed
        elif keys[pygame.K_RIGHT]:
            # Turn wheels right
            self.angle -= self.turning_speed * turning_factor
            self.angular_velocity = -self.turning_speed
        else:
            # Wheels return to center position gradually
            self.angular_velocity *= 0.8
        
        # Normalize angle
        self.angle %= 360
        
        # Calculate velocity components based on car's angle
        angle_rad = math.radians(self.angle)
        target_vx = -math.sin(angle_rad) * self.speed
        target_vy = -math.cos(angle_rad) * self.speed
        
        # Apply drift (lerp between current velocity and target velocity)
        drift_factor = self.drift_factor
        if abs(self.speed) > self.drift_threshold and (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]):
            drift_factor = 0.8  # More drift when turning at high speed
            self.is_drifting = True
            self.skid_counter += 1
            
            # Add skid marks every few frames when drifting
            if self.skid_counter % 3 == 0 and track:
                track.add_skid_mark(self.x, self.y)
        else:
            self.is_drifting = False
        
        # Apply drift physics
        self.velocity_x = self.velocity_x * drift_factor + target_vx * (1 - drift_factor)
        self.velocity_y = self.velocity_y * drift_factor + target_vy * (1 - drift_factor)
        
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Update sprite direction based on car's angle instead of keys
        self.update_sprite_direction_by_angle()
        
        # Check for collision with track
        if track and track.check_collision(self):
            # Revert to previous position if collision detected
            self.x, self.y = prev_x, prev_y
            # Reduce speed on collision
            self.speed *= 0.5
            self.velocity_x *= 0.5
            self.velocity_y *= 0.5
    
    def update_sprite_direction(self, keys):
        """Update the current sprite based on movement direction"""
        if not self.assets or not self.sprite_directions["up"]:
            return
            
        # Determine direction based on keys
        if keys[pygame.K_UP] and keys[pygame.K_RIGHT]:
            self.current_sprite = self.sprite_directions["up_right"]
        elif keys[pygame.K_UP] and keys[pygame.K_LEFT]:
            self.current_sprite = self.sprite_directions["up_left"]
        elif keys[pygame.K_DOWN] and keys[pygame.K_RIGHT]:
            self.current_sprite = self.sprite_directions["down_right"]
        elif keys[pygame.K_DOWN] and keys[pygame.K_LEFT]:
            self.current_sprite = self.sprite_directions["down_left"]
        elif keys[pygame.K_UP]:
            self.current_sprite = self.sprite_directions["up"]
        elif keys[pygame.K_DOWN]:
            self.current_sprite = self.sprite_directions["down"]
        elif keys[pygame.K_LEFT]:
            self.current_sprite = self.sprite_directions["left"]
        elif keys[pygame.K_RIGHT]:
            self.current_sprite = self.sprite_directions["right"]
    
    def render(self, surface):
        """Render the car on the given surface"""
        if self.current_sprite:
            # Get the rotated sprite dimensions
            sprite_rect = self.current_sprite.get_rect(center=(self.x, self.y))
            surface.blit(self.current_sprite, sprite_rect)
        else:
            # Fallback to rectangle if no sprite is available
            # Calculate corner points of the rotated rectangle
            angle_rad = math.radians(self.angle)
            cos_angle = math.cos(angle_rad)
            sin_angle = math.sin(angle_rad)
            
            half_width = self.width / 2
            half_height = self.height / 2
            
            # Calculate the four corners of the rotated rectangle
            corners = [
                (self.x + (half_width * cos_angle - half_height * sin_angle),
                 self.y + (half_width * sin_angle + half_height * cos_angle)),
                (self.x + (half_width * cos_angle + half_height * sin_angle),
                 self.y + (half_width * sin_angle - half_height * cos_angle)),
                (self.x + (-half_width * cos_angle + half_height * sin_angle),
                 self.y + (-half_width * sin_angle - half_height * cos_angle)),
                (self.x + (-half_width * cos_angle - half_height * sin_angle),
                 self.y + (-half_width * sin_angle + half_height * cos_angle))
            ]
            
            # Draw the rotated rectangle
            pygame.draw.polygon(surface, (255, 0, 0), corners)
            
            # Draw a direction indicator
            front_x = self.x - math.sin(angle_rad) * half_width
            front_y = self.y - math.cos(angle_rad) * half_width
            pygame.draw.circle(surface, (0, 0, 255), (int(front_x), int(front_y)), 3)

    def update_sprite_direction_by_angle(self):
        """Update the current sprite based on car's angle"""
        if not self.assets or not self.sprite_directions["up"]:
            return
            
        # Normalize angle to 0-360 range
        angle = self.angle % 360
        
        # Select sprite based on angle
        if angle < 22.5 or angle >= 337.5:
            self.current_sprite = self.sprite_directions["up"]
        elif 22.5 <= angle < 67.5:
            self.current_sprite = self.sprite_directions["up_left"]
        elif 67.5 <= angle < 112.5:
            self.current_sprite = self.sprite_directions["left"]
        elif 112.5 <= angle < 157.5:
            self.current_sprite = self.sprite_directions["down_left"]
        elif 157.5 <= angle < 202.5:
            self.current_sprite = self.sprite_directions["down"]
        elif 202.5 <= angle < 247.5:
            self.current_sprite = self.sprite_directions["down_right"]
        elif 247.5 <= angle < 292.5:
            self.current_sprite = self.sprite_directions["right"]
        elif 292.5 <= angle < 337.5:
            self.current_sprite = self.sprite_directions["up_right"]
