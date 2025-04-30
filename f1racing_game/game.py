import pygame
import math
import random
import time
import os  # Add this import
from car import Car
from track import Track
from network import NetworkManager
from assets import AssetManager

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

from neat_manager import NeatManager
from neat_ai_car import NeatAICar

class Game:
    # In the Game class __init__ method:
    def __init__(self, surface, game_mode, return_callback):
        self.surface = surface
        self.game_mode = game_mode
        self.return_callback = return_callback
        self.clock = pygame.time.Clock()
        
        # Load assets
        self.assets = AssetManager()
        self.assets.create_default_assets()
        
        # Try to load custom fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Create track
        self.track = Track(self.assets)
        
        # Create player car
        self.player_car = Car(400, 150, "player", self.assets)
        self.player_car.angle = 90  # Start facing downward
        
        # For multiplayer
        self.opponent_cars = []
        self.network = None
        
        if game_mode == "multi":
            self.setup_multiplayer()
        elif game_mode == "single":
            # Add AI opponent for single player
            self.add_ai_opponent()
            # Initialize NEAT AI
            self.setup_neat_ai()
        
        # Game state - Adding these missing initializations
        self.paused = False
        self.game_over = False
        self.lap_count = 0
        self.max_laps = 3
        self.race_start_time = None
        self.lap_times = []
        self.best_lap_time = None
        self.lap_start_time = None
        
        # Countdown before race starts
        self.countdown = 3
        self.countdown_start = time.time()
        self.race_started = False
        
        # Camera settings for following the player
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.camera_smoothing = 0.1  # Lower values mean smoother camera
    
    def add_ai_opponent(self):
        # Add an AI opponent car
        ai_car = Car(400, 200, "opponent", self.assets)
        ai_car.angle = 90  # Start facing downward
        self.opponent_cars.append(ai_car)
        
    def setup_multiplayer(self):
        # Initialize networking
        self.network = NetworkManager()
        
        # Show dialog to create or join a game
        self.show_multiplayer_dialog()
        
    def show_multiplayer_dialog(self):
        # This would be a UI to create or join a game
        # For now, we'll just create a game
        self.create_game()
        
    def create_game(self):
        # Create a game session
        self.party_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        print(f"Created game with party code: {self.party_code}")
        
        # In a real implementation, this would start a server or peer connection
        
    def join_game(self, party_code):
        # Join an existing game session
        print(f"Joining game with party code: {party_code}")
        
        # In a real implementation, this would connect to a server or peer
        
    # In the setup_neat_ai method:
    def setup_neat_ai(self):
        """Set up the NEAT AI system"""
        # Ensure the data directory exists
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir)
                print(f"Created data directory: {data_dir}")
            except OSError as e:
                print(f"Error creating data directory {data_dir}: {e}")
                return # Stop if we can't create the directory
    
        self.neat_manager = NeatManager(self.track, self.assets)
        best_genome_path = os.path.join(data_dir, "best_genome.pkl")
    
        if os.path.exists(best_genome_path):
            # Load best genome
            start_x, start_y = self.track.start_line[0]
            self.ai_car = self.neat_manager.create_car_from_best_genome(start_x, start_y - 20)
            if self.ai_car: # Check if car creation was successful
                 self.ai_car.angle = 90
                 self.training_mode = False # Explicitly set training mode to False
                 print("Created AI car from best genome. Training mode OFF.")
            else:
                 print("Failed to load best genome, starting training.")
                 self.training_mode = True # Fallback to training if loading failed
                 self.neat_manager.start_simulation()
        else:
            # Start training if no genome exists
            self.training_mode = True # Explicitly set training mode to True
            self.neat_manager.start_simulation()
            print("No best genome found. Starting NEAT training. Training mode ON.")
    
    # In the toggle_training_mode method:
    def toggle_training_mode(self):
        """Toggle between training mode and racing against best AI"""
        print("--- toggle_training_mode called ---") # DEBUG PRINT
        # Add a check to ensure neat_manager exists
        if not hasattr(self, 'neat_manager') or self.neat_manager is None:
            print("Error: NeatManager not initialized. Cannot toggle mode.")
            return
    
        current_mode = self.training_mode
        print(f"Current training_mode: {current_mode}") # DEBUG PRINT
    
        if current_mode:
            print("Attempting to switch OFF training mode...") # DEBUG PRINT
            self.training_mode = False
            # Create a car from the best genome
            start_x, start_y = self.track.start_line[0]
            self.ai_car = self.neat_manager.create_car_from_best_genome(start_x, start_y - 20)
            if self.ai_car: # Check if car creation was successful
                self.ai_car.angle = 90
                print("Successfully created best AI car. Switched to racing against best AI.") # DEBUG PRINT
            else:
                print("Failed to create car from best genome. Reverting to training mode.") # DEBUG PRINT
                self.training_mode = True # Revert if loading failed
        else:
            print("Attempting to switch ON training mode...") # DEBUG PRINT
            self.training_mode = True
            if hasattr(self, 'ai_car') and self.ai_car is not None:
                 print("Deleting existing single AI car.") # DEBUG PRINT
                 del self.ai_car # Use del instead of delattr
                 self.ai_car = None # Ensure it's None
            print("Starting NEAT simulation.") # DEBUG PRINT
            self.neat_manager.start_simulation()
            print("Successfully switched to training mode.") # DEBUG PRINT
    
        print(f"New training_mode: {self.training_mode}") # DEBUG PRINT
        print("--- toggle_training_mode finished ---") # DEBUG PRINT
    
    # Refactored handle_event method:
    def handle_event(self, event):
        # Debug print for all events
        # print(f"Event type: {event.type}") # Optional: Can be noisy
    
        if event.type == pygame.KEYDOWN:
            # print(f"Key pressed: {pygame.key.name(event.key)}") # Optional: Can be noisy
    
            # --- Game Level Keybindings ---
            if event.key == pygame.K_ESCAPE:
                self.paused = not self.paused
                print(f"Paused state toggled: {self.paused}")
            elif event.key == pygame.K_r and (self.paused or self.game_over): # Allow reset only when paused or game over
                print("Resetting game...")
                self.reset_game()
            elif event.key == pygame.K_BACKSPACE and (self.paused or self.game_over): # Allow return only when paused or game over
                 print("Returning to menu...")
                 self.return_callback()
            elif event.key == pygame.K_t: # Use 'T' for toggling
                print("T key pressed - attempting to toggle NEAT training mode")
                self.toggle_training_mode()
    
            # --- Player Car Keybindings (only if race started and not paused/over) ---
            elif self.race_started and not self.paused and not self.game_over:
                 if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE]:
                     self.player_car.handle_event(event)
    
        elif event.type == pygame.KEYUP:
             # Pass keyup events to player car if relevant
             if self.race_started and not self.paused and not self.game_over:
                 if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE]:
                     self.player_car.handle_event(event)
    
    def update(self):
        # Update countdown
        if not self.race_started:
            current_time = time.time()
            elapsed = current_time - self.countdown_start
            self.countdown = 3 - int(elapsed)
    
            if self.countdown <= 0:
                self.race_started = True
                self.race_start_time = current_time
                self.lap_start_time = current_time # Initialize lap timer when race starts
    
        if self.paused or self.game_over or not self.race_started:
            return # Stop updates if paused, game over, or before race starts
    
        # --- Update Game Objects ---
    
        # Update player car
        self.player_car.update()
    
        # Check collisions with track boundaries for player
        if self.track.check_collision(self.player_car):
            self.player_car.handle_collision()
    
        # Check if player completed a lap
        if self.track.check_lap_completion(self.player_car):
            current_time = time.time()
            # Ensure lap_start_time is not None before calculating lap time
            if self.lap_start_time is not None:
                lap_time = current_time - self.lap_start_time
                self.lap_times.append(lap_time)
                print(f"Player Lap {self.lap_count + 1} completed: {lap_time:.2f}s") # Debug Lap Time
    
                # Update best lap time
                if self.best_lap_time is None or lap_time < self.best_lap_time:
                    self.best_lap_time = lap_time
                    print(f"New best lap time: {self.best_lap_time:.2f}s")
    
            self.lap_start_time = current_time # Reset timer for the next lap
            self.lap_count += 1
    
            if self.lap_count >= self.max_laps:
                print("Player finished race!")
                self.game_over = True
    
        # --- Update AI ---
        if self.game_mode == "single":
            # Update the simple AI opponent (if any)
            self.update_ai_opponents() # Update the basic opponent
    
            # Update NEAT AI based on mode
            if hasattr(self, 'neat_manager') and self.neat_manager:
                if self.training_mode:
                    # Update all NEAT cars during training
                    self.neat_manager.update()
                elif hasattr(self, 'ai_car') and self.ai_car:
                    # Update only the single best AI car when not training
                    self.ai_car.update(self.track) # Pass track for collision checks if needed by NeatAICar update
                    # Optional: Check collision for the single AI car
                    if self.track.check_collision(self.ai_car):
                        self.ai_car.handle_collision() # Assuming NeatAICar has this method
    
        # Update opponent cars (for multiplayer - currently unused placeholder)
        # for car in self.opponent_cars:
        #     car.update()
        #     if self.track.check_collision(car):
        #         car.handle_collision()
    
        # Sync multiplayer data if in multiplayer mode (currently unused placeholder)
        # if self.game_mode == "multi" and self.network:
        #     self.sync_multiplayer_data()
            
    def sync_multiplayer_data(self):
        # Send player car data
        car_data = {
            'x': self.player_car.x,
            'y': self.player_car.y,
            'angle': self.player_car.angle,
            'speed': self.player_car.speed
        }
        
        # In a real implementation, this would send data over the network
        # self.network.send_data(car_data)
        
        # Receive opponent car data
        # opponent_data = self.network.receive_data()
        # Update opponent cars with received data
        
    def update_ai_opponents(self):
        # Simple AI logic for opponent cars
        for car in self.opponent_cars:
            # Find the nearest checkpoint
            nearest_checkpoint_idx = 0
            min_distance = float('inf')
            
            # Include start line as a checkpoint for AI navigation
            all_checkpoints = self.track.checkpoints + [self.track.start_line]
            
            for i, checkpoint in enumerate(all_checkpoints):
                # Calculate midpoint of checkpoint
                mid_x = (checkpoint[0][0] + checkpoint[1][0]) / 2
                mid_y = (checkpoint[0][1] + checkpoint[1][1]) / 2
                
                # Calculate distance to checkpoint
                distance = math.sqrt((car.x - mid_x)**2 + (car.y - mid_y)**2)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_checkpoint_idx = i
            
            # Target the next checkpoint
            next_checkpoint_idx = (nearest_checkpoint_idx + 1) % len(all_checkpoints)
            target_checkpoint = all_checkpoints[next_checkpoint_idx]
            
            # Calculate midpoint of target checkpoint
            target_x = (target_checkpoint[0][0] + target_checkpoint[1][0]) / 2
            target_y = (target_checkpoint[0][1] + target_checkpoint[1][1]) / 2
            
            # Calculate angle to target
            target_angle = math.degrees(math.atan2(target_y - car.y, target_x - car.x))
            
            # Normalize angles for comparison
            car_angle_norm = car.angle % 360
            target_angle_norm = target_angle % 360
            
            # Calculate the difference between angles
            angle_diff = (target_angle_norm - car_angle_norm + 180) % 360 - 180
            
            # Steering logic
            if angle_diff > 5:
                car.turning_right = True
                car.turning_left = False
            elif angle_diff < -5:
                car.turning_left = True
                car.turning_right = False
            else:
                car.turning_left = False
                car.turning_right = False
            
            # Acceleration logic
            if abs(angle_diff) < 45:  # Only accelerate if roughly facing the right direction
                car.accelerating = True
                car.braking = False
            else:
                car.accelerating = False
                car.braking = True
            
            # Avoid collisions with player
            player_distance = math.sqrt((car.x - self.player_car.x)**2 + (car.y - self.player_car.y)**2)
            if player_distance < 60:  # If too close to player
                car.braking = True
                car.accelerating = False
    
    def render(self):
        # Clear the screen
        self.surface.fill(BLACK)
        
        # Calculate camera offset to follow player
        target_offset_x = SCREEN_WIDTH // 2 - self.player_car.x
        target_offset_y = SCREEN_HEIGHT // 2 - self.player_car.y
        
        # Smooth camera movement
        self.camera_offset_x += (target_offset_x - self.camera_offset_x) * self.camera_smoothing
        self.camera_offset_y += (target_offset_y - self.camera_offset_y) * self.camera_smoothing
        
        # Create a temporary surface for the game world
        world_surface = pygame.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2))
        
        # Draw track on world surface
        self.track.render(world_surface)
        
        # Draw player car on world surface
        self.player_car.render(world_surface)
        
        # Draw opponent cars on world surface
        for car in self.opponent_cars:
            car.render(world_surface)
        
        # Draw NEAT cars if in training mode
        if hasattr(self, 'training_mode') and self.training_mode:
            self.neat_manager.render(world_surface)
        elif hasattr(self, 'ai_car') and self.ai_car:
            self.ai_car.render(world_surface)
        
        # Draw the visible portion of the world on the screen
        view_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.camera_offset_x - SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2 - self.camera_offset_y - SCREEN_HEIGHT // 2,
            SCREEN_WIDTH,
            SCREEN_HEIGHT
        )
        self.surface.blit(world_surface, (0, 0), view_rect)
        
        # Draw countdown if race hasn't started
        if not self.race_started:
            self.render_countdown()
        
        # Draw UI
        self.render_ui()
        
        # Draw pause or game over screen
        if self.paused:
            self.render_pause_screen()
        elif self.game_over:
            self.render_game_over_screen()
    
    def render_countdown(self):
        # Draw countdown before race starts
        if self.countdown > 0:
            countdown_text = self.font.render(str(self.countdown), True, WHITE)
        else:
            countdown_text = self.font.render("GO!", True, GREEN)
        
        text_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
        # Add a background to make text more visible
        bg_rect = text_rect.copy()
        bg_rect.inflate_ip(20, 20)
        pygame.draw.rect(self.surface, BLACK, bg_rect)
        pygame.draw.rect(self.surface, WHITE, bg_rect, 2)
        
        self.surface.blit(countdown_text, text_rect)
    
    def render_ui(self):
        # Draw speed
        speed_text = self.font.render(f"Speed: {abs(int(self.player_car.speed * 10))} km/h", True, WHITE)
        self.surface.blit(speed_text, (10, 10))
        
        # Draw lap count
        lap_text = self.font.render(f"Lap: {self.lap_count + 1}/{self.max_laps}", True, WHITE)
        self.surface.blit(lap_text, (10, 50))
        
        # Draw lap times
        if len(self.lap_times) > 0:
            y_offset = 90
            self.surface.blit(self.font.render("Lap Times:", True, WHITE), (10, y_offset))
            
            for i, lap_time in enumerate(self.lap_times):
                time_text = self.small_font.render(f"Lap {i+1}: {lap_time:.2f}s", True, WHITE)
                self.surface.blit(time_text, (20, y_offset + 30 + i * 25))
            
            if self.best_lap_time:
                best_text = self.small_font.render(f"Best: {self.best_lap_time:.2f}s", True, GREEN)
                self.surface.blit(best_text, (20, y_offset + 30 + len(self.lap_times) * 25))
        
        # Draw race time
        if self.race_started and not self.game_over:
            race_time = time.time() - self.race_start_time
            time_text = self.font.render(f"Time: {race_time:.2f}s", True, WHITE)
            self.surface.blit(time_text, (SCREEN_WIDTH - 200, 10))
        
        # Draw party code if in multiplayer
        if self.game_mode == "multi" and hasattr(self, 'party_code'):
            code_text = self.font.render(f"Party Code: {self.party_code}", True, WHITE)
            self.surface.blit(code_text, (SCREEN_WIDTH - 250, 50))
            
    def render_pause_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.surface.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.font.render("PAUSED", True, WHITE)
        text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.surface.blit(pause_text, text_rect)
        
        # Instructions
        instructions = self.font.render("Press ESC to resume, BACKSPACE to return to menu", True, WHITE)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.surface.blit(instructions, inst_rect)
        
    def render_game_over_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.surface.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.font.render("RACE COMPLETE!", True, WHITE)
        text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.surface.blit(game_over_text, text_rect)
        
        # Instructions
        instructions = self.font.render("Press R to restart, BACKSPACE to return to menu", True, WHITE)
        inst_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.surface.blit(instructions, inst_rect)
        
    def reset_game(self):
        self.player_car.reset()
        
        # Reset AI opponents
        for car in self.opponent_cars:
            car.reset()
        
        # Reset game state
        self.lap_count = 0
        self.game_over = False
        self.race_started = False
        self.countdown = 3
        self.countdown_start = time.time()
        self.race_start_time = None
        self.lap_times = []
        self.best_lap_time = None
        self.lap_start_time = None