"""
Orbital Defense Game
--------------------
A simple 2D space game where the player controls a ship in orbit,
defends against enemies, and manages resources.

Core Mechanics:
- Newtonian physics for ship movement, influenced by gravity from celestial bodies.
- Player controls: rotation, thrust, firing railguns and homing missiles.
- Collision detection: ship/projectiles vs. celestial bodies and enemies.
- Game states: Playing, Game Over.
- Basic UI: speed, altitude, weapon status.

Main Components:
- `main.py`: Handles game loop, state management, input, drawing, and initialization.
- `entities.py`: Defines all game objects (PlayerShip, EnemyShip, Projectiles, CelestialBody).
- `vector.py`: Provides a Vec2D class for 2D vector math.
"""
import pygame
import math # math is used in main.py for vy_orbit_planet, etc.
from entities import CelestialBody, PhysicsObject, PlayerShip, Projectile, HomingMissile, EnemyShip 
from vector import Vec2D

# --- Pygame and Font Initialization ---
pygame.init()
pygame.font.init() 

# --- Game Constants ---
# Screen Dimensions
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# Game States
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"

# Physics and Gameplay Constants
# G_GAME = 5000 # Gravitational constant (already defined)
# PLANET_MASS_GAME = 5e6 (already defined)
# MOON_MASS_GAME = 5e4 (already defined)
# PLANET_RADIUS = 50 (already defined)
# MOON_RADIUS = 15 (already defined)

# Colors (using names for clarity)
COLOR_BLACK = (0, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_ENEMY_ORANGE = (255, 100, 0)

# UI Font settings
UI_FONT_SIZE = 24
UI_FONT_NAME = "monospace" # Using a common monospace font

# Player Ship Initial Settings (for reset)
PLAYER_INITIAL_THRUST = 2000.0
PLAYER_INITIAL_ROTATION_SPEED = 180.0 # degrees/sec
PLAYER_INITIAL_MASS = 100.0

# Enemy Settings
ENEMY_DEFAULT_MASS = 100.0
ENEMY_DEFAULT_RADIUS = 12
ENEMY_DEFAULT_HEALTH = 50
ENEMY_DEFAULT_COLOR = COLOR_ENEMY_ORANGE


# --- Global Game Variables ---
current_game_state = GAME_STATE_PLAYING
player_ship_destroyed_flag = False # Tracks if player ship is permanently destroyed
screen = None # Pygame screen surface, initialized later
ui_font = None # UI Font, initialized later
large_font_game_over = None # Font for "GAME OVER" text
medium_font_restart = None # Font for "Press R to Restart" text

# Game Object Lists (managed globally for access in reset_game_state)
celestial_bodies = []
physics_objects = [] # All dynamic objects including player, enemies, projectiles
enemy_ships = [] # Specific list for active enemies (subset of physics_objects)
player_ship = None # Player's ship instance

# Physics Constants (initialized once)
G_GAME = 0.05 # Significantly reduced for more manageable gravity and arcade feel

# --- Helper Functions ---

def initialize_fonts():
    """Initializes fonts used in the game."""
    global ui_font, large_font_game_over, medium_font_restart
    ui_font = pygame.font.SysFont(UI_FONT_NAME, UI_FONT_SIZE)
    if ui_font is None: # Fallback
        ui_font = pygame.font.Font(None, UI_FONT_SIZE + 4)
    
    large_font_game_over = pygame.font.SysFont(UI_FONT_NAME, 72)
    if large_font_game_over is None:
        large_font_game_over = pygame.font.Font(None, 80)

    medium_font_restart = pygame.font.SysFont(UI_FONT_NAME, 36)
    if medium_font_restart is None:
        medium_font_restart = pygame.font.Font(None, 40)


def initialize_celestial_bodies():
    """Creates and initializes celestial bodies."""
    global celestial_bodies, planet, moon # Make planet and moon accessible if needed elsewhere directly
    
    # Planet Properties
    planet_mass = 5e6
    planet_radius = 50
    planet_pos_vec = Vec2D(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    planet = CelestialBody(planet_mass, planet_radius, planet_pos_vec, COLOR_BLUE, name="Planet")

    # Moon Properties
    moon_mass = 5e4
    moon_radius = 15
    moon_pos_vec = Vec2D(planet_pos_vec.x + 300, planet_pos_vec.y) # Relative to planet
    moon = CelestialBody(moon_mass, moon_radius, moon_pos_vec, COLOR_GRAY, name="Moon")
    
    celestial_bodies = [planet, moon]

def initialize_dummy_satellites():
    """Initializes dummy satellites for visual effect or testing (optional)."""
    # This function can be called in reset_game_state or initial setup if these are desired.
    # For now, they are not automatically added on reset to keep it simple.
    if not celestial_bodies: # Ensure planet exists for positioning
        print("Warning: Celestial bodies not initialized before dummy satellites.")
        return [] # Return empty list if no celestial bodies
        
    # Satellite 1 (orbits planet)
    # Uses global G_GAME and planet (from initialize_celestial_bodies)
    initial_dist_planet = planet.radius + 100 # Orbit above planet surface
    vy_orbit_p = math.sqrt(G_GAME * planet.mass / initial_dist_planet)
    sat1_pos = Vec2D(planet.position_vec.x + initial_dist_planet, planet.position_vec.y)
    sat1_vel = Vec2D(0, -vy_orbit_p) # Moving "up" for counter-clockwise
    satellite1 = PhysicsObject(mass=1, position_vec=sat1_pos, velocity_vec=sat1_vel, color=COLOR_WHITE, radius=3)

    # Satellite 2 (orbits moon)
    # Uses global G_GAME and moon (from initialize_celestial_bodies)
    initial_dist_moon = moon.radius + 35 
    vy_orbit_m = math.sqrt(G_GAME * moon.mass / initial_dist_moon)
    sat2_pos = Vec2D(moon.position_vec.x + initial_dist_moon, moon.position_vec.y)
    sat2_vel = Vec2D(0, -vy_orbit_m)
    satellite2 = PhysicsObject(mass=1, position_vec=sat2_pos, velocity_vec=sat2_vel, color=COLOR_YELLOW, radius=2)
    
    return [satellite1, satellite2]


def reset_game_state():
    """Resets the game to the initial playing state."""
    global current_game_state, player_ship_destroyed_flag, player_ship
    global physics_objects, enemy_ships 
    # celestial_bodies are assumed to be static and already initialized

    current_game_state = GAME_STATE_PLAYING
    player_ship_destroyed_flag = False

    # Re-create player_ship
    initial_player_pos = Vec2D(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200) # Start above planet center
    player_ship = PlayerShip(
        mass=PLAYER_INITIAL_MASS, 
        position_vec=initial_player_pos, 
        thrust_strength=PLAYER_INITIAL_THRUST,
        rotation_speed=PLAYER_INITIAL_ROTATION_SPEED 
    )
    # Reset weapon cooldowns explicitly (already part of PlayerShip init, but good for clarity)
    player_ship.last_railgun_fire_time = 0.0
    player_ship.last_missile_fire_time = 0.0
    
    # Reset dynamic physics objects
    physics_objects.clear()
    physics_objects.append(player_ship) # Add new player ship
    
    # Re-initialize enemies
    enemy_ships.clear() 
    enemy_start_pos = Vec2D(planet.position_vec.x + planet.radius + 150, planet.position_vec.y) # Position relative to planet
    enemy1 = EnemyShip(
        mass=ENEMY_DEFAULT_MASS, 
        position_vec=enemy_start_pos, 
        color=ENEMY_DEFAULT_COLOR, 
        radius=ENEMY_DEFAULT_RADIUS, 
        health=ENEMY_DEFAULT_HEALTH
    )
    enemy_ships.append(enemy1)
    physics_objects.extend(enemy_ships) # Add enemies to physics simulation

    # Optional: Re-add dummy satellites if desired for every reset
    # dummy_sats = initialize_dummy_satellites()
    # physics_objects.extend(dummy_sats)

    print("Game Reset!")

def draw_ui(current_screen, ship_obj, primary_planet, font, font_size_val):
    """Draws the game UI (speed, altitude, weapon status)."""
    if ship_obj is None or player_ship_destroyed_flag: # Don't draw UI if no ship or game over
        return

    y_offset = 10
    line_spacing = font_size_val + 2

    # Speed
    speed = ship_obj.get_speed()
    speed_text = f"Speed: {speed:.1f} units/s"
    speed_surface = font.render(speed_text, True, COLOR_WHITE)
    current_screen.blit(speed_surface, (10, y_offset))
    y_offset += line_spacing

    # Altitude (relative to the main planet)
    altitude = ship_obj.get_altitude(primary_planet) 
    altitude_text = f"Altitude: {altitude:.1f} units"
    altitude_surface = font.render(altitude_text, True, COLOR_WHITE)
    current_screen.blit(altitude_surface, (10, y_offset))
    y_offset += line_spacing

    # Missile Status (simplified: just indicates readiness from player ship attribute)
    # Could be enhanced to show ammo count later.
    missile_cooldown_remaining = ship_obj.missile_cooldown_time - (pygame.time.get_ticks()/1000.0 - ship_obj.last_missile_fire_time)
    missile_status = "Ready" if missile_cooldown_remaining <= 0 else f"CD: {missile_cooldown_remaining:.1f}s"
    missile_text = f"Missiles: {missile_status}"
    missile_surface = font.render(missile_text, True, COLOR_WHITE)
    current_screen.blit(missile_surface, (10, y_offset))
    y_offset += line_spacing

    # Railgun Status
    railgun_cooldown_remaining = ship_obj.railgun_cooldown_time - (pygame.time.get_ticks()/1000.0 - ship_obj.last_railgun_fire_time)
    railgun_status = "Ready" if railgun_cooldown_remaining <= 0 else f"CD: {railgun_cooldown_remaining:.1f}s"
    railgun_text = f"Railgun: {railgun_status}"
    railgun_surface = font.render(railgun_text, True, COLOR_WHITE)
    current_screen.blit(railgun_surface, (10, y_offset))
    y_offset += line_spacing
    
    # Missile Fuel Capacity (per missile unit)
    missile_fuel_text = f"Missile Fuel/Unit: {ship_obj.missile_fuel:.1f}s"
    missile_fuel_surf = font.render(missile_fuel_text, True, COLOR_WHITE)
    current_screen.blit(missile_fuel_surf, (10, y_offset))


# --- Main Game Setup ---
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Orbital Defense")

initialize_fonts()
initialize_celestial_bodies() # Initialize planet and moon

# Initial game setup
# Instantiate PlayerShip (will be overwritten by reset_game_state if called immediately)
# This initial player_ship is mostly a placeholder before the first potential reset.
player_ship = PlayerShip(
    mass=PLAYER_INITIAL_MASS, 
    position_vec=Vec2D(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200), 
    thrust_strength=50000, # Different from reset for initial visual
    rotation_speed=200    # Different from reset
)
physics_objects.append(player_ship)

# Initialize enemies (will be overwritten by reset_game_state if called immediately)
enemy_start_pos_init = Vec2D(planet.position_vec.x + planet.radius + 100, planet.position_vec.y)
enemy1_init = EnemyShip(
    mass=ENEMY_DEFAULT_MASS, 
    position_vec=enemy_start_pos_init, 
    color=ENEMY_DEFAULT_COLOR, 
    radius=ENEMY_DEFAULT_RADIUS, 
    health=ENEMY_DEFAULT_HEALTH
)
enemy_ships.append(enemy1_init)
physics_objects.extend(enemy_ships)

# Optional: Add initial dummy satellites
# initial_dummy_sats = initialize_dummy_satellites()
# physics_objects.extend(initial_dummy_sats)

reset_game_state() # Call reset_game_state once at the start to ensure consistent state

# --- Game Loop ---
running = True
clock = pygame.time.Clock()
player_ship_collided_this_frame = False # Frame-local flag for player collision

while running:
    delta_time = clock.tick(60) / 1000.0
    if delta_time > 0.05: delta_time = 0.05 # Cap delta_time to prevent physics instability

    player_ship_collided_this_frame = False # Reset at the start of each frame

    # === Event Handling ===
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if current_game_state == GAME_STATE_PLAYING:
                if event.key == pygame.K_p: # Toggle orbit predictor
                    if player_ship: # Ensure player_ship exists
                        player_ship.show_orbit_predictor = not player_ship.show_orbit_predictor
            elif current_game_state == GAME_STATE_GAME_OVER:
                if event.key == pygame.K_r: # Restart game
                    reset_game_state()

    # === Game Logic ===
    if current_game_state == GAME_STATE_PLAYING:
        # --- Player Input ---
        keys = pygame.key.get_pressed()
        if player_ship and not player_ship_destroyed_flag : # Check if player_ship exists and is not destroyed
            if keys[pygame.K_a]: player_ship.rotate(-1, delta_time) # Rotate left
            if keys[pygame.K_d]: player_ship.rotate(1, delta_time)  # Rotate right
            if keys[pygame.K_w]: player_ship.apply_ship_thrust()    # Apply thrust
            if keys[pygame.K_SPACE]: player_ship.fire_railgun()     # Fire railgun
            if keys[pygame.K_m]:                                    # Fire missile
                target_for_missile = None
                # Prioritize targeting live enemies
                live_enemies = [e for e in enemy_ships if e.health > 0 and e in physics_objects]
                if live_enemies:
                    target_for_missile = live_enemies[0] 
                elif moon: # Fallback to moon if no live enemies
                    target_for_missile = moon 
                if target_for_missile:
                    player_ship.fire_missile(target_for_missile)

        # --- Updates ---
        # Orbit prediction (only if player ship is active)
        if player_ship and player_ship in physics_objects and not player_ship_destroyed_flag:
            player_ship.predict_orbit(celestial_bodies, G_GAME)

        # Collect new projectiles from player ship
        if player_ship and player_ship.projectiles_to_add:
            physics_objects.extend(player_ship.projectiles_to_add)
            player_ship.projectiles_to_add.clear()

        # Update all physics objects (player, enemies, projectiles)
        active_physics_objects_after_updates = []
        for p_obj in physics_objects:
            # Specific updates based on type
            if isinstance(p_obj, HomingMissile): 
                 p_obj.update_guidance_and_thrust(delta_time)
            elif isinstance(p_obj, EnemyShip):
                 # Pass player_ship if it exists, else None (for AI targeting)
                 current_player_target = player_ship if player_ship in physics_objects else None
                 p_obj.update_ai(delta_time, current_player_target, celestial_bodies, G_GAME)
            
            # General physics update
            p_obj.update_physics(delta_time, celestial_bodies, G_GAME)
            
            # Lifespan check for projectiles (including HomingMissiles)
            still_active = True
            if isinstance(p_obj, Projectile): 
                if not p_obj.update(delta_time): # update() returns False if lifespan expired
                    still_active = False
            
            if still_active:
                active_physics_objects_after_updates.append(p_obj)
        physics_objects = active_physics_objects_after_updates

        # --- Collision Handling ---
        # This section determines which objects survive collisions this frame.
        new_physics_objects_after_collisions = []
        player_ship_survived_this_frame = not player_ship_collided_this_frame # Initial assumption

        # Ensure player_ship reference is valid if it was part of physics_objects
        if player_ship and player_ship not in physics_objects:
             player_ship_survived_this_frame = False # It was removed before collision checks (e.g. by other logic)
        
        # Temporary lists to manage objects during collision checks
        collided_projectiles = set()
        destroyed_enemies = set()

        for p_obj in physics_objects:
            is_obj_destroyed_this_step = False # Has this specific object been destroyed in this iteration?

            # 1. Player Ship Collision Checks
            if p_obj == player_ship:
                for body in celestial_bodies: # Player vs Celestial Body
                    if p_obj.check_collision(body):
                        print(f"Player ship collided with {body.name}!")
                        player_ship_collided_this_frame = True # Set frame-local flag
                        player_ship_survived_this_frame = False
                        is_obj_destroyed_this_step = True
                        break 
                if is_obj_destroyed_this_step: continue # Player ship destroyed, skip other checks for it

            # 2. Projectile Collision Checks (Railgun & Missiles)
            elif isinstance(p_obj, Projectile):
                # Projectile vs Celestial Body
                for body in celestial_bodies:
                    if p_obj.check_collision(body):
                        collided_projectiles.add(p_obj)
                        is_obj_destroyed_this_step = True
                        break
                if is_obj_destroyed_this_step: continue

                # Projectile vs Enemy Ship
                for enemy in enemy_ships: # Iterate through the specific enemy_ships list
                    if enemy.health > 0 and enemy not in destroyed_enemies and enemy in physics_objects: # Check if enemy is alive and not already processed
                        if p_obj.check_collision(enemy):
                            damage = 50 if isinstance(p_obj, HomingMissile) else 25 # Example damage values
                            if enemy.take_damage(damage): # True if enemy health <= 0
                                destroyed_enemies.add(enemy)
                            collided_projectiles.add(p_obj) # Projectile is consumed
                            is_obj_destroyed_this_step = True
                            break # Projectile hit one enemy, it's done
                if is_obj_destroyed_this_step: continue
            
            # 3. Enemy Ship Collision Checks (Enemy vs Celestial Body)
            elif isinstance(p_obj, EnemyShip):
                if p_obj in destroyed_enemies: # Already destroyed by a projectile
                    is_obj_destroyed_this_step = True
                else: # Check collision with celestial bodies
                    for body in celestial_bodies:
                        if p_obj.check_collision(body):
                            print(f"Enemy {id(p_obj)} collided with {body.name} and was destroyed.")
                            destroyed_enemies.add(p_obj) # Mark as destroyed
                            is_obj_destroyed_this_step = True
                            break
                if is_obj_destroyed_this_step: continue

            # If the object wasn't destroyed by any checks, add it to the list of survivors
            if not is_obj_destroyed_this_step:
                new_physics_objects_after_collisions.append(p_obj)
        
        # Update physics_objects list with survivors
        physics_objects = new_physics_objects_after_collisions
        
        # Update enemy_ships list to only contain surviving enemies
        enemy_ships = [e for e in enemy_ships if e not in destroyed_enemies and e in physics_objects]

        # Update game over state if player ship was destroyed this frame
        if player_ship_collided_this_frame: 
            current_game_state = GAME_STATE_GAME_OVER
            player_ship_destroyed_flag = True # Set persistent flag
            # Player ship is already removed from physics_objects if it collided

    # === Drawing ===
    screen.fill(COLOR_BLACK) # Use defined color constant

    if current_game_state == GAME_STATE_PLAYING:
        # Draw celestial bodies
        for body in celestial_bodies:
            body.draw(screen)
        # Draw all remaining physics objects (player, enemies, projectiles)
        for p_obj in physics_objects: 
            p_obj.draw(screen)
        
        # Draw UI elements
        draw_ui(screen, player_ship, planet, ui_font, UI_FONT_SIZE)

    elif current_game_state == GAME_STATE_GAME_OVER:
        # Optionally draw celestial bodies in game over screen for context
        for body in celestial_bodies:
            body.draw(screen)

        # "GAME OVER" Text
        go_surface = large_font_game_over.render("GAME OVER", True, COLOR_RED)
        go_rect = go_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(go_surface, go_rect)

        # "Press 'R' to Restart" Text
        restart_surface = medium_font_restart.render("Press 'R' to Restart", True, COLOR_WHITE)
        restart_rect = restart_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(restart_surface, restart_rect)

    pygame.display.flip() # Update the full display

pygame.quit() # Uninitialize Pygame modules
