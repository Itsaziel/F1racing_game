import pygame
import os

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

class Button:
    def __init__(self, x, y, width, height, text, font_size=36, color=(200, 200, 200), hover_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont(None, font_size)
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.was_hovered = False  # Track previous hover state
        self.is_clicked = False
        self.is_expanded = False
        self.sub_buttons = []
    
    def add_sub_button(self, text):
        # Create a sub-button below this button
        sub_button_height = 50
        sub_button_y = self.rect.y + len(self.sub_buttons) * sub_button_height + self.rect.height
        sub_button = Button(
            self.rect.x + 20,  # Indented
            sub_button_y,
            self.rect.width - 40,  # Slightly smaller
            sub_button_height,
            text,
            font_size=30,
            color=(180, 180, 180),
            hover_color=(220, 220, 220)
        )
        self.sub_buttons.append(sub_button)
        return sub_button
    
    def update(self, events, sounds=None):
        mouse_pos = pygame.mouse.get_pos()
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        self.is_clicked = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
                self.is_clicked = True
                # Play select sound
                if sounds and sounds["select"]:
                    sounds["select"].play()
                return True
        
        # Update sub-buttons if expanded
        if self.is_expanded:
            for sub_button in self.sub_buttons:
                if sub_button.update(events, sounds):
                    return True
        
        return False
    
    def render(self, screen):
        # Draw button background
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2)  # Border
        
        # Draw button text
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
        # Draw sub-buttons if expanded
        if self.is_expanded:
            for sub_button in self.sub_buttons:
                sub_button.render(screen)

class MainMenu:
    def __init__(self, screen, change_state_callback):
        self.screen = screen
        self.change_state_callback = change_state_callback
        self.running = True
        self.result = None
        self.current_screen = "main"  # Track which screen we're on
        self.selected_driver = "max"  # Default driver
        
        # Load sound effects
        self.sounds = {
            "select": None,
            "back": None
        }
        self.load_sounds()
        
        # Start menu background music
        self.start_background_music()
        
        # Create buttons for main menu
        button_width = 300
        button_height = 60
        button_spacing = 30
        start_y = SCREEN_HEIGHT // 2 - (3 * button_height + 2 * button_spacing) // 2
        
        # Main menu buttons
        self.start_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y,
            button_width,
            button_height,
            "Start Game"
        )
        
        self.settings_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "Settings"
        )
        
        self.exit_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + 2 * (button_height + button_spacing),
            button_width,
            button_height,
            "Exit"
        )
        
        # Create buttons for game mode selection screen
        self.singleplayer_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y,
            button_width,
            button_height,
            "Singleplayer"
        )
        
        self.multiplayer_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + button_height + button_spacing,
            button_width,
            button_height,
            "Multiplayer"
        )
        
        self.back_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            start_y + 2 * (button_height + button_spacing),
            button_width,
            button_height,
            "Back to Menu"
        )
        
        # Create buttons for driver selection screen
        driver_button_width = 400
        driver_button_height = 300
        driver_spacing = 100
        
        self.max_button = Button(
            SCREEN_WIDTH // 2 - driver_button_width - driver_spacing // 2,
            SCREEN_HEIGHT // 2 - driver_button_height // 2,
            driver_button_width,
            driver_button_height,
            "Max Verstappen",
            font_size=30,
            color=(30, 144, 255),  # Blue for Red Bull
            hover_color=(65, 165, 255)
        )
        
        self.charles_button = Button(
            SCREEN_WIDTH // 2 + driver_spacing // 2,
            SCREEN_HEIGHT // 2 - driver_button_height // 2,
            driver_button_width,
            driver_button_height,
            "Charles Leclerc",
            font_size=30,
            color=(220, 20, 60),  # Red for Ferrari
            hover_color=(255, 50, 80)
        )
        
        self.settings_back_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            SCREEN_HEIGHT - 120,
            button_width,
            button_height,
            "Back to Menu"
        )
        
        # Load driver images
        self.max_image_path = os.path.join(os.path.dirname(__file__), "assets", "images", "max_verstappen.png")
        self.charles_image_path = os.path.join(os.path.dirname(__file__), "assets", "images", "charles_leclerc.png")
        
        # Create directories if they don't exist
        os.makedirs(os.path.join(os.path.dirname(__file__), "assets", "images"), exist_ok=True)
        
        # Load driver images if they exist, otherwise use placeholders
        if os.path.exists(self.max_image_path):
            self.max_image = pygame.image.load(self.max_image_path).convert_alpha()
            self.max_image = pygame.transform.scale(self.max_image, (driver_button_width - 40, driver_button_height - 80))
        else:
            self.max_image = None
            
        if os.path.exists(self.charles_image_path):
            self.charles_image = pygame.image.load(self.charles_image_path).convert_alpha()
            self.charles_image = pygame.transform.scale(self.charles_image, (driver_button_width - 40, driver_button_height - 80))
        else:
            self.charles_image = None
        
        # Background image
        self.bg_image_path = os.path.join(os.path.dirname(__file__), "assets", "images", "menu_bg.jpg")
        
        # Create images directory if it doesn't exist
        images_dir = os.path.join(os.path.dirname(__file__), "assets", "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # Load background image if it exists
        if os.path.exists(self.bg_image_path):
            try:
                self.bg_image = pygame.image.load(self.bg_image_path).convert()
                self.bg_image = pygame.transform.scale(self.bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                print(f"Successfully loaded background image: {self.bg_image_path}")
            except pygame.error as e:
                print(f"Error loading background image: {e}")
                self.bg_image = None
        else:
            print(f"Background image not found: {self.bg_image_path}")
            print(f"Please place a menu_bg.jpg file in: {images_dir}")
            self.bg_image = None
        
        # Title
        self.title_font = pygame.font.SysFont(None, 100)
        self.title_text = self.title_font.render("Racing Game", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH//2, start_y - 100))
        
        # Game mode selection title
        self.mode_title_text = self.title_font.render("Select Game Mode", True, WHITE)
        self.mode_title_rect = self.mode_title_text.get_rect(center=(SCREEN_WIDTH//2, start_y - 100))
        
        # Driver selection title
        self.driver_title_text = self.title_font.render("Select Driver", True, WHITE)
        self.driver_title_rect = self.driver_title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
    
    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                self.result = "exit"
        
        # Handle different screens
        if self.current_screen == "main":
            self.handle_main_menu_events(events)
        elif self.current_screen == "game_mode":
            self.handle_game_mode_events(events)
        elif self.current_screen == "driver_selection":
            self.handle_driver_selection_events(events)
    
    def handle_main_menu_events(self, events):
        # Handle main menu button clicks
        if self.start_button.update(events, self.sounds):
            # Switch to game mode selection screen
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.current_screen = "game_mode"
        
        if self.settings_button.update(events, self.sounds):
            # Go to driver selection screen
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.current_screen = "driver_selection"
        
        if self.exit_button.update(events, self.sounds):
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.running = False
            self.result = "exit"
    
    def handle_game_mode_events(self, events):
        # Handle game mode selection button clicks
        if self.singleplayer_button.update(events, self.sounds):
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.running = False
            self.result = "singleplayer"
        
        if self.multiplayer_button.update(events, self.sounds):
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.running = False
            self.result = "multiplayer"
        
        if self.back_button.update(events, self.sounds):
            # Go back to main menu
            if self.sounds["back"]:
                self.sounds["back"].play()
            self.current_screen = "main"
    
    def handle_driver_selection_events(self, events):
        # Handle driver selection button clicks
        if self.max_button.update(events, self.sounds):
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.selected_driver = "max"
            # Save the selection to a file so the game can read it
            self.save_driver_selection("car.png")
            # Visual feedback
            self.max_button.color = (30, 144, 255)  # Brighter blue
            self.charles_button.color = (180, 20, 60)  # Dimmer red
        
        if self.charles_button.update(events, self.sounds):
            if self.sounds["select"]:
                self.sounds["select"].play()
            self.selected_driver = "charles"
            # Save the selection to a file so the game can read it
            self.save_driver_selection("car2.png")
            # Visual feedback
            self.max_button.color = (20, 100, 200)  # Dimmer blue
            self.charles_button.color = (220, 20, 60)  # Brighter red
        
        if self.settings_back_button.update(events, self.sounds):
            # Go back to main menu
            if self.sounds["back"]:
                self.sounds["back"].play()
            self.current_screen = "main"
    
    def save_driver_selection(self, car_image):
        # Save the selected car image to a file that the game can read
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, "car_selection.txt")
        with open(config_path, "w") as f:
            f.write(car_image)
        
        print(f"Selected car: {car_image}")
    
    def render(self):
        # Draw background
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
            
            # Add a semi-transparent overlay to make text more readable
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Black with 50% transparency
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill((50, 50, 80))  # Dark blue-gray background
        
        # Render different screens
        if self.current_screen == "main":
            self.render_main_menu()
        elif self.current_screen == "game_mode":
            self.render_game_mode()
        elif self.current_screen == "driver_selection":
            self.render_driver_selection()
        
        # Update display
        pygame.display.flip()
    
    def render_main_menu(self):
        # Draw title
        self.screen.blit(self.title_text, self.title_rect)
        
        # Draw main menu buttons
        self.start_button.render(self.screen)
        self.settings_button.render(self.screen)
        self.exit_button.render(self.screen)
    
    def render_game_mode(self):
        # Draw title
        self.screen.blit(self.mode_title_text, self.mode_title_rect)
        
        # Draw game mode selection buttons
        self.singleplayer_button.render(self.screen)
        self.multiplayer_button.render(self.screen)
        self.back_button.render(self.screen)
    
    def render_driver_selection(self):
        # Draw title
        self.screen.blit(self.driver_title_text, self.driver_title_rect)
        
        # Draw driver selection buttons
        self.max_button.render(self.screen)
        self.charles_button.render(self.screen)
        self.settings_back_button.render(self.screen)
        
        # Draw driver images on top of buttons
        if self.max_image:
            image_rect = self.max_image.get_rect(center=(
                self.max_button.rect.centerx,
                self.max_button.rect.centery - 20
            ))
            self.screen.blit(self.max_image, image_rect)
        else:
            # Draw placeholder text if image not available
            font = pygame.font.SysFont(None, 24)
            text = font.render("Max Verstappen Image", True, WHITE)
            text_rect = text.get_rect(center=(
                self.max_button.rect.centerx,
                self.max_button.rect.centery - 20
            ))
            self.screen.blit(text, text_rect)
        
        if self.charles_image:
            image_rect = self.charles_image.get_rect(center=(
                self.charles_button.rect.centerx,
                self.charles_button.rect.centery - 20
            ))
            self.screen.blit(self.charles_image, image_rect)
        else:
            # Draw placeholder text if image not available
            font = pygame.font.SysFont(None, 24)
            text = font.render("Charles Leclerc Image", True, WHITE)
            text_rect = text.get_rect(center=(
                self.charles_button.rect.centerx,
                self.charles_button.rect.centery - 20
            ))
            self.screen.blit(text, text_rect)
        
        # Draw driver names below images
        name_font = pygame.font.SysFont(None, 36)
        
        max_name = name_font.render("Max Verstappen", True, WHITE)
        max_name_rect = max_name.get_rect(center=(
            self.max_button.rect.centerx,
            self.max_button.rect.bottom - 30
        ))
        self.screen.blit(max_name, max_name_rect)
        
        charles_name = name_font.render("Charles Leclerc", True, WHITE)
        charles_name_rect = charles_name.get_rect(center=(
            self.charles_button.rect.centerx,
            self.charles_button.rect.bottom - 30
        ))
        self.screen.blit(charles_name, charles_name_rect)
        
        # Draw selection indicator
        if self.selected_driver == "max":
            pygame.draw.rect(self.screen, (255, 255, 0), self.max_button.rect, 5)  # Yellow outline
        else:
            pygame.draw.rect(self.screen, (255, 255, 0), self.charles_button.rect, 5)  # Yellow outline
    
    def run(self):
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            self.render()
            clock.tick(60)  # 60 FPS
        
        # Stop menu music when exiting menu
        pygame.mixer.music.stop()
        
        # If starting the game, start game music
        if self.result in ["singleplayer", "multiplayer"]:
            self.start_game_music()
        
        return self.result or "exit"
    
    def start_game_music(self):
        """Start playing game background music"""
        music_path = os.path.join(os.path.dirname(__file__), "assets", "sounds", "game_music.mp3")
        
        # Check if music file exists
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.2)  # Set volume to 20%
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            except:
                print(f"Could not play game background music: {music_path}")
        else:
            print(f"Game background music file not found: {music_path}")

    def load_sounds(self):
        """Load menu sound effects"""
        sound_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        
        # Create sounds directory if it doesn't exist
        os.makedirs(sound_dir, exist_ok=True)
        
        # Try to load sound effects
        try:
            self.sounds["click"] = pygame.mixer.Sound(os.path.join(sound_dir, "menu_click.wav"))
            self.sounds["hover"] = pygame.mixer.Sound(os.path.join(sound_dir, "menu_hover.wav"))
            self.sounds["select"] = pygame.mixer.Sound(os.path.join(sound_dir, "menu_select.wav"))
            self.sounds["back"] = pygame.mixer.Sound(os.path.join(sound_dir, "menu_back.wav"))
            
            # Set volume for hover sound (quieter)
            if self.sounds["hover"]:
                self.sounds["hover"].set_volume(0.3)
        except:
            print("Could not load menu sound effects. Make sure the files exist in the assets/sounds directory.")

    def start_background_music(self):
        """Start playing menu background music"""
        music_path = os.path.join(os.path.dirname(__file__), "assets", "sounds", "menu_music.mp3")
        
        # Check if music file exists
        if os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.4)  # Set volume to 40%
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
            except:
                print(f"Could not play background music: {music_path}")
        else:
            print(f"Background music file not found: {music_path}")