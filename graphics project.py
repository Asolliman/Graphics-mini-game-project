import pygame as pg
from OpenGL.GL import *
from OpenGL.GLU import *
from pygame.locals import DOUBLEBUF, OPENGL, QUIT, K_LEFT, K_RIGHT, K_q, K_r
import random
import math

# --- Display List IDs ---
CAR_3D_LIST_ID = 0
STREET_LIST_ID = 0

# --- Added 3D Car Model Data Back ---
# Simple blocky car shape
car_vertices = [
    # Main body (slightly wider base)
    ( 1.2, -0.5, -2.0), ( 1.2,  0.5, -2.0), (-1.2,  0.5, -2.0), (-1.2, -0.5, -2.0), # 0-3 Front face base
    ( 1.2, -0.5,  2.0), ( 1.2,  0.5,  2.0), (-1.2, -0.5,  2.0), (-1.2,  0.5,  2.0), # 4-7 Back face base
    # Roof/Cabin (narrower, shorter)
    ( 1.0,  0.5, -1.0), ( 1.0,  1.2, -1.0), (-1.0,  1.2, -1.0), (-1.0,  0.5, -1.0), # 8-11 Front cabin
    ( 1.0,  0.5,  1.5), ( 1.0,  1.2,  1.5), (-1.0,  0.5,  1.5), (-1.0,  1.2,  1.5)  # 12-15 Back cabin
]

# Faces defined by vertex indices (ensure counter-clockwise order for front-facing)
car_faces = [
    # Main Body Faces (6 faces)
    (0, 3, 2, 1), # Front Base
    (4, 5, 7, 6), # Back Base
    (0, 4, 6, 3), # Bottom
    (1, 2, 7, 5), # Top Base (where cabin sits)
    (0, 1, 5, 4), # Right Base
    (3, 6, 7, 2), # Left Base
    # Cabin Faces (5 faces - skip bottom which overlaps)
    (8, 11, 10, 9), # Front Cabin
    (12, 13, 15, 14), # Back Cabin
    (9, 10, 14, 13), # Roof
    (8, 9, 13, 12), # Right Cabin
    (11, 15, 14, 10) # Left Cabin
]

car_colors = [ # One color per face
    (0.8, 0.1, 0.1), # Front Base Red
    (0.8, 0.1, 0.1), # Back Base Red
    (0.3, 0.3, 0.3), # Bottom Gray
    (0.8, 0.1, 0.1), # Top Base Red
    (0.8, 0.1, 0.1), # Right Base Red
    (0.8, 0.1, 0.1), # Left Base Red
    (0.6, 0.8, 1.0), # Front Cabin Blue (window)
    (0.6, 0.8, 1.0), # Back Cabin Blue (window)
    (0.7, 0.1, 0.1), # Roof Dark Red
    (0.7, 0.1, 0.1), # Right Cabin Dark Red
    (0.7, 0.1, 0.1)  # Left Cabin Dark Red
]

# --- Drawing Functions ---
def draw_rect(x, y, width, height, r, g, b):
    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

def draw_street_background_geometry():
    # Full window coordinates
    road_x = -ASPECT_X
    road_w = ASPECT_X * 2
    # Draw road (dark gray)
    draw_rect(road_x, -1, road_w, 2, 0.18, 0.18, 0.18)
    # Draw lane lines (dashed white)
    num_lanes = 3
    lane_w = road_w / num_lanes
    dash_h = 0.09
    gap_h = 0.08
    for i in range(1, num_lanes):
        lane_x = road_x + i * lane_w
        y = -1
        while y < 1:
            draw_rect(lane_x - 0.01, y, 0.02, dash_h, 1, 1, 1)
            y += dash_h + gap_h

def draw_street_background():
    global STREET_LIST_ID
    if STREET_LIST_ID:
        glCallList(STREET_LIST_ID)
    else:
        # Fallback if list compilation failed
        draw_street_background_geometry()

def draw_timer(seconds, window_w, window_h):
    # Render timer using Pygame font, then blit as texture
    font = pg.font.SysFont("Arial", 36, bold=True)
    timer_text = f"Time: {seconds:.1f}s"
    text_surf = font.render(timer_text, True, (255,255,255))
    text_data = pg.image.tostring(text_surf, "RGBA", True)
    tw, th = text_surf.get_size()
    text_x = (window_w - tw) / 2
    text_y = 40  # Lowered from top

    # Set up OpenGL for 2D overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window_w, window_h, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # Draw timer text
    glRasterPos2f(text_x, text_y)
    glDrawPixels(tw, th, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glDisable(GL_BLEND)

    # Restore OpenGL matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_circle(x, y, radius, r, g, b):
    # import math # No longer needed here
    glColor3f(r, g, b)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(x, y)
    for i in range(20):
        angle = 2 * math.pi * i / 20
        glVertex2f(x + math.cos(angle) * radius, y + math.sin(angle) * radius)
    glEnd()

def draw_taxi(x, y, width, height):
    # Wheels (black rectangles, top-down corners)
    wheel_w = width * 0.18
    wheel_h = height * 0.18
    # Front
    draw_rect(x - wheel_w*0.7, y + height*0.07, wheel_w, wheel_h, 0.1, 0.1, 0.1)
    draw_rect(x + width - wheel_w*0.3, y + height*0.07, wheel_w, wheel_h, 0.1, 0.1, 0.1)
    # Rear
    draw_rect(x - wheel_w*0.7, y + height*0.75, wheel_w, wheel_h, 0.1, 0.1, 0.1)
    draw_rect(x + width - wheel_w*0.3, y + height*0.75, wheel_w, wheel_h, 0.1, 0.1, 0.1)
    # Main body (yellow)
    draw_rect(x, y, width, height, 1.0, 0.85, 0.1)
    # Windows (light blue, top part)
    win_y = y + height*0.08
    win_h = height * 0.32
    draw_rect(x + width*0.13, win_y, width*0.74, win_h, 0.6, 0.8, 1.0)
    # Taxi sign (small white/yellow box on roof)
    sign_w = width * 0.28
    sign_h = height * 0.10
    sign_x = x + width/2 - sign_w/2
    sign_y = y + height*0.01
    draw_rect(sign_x, sign_y, sign_w, sign_h, 1, 1, 0.2)
    glColor3f(0,0,0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(sign_x, sign_y)
    glVertex2f(sign_x + sign_w, sign_y)
    glVertex2f(sign_x + sign_w, sign_y + sign_h)
    glVertex2f(sign_x, sign_y + sign_h)
    glEnd()
    # Bumpers (black, front/rear)
    bumper_h = height * 0.07
    draw_rect(x, y, width, bumper_h, 0.1, 0.1, 0.1)
    draw_rect(x, y + height - bumper_h, width, bumper_h, 0.1, 0.1, 0.1)
    # Hood/trunk line
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINES)
    glVertex2f(x, y + height*0.23)
    glVertex2f(x + width, y + height*0.23)
    glVertex2f(x, y + height*0.77)
    glVertex2f(x + width, y + height*0.77)
    glEnd()


def draw_motorcycle(x, y, width, height):
    # Wheels (black circles, front/rear)
    wheel_r = width * 0.22
    draw_circle(x + width/2, y + height*0.11, wheel_r, 0.1, 0.1, 0.1)
    draw_circle(x + width/2, y + height*0.89, wheel_r, 0.1, 0.1, 0.1)
    # Body (thin central rectangle)
    draw_rect(x + width*0.42, y + height*0.18, width*0.16, height*0.64, 0.2, 0.5, 1.0)
    # Fuel tank (ellipse)
    import math
    glColor3f(0.3, 0.7, 1.0)
    glBegin(GL_POLYGON)
    for i in range(20):
        angle = 2 * math.pi * i / 20
        glVertex2f(x + width/2 + math.cos(angle)*width*0.18, y + height*0.40 + math.sin(angle)*height*0.13)
    glEnd()
    # Seat (dark gray)
    draw_rect(x + width*0.44, y + height*0.63, width*0.12, height*0.13, 0.2, 0.2, 0.2)
    # Headlight (yellow, front)
    draw_circle(x + width/2, y + height*0.07, width*0.08, 1.0, 1.0, 0.2)
    # Handlebars (gray, front)
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES)
    glVertex2f(x + width/2, y)
    glVertex2f(x + width*0.28, y + height*0.10)
    glVertex2f(x + width/2, y)
    glVertex2f(x + width*0.72, y + height*0.10)
    glEnd()
    # Rider helmet (red, middle)
    draw_circle(x + width/2, y + height*0.48, width*0.10, 1.0, 0.2, 0.2)
    # Accent stripe (white, vertical)
    draw_rect(x + width*0.49, y + height*0.22, width*0.02, height*0.56, 1, 1, 1)

def draw_car(x, y, width, height, color=(0.8, 0.1, 0.1), flipped=False):
    # If flipped, draw car facing the other way (front at bottom)
    if not flipped:
        # Main body
        draw_rect(x, y, width, height, *color)
        # Windshield (light blue)
        ws_h = height * 0.25
        ws_y = y + height - ws_h * 0.9
        draw_rect(x + width * 0.2, ws_y, width * 0.6, ws_h, 0.6, 0.85, 1.0)
        # Wheels (black rectangles)
        wheel_w = width * 0.18
        wheel_h = height * 0.18
        # Left wheels
        draw_rect(x - wheel_w * 0.5, y + height * 0.15, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        draw_rect(x - wheel_w * 0.5, y + height * 0.65, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        # Right wheels
        draw_rect(x + width - wheel_w * 0.5, y + height * 0.15, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        draw_rect(x + width - wheel_w * 0.5, y + height * 0.65, wheel_w, wheel_h, 0.05, 0.05, 0.05)
    else:
        # Main body
        draw_rect(x, y, width, height, *color)
        # Windshield (light blue) at bottom
        ws_h = height * 0.25
        ws_y = y + ws_h * 0.1
        draw_rect(x + width * 0.2, ws_y, width * 0.6, ws_h, 0.6, 0.85, 1.0)
        # Wheels (black rectangles)
        wheel_w = width * 0.18
        wheel_h = height * 0.18
        # Left wheels
        draw_rect(x - wheel_w * 0.5, y + height * 0.15, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        draw_rect(x - wheel_w * 0.5, y + height * 0.65, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        # Right wheels
        draw_rect(x + width - wheel_w * 0.5, y + height * 0.15, wheel_w, wheel_h, 0.05, 0.05, 0.05)
        draw_rect(x + width - wheel_w * 0.5, y + height * 0.65, wheel_w, wheel_h, 0.05, 0.05, 0.05)

def draw_3d_car_geometry():
    # --- Draw Main Body/Cabin ---
    glBegin(GL_QUADS)
    for i, face in enumerate(car_faces):
        if 0 <= i < len(car_colors):
            glColor3fv(car_colors[i])
        else:
            glColor3f(1,1,1)
            print(f"Warning: Color index {i} out of bounds")
        for vertex_index in face:
            if 0 <= vertex_index < len(car_vertices):
                 glVertex3fv(car_vertices[vertex_index])
            else:
                 print(f"Warning: Vertex index {vertex_index} out of bounds for face {i}")
    glEnd()

    # --- Draw Wheels (simple blocks) ---
    wheel_color = (0.15, 0.15, 0.15)
    wheel_w = 0.3; wheel_h = 0.6; wheel_d = 0.6
    body_w = 1.2; body_y_offset = -0.5
    front_z = -1.8; rear_z = 1.3
    wheel_x_offset = body_w + wheel_w * 0.1

    glColor3fv(wheel_color)
    # Front Right
    glPushMatrix(); glTranslatef(wheel_x_offset, body_y_offset + wheel_h/2, front_z); glScalef(wheel_w, wheel_h, wheel_d); draw_cube(); glPopMatrix()
    # Front Left
    glPushMatrix(); glTranslatef(-wheel_x_offset, body_y_offset + wheel_h/2, front_z); glScalef(wheel_w, wheel_h, wheel_d); draw_cube(); glPopMatrix()
    # Rear Right
    glPushMatrix(); glTranslatef(wheel_x_offset, body_y_offset + wheel_h/2, rear_z); glScalef(wheel_w, wheel_h, wheel_d); draw_cube(); glPopMatrix()
    # Rear Left
    glPushMatrix(); glTranslatef(-wheel_x_offset, body_y_offset + wheel_h/2, rear_z); glScalef(wheel_w, wheel_h, wheel_d); draw_cube(); glPopMatrix()

    # --- Draw Lights ---
    light_w = 0.2; light_h = 0.15; light_d = 0.05
    light_y = 0.0; front_light_z = -2.0 - light_d; rear_light_z = 2.0 + light_d
    light_x = 0.7

    # Headlights (Yellow)
    glColor3f(1.0, 1.0, 0.2)
    glPushMatrix(); glTranslatef(light_x, light_y, front_light_z); glScalef(light_w, light_h, light_d); draw_cube(); glPopMatrix()
    glPushMatrix(); glTranslatef(-light_x, light_y, front_light_z); glScalef(light_w, light_h, light_d); draw_cube(); glPopMatrix()
    # Taillights (Red)
    glColor3f(1.0, 0.1, 0.1)
    glPushMatrix(); glTranslatef(light_x, light_y, rear_light_z); glScalef(light_w, light_h, light_d); draw_cube(); glPopMatrix()
    glPushMatrix(); glTranslatef(-light_x, light_y, rear_light_z); glScalef(light_w, light_h, light_d); draw_cube(); glPopMatrix()

# Helper function to draw a unit cube centered at origin
def draw_cube():
    glBegin(GL_QUADS)
    # Front Face
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f( 0.5, -0.5, 0.5)
    glVertex3f( 0.5,  0.5, 0.5)
    glVertex3f(-0.5,  0.5, 0.5)
    # Back Face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5,  0.5, -0.5)
    glVertex3f( 0.5,  0.5, -0.5)
    glVertex3f( 0.5, -0.5, -0.5)
    # Top Face
    glVertex3f(-0.5,  0.5, -0.5)
    glVertex3f(-0.5,  0.5,  0.5)
    glVertex3f( 0.5,  0.5,  0.5)
    glVertex3f( 0.5,  0.5, -0.5)
    # Bottom Face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f( 0.5, -0.5, -0.5)
    glVertex3f( 0.5, -0.5,  0.5)
    glVertex3f(-0.5, -0.5,  0.5)
    # Right face
    glVertex3f( 0.5, -0.5, -0.5)
    glVertex3f( 0.5,  0.5, -0.5)
    glVertex3f( 0.5,  0.5,  0.5)
    glVertex3f( 0.5, -0.5,  0.5)
    # Left Face
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5,  0.5)
    glVertex3f(-0.5,  0.5,  0.5)
    glVertex3f(-0.5,  0.5, -0.5)
    glEnd()

# --- Compilation Function ---
def compile_display_lists():
    global CAR_3D_LIST_ID, STREET_LIST_ID
    print("Compiling display lists...")
    try:
        # Compile 3D Car
        CAR_3D_LIST_ID = glGenLists(1)
        if not CAR_3D_LIST_ID:
            print("Error: Failed to generate display list for 3D car.")
            return
        glNewList(CAR_3D_LIST_ID, GL_COMPILE)
        draw_3d_car_geometry() # Call the function containing geometry commands
        glEndList()
        print(f"  - 3D Car list compiled (ID: {CAR_3D_LIST_ID})")

        # Compile Street Background
        STREET_LIST_ID = glGenLists(1)
        if not STREET_LIST_ID:
            print("Error: Failed to generate display list for street.")
            return
        glNewList(STREET_LIST_ID, GL_COMPILE)
        # Critical: Set projection for street compilation temporarily
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(-ASPECT_X, ASPECT_X, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        # Draw the geometry
        draw_street_background_geometry()
        # Restore matrices
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW) # Ensure modelview is current
        glEndList()
        print(f"  - Street background list compiled (ID: {STREET_LIST_ID})")

    except Exception as e:
        print(f"Error during display list compilation: {e}")
        # Reset IDs on error to prevent calling invalid lists
        CAR_3D_LIST_ID = 0
        STREET_LIST_ID = 0

# --- Game Constants ---
WINDOW_W, WINDOW_H = 600, 900
ASPECT_X = WINDOW_W / WINDOW_H
PLAYER_W, PLAYER_H = 0.13, 0.19
BLOCK_W, BLOCK_H = 0.18, 0.07
MOTO_W, MOTO_H = 0.08, 0.12
PLAYER_SPEED = 0.03
BLOCK_SPEED = 0.01
BLOCK_INTERVAL = 60  # Frames between new blocks

# --- Main Game Loop ---
def main():
    pg.init()
    pg.font.init()
    pg.display.set_mode((WINDOW_W, WINDOW_H), DOUBLEBUF | OPENGL)
    pg.display.set_caption("Wrong Way!")
    gluOrtho2D(-ASPECT_X, ASPECT_X, -1, 1)
    # Initialize mixer here, but load/play music later
    try:
        pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except Exception as e:
        print(f"Could not initialize mixer: {e}")
        pg.mixer = None # Disable mixer if init fails
    
    # Load crash sound (replace extension if needed)
    crash_sound_path = r"C:\\Users\\mrsol\\Downloads\\car_crash.wav" # <-- Updated filename
    try:
        crash_sound = pg.mixer.Sound(crash_sound_path)
    except Exception as e:
        print(f"Could not load crash sound: {e}")
        crash_sound = None # Set to None if loading fails
    
    # --- COMPILE DISPLAY LISTS ---
    compile_display_lists()
    # ---------------------------
    
    # Player starts at bottom center
    player_x = 0 - PLAYER_W/2
    player_y = -0.6
    player_w = PLAYER_W

    blocks = []  # Each block: [x, y, type]
    frame_count = 0
    running = True
    clock = pg.time.Clock()
    score = 0
    start_ticks = pg.time.get_ticks()

    game_state = "start_menu" # Possible states: start_menu, playing, game_over
    rotation_y = 0.0 # Added for start menu 3D rotation

    while True: # Main loop now controls game state transitions
        if game_state == "start_menu":
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(45, (WINDOW_W / WINDOW_H), 0.1, 100.0) # Increased far clip plane
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glTranslatef(0.0, 0.0, -15) # Move camera back

            glEnable(GL_DEPTH_TEST)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Set up transformations for the 3D car
            glPushMatrix()
            glRotatef(rotation_y, 0, 1, 0)
            glScalef(0.5, 0.5, 0.5)
            glTranslatef(0, -0.5, 0)
            # Call the compiled display list
            if CAR_3D_LIST_ID:
                glCallList(CAR_3D_LIST_ID)
            else:
                # Fallback: Draw geometry directly if list failed
                draw_3d_car_geometry()
            glPopMatrix()

            rotation_y += 0.5 # Increment rotation angle
            if rotation_y > 360: rotation_y -= 360

            glDisable(GL_DEPTH_TEST) # Disable depth test for 2D overlay
            # Overlay text (draw_text handles its own ortho projection setup)
            draw_text("Wrong Way!", WINDOW_W / 2, WINDOW_H / 4, 50, (255, 255, 0))
            draw_text("Press any key to start", WINDOW_W / 2, WINDOW_H * 3/4, 30, (255, 255, 255))
            pg.display.flip()

            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    return
                if event.type == pg.KEYDOWN:
                    # Load and play music ONLY when starting a new game
                    if pg.mixer:
                        music_path = r"C:\\Users\\mrsol\\Downloads\\perfect-299866.mp3"
                        try:
                            pg.mixer.music.load(music_path)
                            pg.mixer.music.play(-1) # Loop forever
                        except Exception as e:
                            print(f"Could not load/play music: {e}")
                    
                    game_state = "playing"
                    # CRITICAL: Reset projection to 2D for the game
                    glMatrixMode(GL_PROJECTION)
                    glLoadIdentity()
                    gluOrtho2D(-ASPECT_X, ASPECT_X, -1, 1)
                    glMatrixMode(GL_MODELVIEW)
                    glLoadIdentity()
                    glDisable(GL_DEPTH_TEST) # Ensure depth test is off for 2D game

                    # Reset game variables for a new game
                    player_x = 0 - PLAYER_W/2
                    player_y = -0.6
                    player_w = PLAYER_W
                    blocks = []
                    frame_count = 0
                    score = 0
                    start_ticks = pg.time.get_ticks()
                    running = True


        elif game_state == "playing":
            if not running: # Game over condition met
                game_state = "game_over"
                # Reset projection to 2D Ortho needed for game over screen text
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                gluOrtho2D(-ASPECT_X, ASPECT_X, -1, 1)
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                continue

            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    return # Exit main function, thus exiting game
            keys = pg.key.get_pressed()
            if keys[K_LEFT]:
                player_x -= PLAYER_SPEED
            if keys[K_RIGHT]:
                player_x += PLAYER_SPEED
            # Timer for car thickness
            elapsed_sec = (pg.time.get_ticks() - start_ticks) / 1000.0
            intervals = int(elapsed_sec // 10)
            player_w = PLAYER_W * (1.1 ** intervals)

            # Clamp player to screen
            player_x = max(-ASPECT_X, min(ASPECT_X - player_w, player_x))

            # Spawn new block
            if frame_count % BLOCK_INTERVAL == 0:
                if random.random() < 0.5:
                    bx = random.uniform(-ASPECT_X, ASPECT_X - BLOCK_W)
                    blocks.append([bx, 1, 'taxi'])
                else:
                    bx = random.uniform(-ASPECT_X, ASPECT_X - MOTO_W)
                    blocks.append([bx, 1, 'moto'])
            frame_count += 1

            # Move blocks
            for b in blocks:
                b[1] -= BLOCK_SPEED
            # Remove off-screen blocks
            blocks = [b for b in blocks if (b[2]=='taxi' and b[1] > -1 - BLOCK_H) or (b[2]=='moto' and b[1] > -1 - MOTO_H)]

            # Collision detection
            for b in blocks:
                if b[2] == 'taxi':
                    bw, bh = BLOCK_W, BLOCK_H
                else:
                    bw, bh = MOTO_W, MOTO_H
                # Collision check needs to consider player's current width (player_w)
                if (b[0] < player_x + player_w and b[0] + bw > player_x and
                    b[1] < player_y + PLAYER_H and b[1] + bh > player_y):
                    running = False  # Game Over, will transition to game_over state
                    if pg.mixer: # Pause music if mixer is available
                        pg.mixer.music.pause()
                    if crash_sound: # Play crash sound if loaded successfully
                        crash_sound.play()

            # Drawing
            glClear(GL_COLOR_BUFFER_BIT)
            draw_street_background()
            # Draw player as a car
            draw_car(player_x, player_y, player_w, PLAYER_H)
            # Draw obstacles
            for b in blocks:
                if b[2] == 'taxi':
                    # Make obstacles cars taller and narrower
                    bw = BLOCK_W * 0.9
                    bh = BLOCK_H * 1.2
                    car_colors = [
                        (0.1, 0.4, 0.8),  # blue
                        (0.1, 0.7, 0.2),  # green
                        (0.8, 0.7, 0.1),  # yellow
                        (0.7, 0.1, 0.7),  # purple
                        (0.8, 0.4, 0.1),  # orange
                    ]
                    idx = int(abs(b[0]*1000)) % len(car_colors)
                    draw_car(b[0], b[1], bw, bh, car_colors[idx], flipped=True)
                else:
                    bw, bh = MOTO_W, MOTO_H
                    draw_motorcycle(b[0], b[1], bw, bh)
            # Draw timer
            elapsed_sec_timer = (pg.time.get_ticks() - start_ticks) / 1000.0 # Use a different var name for clarity
            draw_timer(elapsed_sec_timer, WINDOW_W, WINDOW_H)
            pg.display.flip()
            clock.tick(60)
            if running: # Only increment score if game is still running
                score += 1
        
        elif game_state == "game_over":
            # Ensure 2D projection is set for text drawing
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            draw_text("Game Over!", WINDOW_W / 2, WINDOW_H / 3, 50, (255, 0, 0))
            draw_text(f"Your Score: {score}", WINDOW_W / 2, WINDOW_H / 2, 40, (255, 255, 255))
            draw_text("Press R to Restart or Q to Quit", WINDOW_W / 2, WINDOW_H * 2/3, 30, (255, 255, 255))
            pg.display.flip()

            for event in pg.event.get():
                if event.type == QUIT:
                    pg.quit()
                    return
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_q:
                        pg.quit()
                        return
                    if event.key == pg.K_r:
                        game_state = "start_menu" # Go back to start menu

    # This part is now unreachable due to the main loop structure, can be removed or kept for clarity
    # print(f"Game Over! Your score: {score}") 
    # pg.quit() 

# Helper function to draw text (similar to draw_timer but more generic)
def draw_text(text, x, y, size, color, font_name="Arial", bold=True, align_center=True):
    font = pg.font.SysFont(font_name, size, bold=bold)
    text_surf = font.render(text, True, color)
    text_data = pg.image.tostring(text_surf, "RGBA", True)
    tw, th = text_surf.get_size()
    
    if align_center:
        text_x = x - tw / 2
        text_y = y - th / 2 # Center vertically as well
    else:
        text_x = x
        text_y = y


    # Set up OpenGL for 2D overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_W, WINDOW_H, 0, -1, 1) # Match draw_timer projection
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glRasterPos2f(text_x, text_y) # Use text_y for vertical positioning
    glDrawPixels(tw, th, GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    glDisable(GL_BLEND)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


if __name__ == "__main__":
    main()
