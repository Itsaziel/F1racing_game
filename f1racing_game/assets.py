import pygame
import os

class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.fonts = {}
        
    def load_image(self, name, path, scale=None, convert_alpha=True):
        """Load an image and store it in the images dictionary"""
        try:
            full_path = os.path.join("assets", "images", path)
            if convert_alpha:
                image = pygame.image.load(full_path).convert_alpha()
            else:
                image = pygame.image.load(full_path).convert()
                
            if scale:
                image = pygame.transform.scale(image, scale)
                
            self.images[name] = image
            return True
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            # Create a placeholder image
            placeholder = pygame.Surface((50, 50))
            placeholder.fill((255, 0, 255))  # Magenta for missing textures
            self.images[name] = placeholder
            return False
            
    def load_sound(self, name, path):
        """Load a sound and store it in the sounds dictionary"""
        try:
            full_path = os.path.join("assets", "sounds", path)
            sound = pygame.mixer.Sound(full_path)
            self.sounds[name] = sound
            return True
        except Exception as e:
            print(f"Error loading sound {path}: {e}")
            return False
            
    def load_font(self, name, path, size):
        """Load a font and store it in the fonts dictionary"""
        try:
            full_path = os.path.join("assets", "fonts", path)
            font = pygame.font.Font(full_path, size)
            self.fonts[name] = font
            return True
        except Exception as e:
            print(f"Error loading font {path}: {e}")
            # Use default font as fallback
            font = pygame.font.Font(None, size)
            self.fonts[name] = font
            return False
            
    def get_image(self, name):
        """Get an image by name"""
        return self.images.get(name)
        
    def get_sound(self, name):
        """Get a sound by name"""
        return self.sounds.get(name)
        
    def get_font(self, name):
        """Get a font by name"""
        return self.fonts.get(name)
        
    def play_sound(self, name):
        """Play a sound by name"""
        sound = self.get_sound(name)
        if sound:
            sound.play()
            
    def create_default_assets(self):
        """Create default assets when actual files are not available"""
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        # Create car images
        car_player = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.rect(car_player, (255, 0, 0), (0, 0, 40, 20))
        pygame.draw.polygon(car_player, (255, 0, 0), [(40, 0), (40, 20), (50, 10)])
        self.images["car_player"] = car_player
        
        car_opponent = pygame.Surface((40, 20), pygame.SRCALPHA)
        pygame.draw.rect(car_opponent, (0, 0, 255), (0, 0, 40, 20))
        pygame.draw.polygon(car_opponent, (0, 0, 255), [(40, 0), (40, 20), (50, 10)])
        self.images["car_opponent"] = car_opponent
        
        # Create track textures
        track_asphalt = pygame.Surface((100, 100))
        track_asphalt.fill((50, 50, 50))
        for i in range(10):
            for j in range(10):
                if (i + j) % 2 == 0:
                    pygame.draw.rect(track_asphalt, (60, 60, 60), (i*10, j*10, 10, 10))
        self.images["track_asphalt"] = track_asphalt
        
        # Create UI elements
        button_bg = pygame.Surface((200, 50))
        button_bg.fill((0, 0, 0))
        pygame.draw.rect(button_bg, (255, 255, 255), (0, 0, 200, 50), 2)
        self.images["button_bg"] = button_bg
        
        # Create engine sound (empty sound as placeholder)
        try:
            self.sounds["engine"] = pygame.mixer.Sound(buffer=bytes([0]*44100))
            self.sounds["crash"] = pygame.mixer.Sound(buffer=bytes([0]*22050))
            self.sounds["checkpoint"] = pygame.mixer.Sound(buffer=bytes([0]*11025))
        except:
            # If creating sounds with buffer fails, create empty dictionary entries
            self.sounds["engine"] = None
            self.sounds["crash"] = None
            self.sounds["checkpoint"] = None