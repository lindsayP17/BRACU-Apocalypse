from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import sys
import random

WIDTH, HEIGHT = 800, 600
FOV = 60
MOVEMENT_SPEED = 0.05
ROTATION_SPEED = 0.002
ENEMY_HEIGHT = 0.8
PLAYER_HEIGHT = ENEMY_HEIGHT * 0.9
DOOR_THICKNESS = 0.1
BULLET_SPEED = 0.2
DAMAGE_COOLDOWN = 0.5
ENEMY_DAMAGE = 5
HEALTH_BONUS = 5  # 10% health bonus
BULLET_DAMAGE = {
    "human": 34,  
    "mini": 51    
}
ENEMY_POINTS = {
    "human": 5,
    "mini": 3
}
AMMO=30

player_pos = [1.5, 1.5]   #initial positon of the player
player_angle = 0.0
player_hp = 100
player_vertical_angle = 0.0
last_damage_time = 0  
hit_flash_timer = 0   
ammo = 30
weapon_pos = 0.0
shoot = False
keys = {
    b'w': False, b's': False, b'a': False, b'd': False
}
bullets = []
player_score = 0

bonus_triangles = []
max_triangles = random.randint(4, 5)  # Will spawn 4 or 5 triangles
triangles_spawned = 0

game_map = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,0,1,1,0,1],
    [1,0,1,0,2,0,0,1,0,1],
    [1,0,1,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,1,0,1],
    [1,0,1,1,1,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,1,0,1],
    [1,1,1,1,1,1,1,1,1,1]
]

visited_region = set()   #tracks if player visited a certain area
curr_area = (1, 1)

class Door:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.is_open = False
        self.timer = 0
    
    def update(self):
        if self.is_open and self.timer > 0:
            self.timer -= 1
            if self.timer == 0:
                self.is_open = False

doors = []
for x in range(len(game_map)):
    for y in range(len(game_map[0])):
        if game_map[x][y] == 2:
            doors.append(Door(x, y))

class Enemy:
    def __init__(self, x, y, enemy_type='human'):
        self.enemy_type = enemy_type
        self.pos = [x, y]
        self.health = 100
        self.speed = 0.01  #movement speed of enemy
        self.size = 0.3
        self.angle = 0
        self.color = [0.8, 0.2, 0.2] if enemy_type == 'human' else [0.2, 0.8, 0.2]
    
    def update(self, player_pos):    #basically updates and calculates position and distance of enemy
        dx = player_pos[0] - self.pos[0]
        dy = player_pos[1] - self.pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        self.angle = math.atan2(dy, dx)
        
        if dist > 0.5:
            self.pos[0] += (dx / dist) * self.speed
            self.pos[1] += (dy / dist) * self.speed
        
        #wall collisions
        map_x, map_y = int(self.pos[0]), int(self.pos[1])
        if game_map[map_x][map_y] == 1:
            self.pos[0] -= (dx / dist) * self.speed
            self.pos[1] -= (dy / dist) * self.speed
        elif game_map[map_x][map_y] == 2:
            for door in doors:
                if door.x == map_x and door.y == map_y and not door.is_open:
                    self.pos[0] -= (dx / dist) * self.speed
                    self.pos[1] -= (dy / dist) * self.speed

enemies = [
    Enemy(5.5, 5.5, "human"),      
    Enemy(3.5, 3.5, "slender")     
]

def spawn_bonus_triangle():
    global triangles_spawned
    if triangles_spawned >= max_triangles:
        return
    
    for i in range(10):  # Tries 10 times to find a valid position
        x = random.uniform(1, len(game_map)-1)
        y = random.uniform(1, len(game_map[0])-1)
        map_x, map_y = int(x), int(y)
        # Check distance from player
        if game_map[map_x][map_y] == 0:   # Only spawn on floor
            dist_to_player = math.sqrt((x-player_pos[0])**2 + (y-player_pos[1])**2)
            if dist_to_player > 3.0:  # Don't spawn too close
                bonus_triangles.append([x, y])
                triangles_spawned += 1
                break

def draw_bonus_triangles():
    glDisable(GL_LIGHTING)  
    for triangle in bonus_triangles[:]:
        x, y = triangle
        glColor3f(0.2, 0.2, 0.8)
        glBegin(GL_TRIANGLES)
        glVertex3f(x-0.2, y-0.2, 0)
        glVertex3f(x+0.2, y-0.2, 0)
        glVertex3f(x, y+0.2, 0)
        glEnd()
    glEnable(GL_LIGHTING)

def get_curr_area():
    region_x = int(player_pos[0]/3)
    region_y = int(player_pos[1]/3)
    return (region_x, region_y)

last_spawn_time = {} 
def spawn_enemies():
    global curr_area, enemies, last_spawn_time
    curr_time = glutGet(GLUT_ELAPSED_TIME)/1000 
    if len(enemies)>=10:  
        return
        
    new_area = get_curr_area()
    if (new_area != curr_area and 
        (new_area not in visited_region or 
         curr_time-last_spawn_time.get(new_area, 0)>60)):
        
        curr_area = new_area
        visited_region.add(curr_area)
        last_spawn_time[new_area] = curr_time
        
        spawn_count = random.randint(1, 2)
        for i in range(spawn_count):
            for j in range(10):
                x = random.uniform(curr_area[0]*3 + 0.5, curr_area[0]*3 + 2.5)
                y = random.uniform(curr_area[1]*3 + 0.5, curr_area[1]*3 + 2.5)
                map_x, map_y = int(x), int(y)
                
                if (game_map[map_x][map_y] == 0 and math.sqrt((x-player_pos[0])**2 + (y-player_pos[1])**2) > 2.0):
                    enemy_type = 'human' if random.random() < 0.7 else 'mini'
                    enemies.append(Enemy(x, y, enemy_type))
                    break

def init():
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glClearColor(0.05, 0.1, 0.1, 1.0)

def walls():
    glColor3f(0.5, 0.3, 0.3)
    for x in range(len(game_map)):
        for y in range(len(game_map[0])):
            if game_map[x][y] == 1:
                glPushMatrix()
                glTranslatef(x + 0.5, y + 0.5, 0.5)
                glScalef(1.0, 1.0, 1.0)
                glutSolidCube(1.0)
                glPopMatrix()
    
    glColor3f(0.4, 0.2, 0.1)
    for door in doors:
        glPushMatrix()
        if door.is_open:
            glTranslatef(door.x + 0.5, door.y + 0.1, 0.5)
            glScalef(1.0, DOOR_THICKNESS, 1.0)
        else:
            glTranslatef(door.x + 0.5, door.y + 0.5, 0.5)
            glScalef(1.0, 1.0, 1.0)
        glutSolidCube(1.0)
        glPopMatrix()

def floors():
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    for x in range(len(game_map)-1):
        for y in range(len(game_map[0])-1):
            if game_map[x][y] == 0 or game_map[x][y] == 2:
                glVertex3f(x+0.1, y+0.1, -0.1)
                glVertex3f(x+0.9, y+0.1, -0.1)
                glVertex3f(x+0.9, y+0.9, -0.1)
                glVertex3f(x+0.1, y+0.9, -0.1)
    glEnd()

def ceiling():
    glColor3f(0.2, 0.2, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 1.0)
    glVertex3f(len(game_map), 0, 1.0)
    glVertex3f(len(game_map), len(game_map[0]), 1.0)
    glVertex3f(0, len(game_map[0]), 1.0)
    glEnd()

def draw_mini_enemy(x, y, z, angle, size, color):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(math.degrees(angle)-90, 0, 0, 1)
    glColor3f(0.2, 0.2, 0.2)  
    glPushMatrix()
    glTranslatef(0, 0, size * 0.75)
    glScalef(size * 0.5, size * 0.3, size * 1.2)  
    glutSolidCube(1.0)
    glPopMatrix()
    
    
    glPushMatrix()
    glTranslatef(0, 0, size * 1.6)

    #neck 
    
    glColor3f(0.8, 0.6, 0.4)
    glPushMatrix()
    glScalef(size * 0.15, size * 0.15, size * 0.2)
    glutSolidCube(1.0)
    glPopMatrix()

    #head
    
    glColor3f(0.8, 0.6, 0.4)
    glutSolidSphere(size * 0.25, 16, 16)
    
    # Eyes
    glPushMatrix()
    glTranslatef(size * 0.1, size * 0.15, size * 0.15)
    glColor3f(1.0, 1.0, 1.0)
    glutSolidSphere(size * 0.05, 8, 8)
    glColor3f(0.0, 0.0, 0.0)
    glTranslatef(0, size * 0.02, size * 0.02)
    glutSolidSphere(size * 0.02, 8, 8)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.1, size * 0.15, size * 0.15)
    glColor3f(1.0, 1.0, 1.0)
    glutSolidSphere(size * 0.05, 8, 8)
    glColor3f(0.0, 0.0, 0.0)
    glTranslatef(0, size * 0.02, size * 0.02)
    glutSolidSphere(size * 0.02, 8, 8)
    glPopMatrix()
    glPopMatrix()
    
    # Arms with shoulders
    glColor3f(0.2, 0.2, 0.2)
    
    glPushMatrix()
    glTranslatef(size * 0.3, 0, size * 1.3)
    glutSolidSphere(size * 0.15, 8, 8)
    glRotatef(45, 0, 1, 0)
    glScalef(size * 0.2, size * 0.2, size * 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.3, 0, size * 1.3)
    glutSolidSphere(size * 0.15, 8, 8)
    glRotatef(-45, 0, 1, 0)
    glScalef(size * 0.2, size * 0.2, size * 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Legs
    glColor3f(0.1, 0.1, 0.1)
    
    glPushMatrix()
    glTranslatef(size * 0.2, 0, size * 0.6)
    glScalef(size * 0.25, size * 0.25, size * 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.2, 0, size * 0.6)
    glScalef(size * 0.25, size * 0.25, size * 0.6)
    glutSolidCube(1.0)
    glPopMatrix()
    # Right foot
    glColor3f(0.05, 0.05, 0.05)
    glPushMatrix()
    glTranslatef(size * 0.2, size * 0.1, 0)
    glScalef(size * 0.3, size * 0.4, size * 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    #Left foot
    glPushMatrix()
    glTranslatef(-size * 0.2, size * 0.1, 0)
    glScalef(size * 0.3, size * 0.4, size * 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()

def draw_human_enemy(x, y, z, angle, size, color): #Bigger one 
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(math.degrees(angle)-90, 0, 0, 1)
    # Body (slim and tall)
    glColor3f(color[0], color[1], color[2])
    glPushMatrix()
    glTranslatef(0, 0, size * 0.9)
    glScalef(size * 0.4, size * 0.2, size * 1.8)  # Tall body
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Head with facial features
    glPushMatrix()
    glTranslatef(0, 0, size * 1.8)
    
    # Head base
    glColor3f(min(1.0, color[0]+0.1), min(1.0, color[1]+0.1), min(1.0, color[2]+0.1))
    glutSolidSphere(size * 0.3, 16, 16)
    
    # Eyes
    glPushMatrix()
    glTranslatef(size * 0.1, size * 0.3, size * 0.1)  
    glColor3f(1, 1, 1)  
    glutSolidSphere(size * 0.08, 8, 8)
    glTranslatef(0, 0, size * 0.01)
    glColor3f(0, 0, 0)  
    glutSolidSphere(size * 0.04, 8, 8)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.1, size * 0.3, size * 0.1)  
    glColor3f(1, 1, 1) 
    glutSolidSphere(size * 0.08, 8, 8)
    glTranslatef(0, 0, size * 0.01)
    glColor3f(0, 0, 0) 
    glutSolidSphere(size * 0.04, 8, 8)
    glPopMatrix()
    
    # Nose (triangle) 
    glColor3f(0.8, 0.6, 0.4) 
    glBegin(GL_TRIANGLES)
    glVertex3f(0, size * 0.35, size * 0.1)    # Tip of nose 
    glVertex3f(-size * 0.05, size * 0.25, size * 0.15)  
    glVertex3f(size * 0.05, size * 0.25, size * 0.15)   
    glEnd()
    
    glPopMatrix()  
    
    # Arms 
    arm_length = size * 0.8
    glColor3f(color[0], color[1], color[2])
    
    # Right arm
    glPushMatrix()
    glTranslatef(size * 0.2, 0, size * 1.2)
    glRotatef(90, 0, 1, 0)  
    glRotatef(20, 1, 0, 0)   
    glScalef(size * 0.15, size * 0.1, arm_length)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Left arm
    glPushMatrix()
    glTranslatef(-size * 0.2, 0, size * 1.2)
    glRotatef(-90, 0, 1, 0)   
    glRotatef(-20, 1, 0, 0)  
    glScalef(size * 0.15, size * 0.1, arm_length)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Hands 
    glColor3f(min(1.0, color[0]+0.1), min(1.0, color[1]+0.1), min(1.0, color[2]+0.1))
    glPushMatrix()
    glTranslatef(0, size * 0.2, size * 1.5)  
    glutSolidSphere(size * 0.1, 8, 8)
    glPopMatrix()
    
    # Legs 
    glColor3f(max(0.0, color[0]-0.2), max(0.0, color[1]-0.2), max(0.0, color[2]-0.2))
    glPushMatrix()
    glTranslatef(size * 0.1, 0, size * 0.4)
    glScalef(size * 0.12, size * 0.12, size * 1.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.1, 0, size * 0.4)
    glScalef(size * 0.12, size * 0.12, size * 1.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Feet (simple cubes)
    glPushMatrix()
    glTranslatef(size * 0.1, 0, 0)
    glScalef(size * 0.15, size * 0.2, size * 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-size * 0.1, 0, 0)
    glScalef(size * 0.15, size * 0.2, size * 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()  # End enemy

def draw_enemies():
    for enemy in enemies:
        pulse = 0.1 * math.sin(glutGet(GLUT_ELAPSED_TIME) * 0.005)
        color_asp = [min(1.0, enemy.color[0] + pulse), min(1.0, enemy.color[1] + pulse), min(1.0, enemy.color[2] + pulse)]
        if enemy.enemy_type == 'human':
            draw_human_enemy(enemy.pos[0], enemy.pos[1], 0, enemy.angle, enemy.size, color_asp)
        else:
            draw_mini_enemy(enemy.pos[0], enemy.pos[1], 0, enemy.angle, enemy.size, color_asp)
def draw_weapon():
    global weapon_pos
    
    glPushMatrix()
    glTranslatef(0.3, -0.5, -0.2 + weapon_pos * 0.1)
    glColor3f(0.7, 0.7, 0.7)
    
    glPushMatrix()
    glScalef(0.5, 0.1, 0.1)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.1, 0, 0)
    glScalef(0.2, 0.3, 0.2)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()

def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIDTH, HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_LIGHTING)
    
    health_bar_width = 200
    health_bar_height = 20
    health_bar_x = (WIDTH - health_bar_width) // 2
    health_bar_y = 20
    
    health_percent = player_hp / 100.0
    health_width = health_percent * health_bar_width
    
    red_intensity = health_percent
    glColor3f(red_intensity, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(health_bar_x, health_bar_y)
    glVertex2f(health_bar_x + health_width, health_bar_y)
    glVertex2f(health_bar_x + health_width, health_bar_y + health_bar_height)
    glVertex2f(health_bar_x, health_bar_y + health_bar_height)
    glEnd()
    
    glColor3f(1, 1, 1)
    glRasterPos2f(health_bar_x + health_bar_width + 10, health_bar_y + health_bar_height//2 + 4)
    health_text = f"{player_hp}%".encode('ascii')
    for char in health_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
    
    glEnable(GL_LIGHTING)
    
    glColor3f(1.0, 0.0, 1.0)
    glRasterPos2f(20, 30)
    score_text = f"Score: {player_score}".encode('ascii')
    for char in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, char)
    
    glColor3f(1, 1, 1)
    glRasterPos2f(WIDTH - 100, 30)
    ammo_counter = f"Ammo: {ammo}".encode('ascii')
    for char in ammo_counter:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, char)
    
    glRasterPos2f(20, 60)
    enemy_counter = f"Enemies: {len(enemies)}".encode('ascii')
    for char in enemy_counter:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, char)
    
    glBegin(GL_LINES)
    glVertex2f(WIDTH//2 - 10, HEIGHT//2)
    glVertex2f(WIDTH//2 + 10, HEIGHT//2)
    glVertex2f(WIDTH//2, HEIGHT//2 - 10)
    glVertex2f(WIDTH//2, HEIGHT//2 + 10)
    glEnd()
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
class Bullet:
    def __init__(self, pos, angle, vertical_angle):
        self.pos = list(pos)
        self.angle = angle
        self.vertical_angle = vertical_angle
        self.pos[2] = PLAYER_HEIGHT
        
        self.direction_x = math.cos(angle) * math.cos(vertical_angle)
        self.direction_y = math.sin(angle) * math.cos(vertical_angle)
        self.direction_z = math.sin(vertical_angle)
        
        length = math.sqrt(self.direction_x**2 + self.direction_y**2 + self.direction_z**2)
        self.direction_x /= length
        self.direction_y /= length
        self.direction_z /= length

    def update(self):
        self.pos[0] += self.direction_x * BULLET_SPEED
        self.pos[1] += self.direction_y * BULLET_SPEED
        self.pos[2] += self.direction_z * BULLET_SPEED
        
        map_x, map_y = int(self.pos[0]),int(self.pos[1])
        if map_x < 0 or map_x >= len(game_map) or map_y < 0 or map_y >= len(game_map[0]):
            return True
        if game_map[map_x][map_y] == 1:
            return True
            
            
        for enemy in enemies[:]:
            dx = enemy.pos[0] - self.pos[0]
            dy = enemy.pos[1] - self.pos[1]
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > enemy.size * 1.2: 
                continue
            bullet_height = self.pos[2]
            if bullet_height >= ENEMY_HEIGHT * 0.8:
                damage = BULLET_DAMAGE.get(enemy.enemy_type, 34) *  2  
            elif bullet_height >= ENEMY_HEIGHT * 0.4:
                damage = BULLET_DAMAGE.get(enemy.enemy_type, 34)
            elif bullet_height >= 0:
                damage = BULLET_DAMAGE.get(enemy.enemy_type, 34) * 0.7
            else:
                continue
            
            enemy.health -= damage

            if enemy.health <= 0:
                global player_score
                points = ENEMY_POINTS.get(enemy.enemy_type, 5)
                if bullet_height >= ENEMY_HEIGHT * 0.8:
                    points *= 2
                player_score += points
                enemies.remove(enemy)
            return True
        
        return False
    def draw(self):
        glColor3f(1.0, 0.8, 0.0)
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glutSolidSphere(0.05, 8, 8) 
        glPopMatrix()

def display():
    global hit_flash_timer  
    
    if hit_flash_timer > 0:
        glClearColor(0.8, 0.1, 0.1, 1.0) # Red flash color
        hit_flash_timer -= 1
    else:
        glClearColor(0.05, 0.1, 0.1, 1.0)  # Normal bg color
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    look_x = player_pos[0] + math.cos(player_angle)
    look_y = player_pos[1] + math.sin(player_angle)
    look_z = PLAYER_HEIGHT + math.sin(player_vertical_angle)

    gluLookAt(
        player_pos[0], player_pos[1], PLAYER_HEIGHT,
        look_x, look_y, look_z,
        0, 0, 1
    )
    
    floors()
    ceiling()
    walls()
    draw_bonus_triangles() 
    draw_enemies()
    for bullet in bullets:
        bullet.draw()
    draw_weapon()
    draw_hud()
    
    glutSwapBuffers()

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(FOV, w/h, 0.1, 50.0)
    glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    global keys, ammo
    keys[key] = True
    if key == b'r':
        ammo = AMMO
    if key == b' ' and not shoot:
        for door in doors:
            dist = math.sqrt((player_pos[0]-door.x)**2 + (player_pos[1]-door.y)**2)
            if dist < 1.5:
                door.is_open = True
                door.timer = 100
                break
    
    if key == b'\x1b':
        glutLeaveMainLoop()

def keyboard_up(key, x, y):
    global keys
    keys[key] = False

def mouse_listener(x, y):
    global player_angle, player_vertical_angle
    player_angle -= (x - WIDTH//2)*ROTATION_SPEED
    player_vertical_angle -= (y - HEIGHT//2)*ROTATION_SPEED
    player_vertical_angle = max(-1.48, min(1.48, player_vertical_angle))
    glutWarpPointer(WIDTH//2, HEIGHT//2)

def mouse_button(button, state, x, y):
    global shoot, ammo
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and ammo > 0:
        shoot = True
        ammo -= 1
        bullets.append(Bullet(
            [player_pos[0], player_pos[1], PLAYER_HEIGHT],
            player_angle,
            player_vertical_angle
        ))

def update(value):
    global player_pos, weapon_pos, shoot, player_hp,last_damage_time, hit_flash_timer,bonus_triangles
    
    # Movement with collision detection
    move = [0, 0]
    if keys[b'w']:
        move[0] += math.cos(player_angle)
        move[1] += math.sin(player_angle)
    if keys[b's']:
        move[0] -= math.cos(player_angle)
        move[1] -= math.sin(player_angle)
    if keys[b'a']:
        move[0] -= math.cos(player_angle - math.pi/2)
        move[1] -= math.sin(player_angle - math.pi/2)
    if keys[b'd']:
        move[0] -= math.cos(player_angle + math.pi/2)
        move[1] -= math.sin(player_angle + math.pi/2)
    
    length = math.sqrt(move[0]**2 + move[1]**2)
    if length > 0:
        new_pos = [
            player_pos[0] + move[0]/length*MOVEMENT_SPEED,
            player_pos[1] + move[1]/length*MOVEMENT_SPEED
        ]
        
        if (0 < new_pos[0] < len(game_map)-1 and 
            0 < new_pos[1] < len(game_map[0])-1):
            
            cell_x, cell_y = int(new_pos[0]), int(new_pos[1])
            
            if (game_map[cell_x][cell_y] == 0 or 
                (game_map[cell_x][cell_y] == 2 and 
                 any(door.x == cell_x and door.y == cell_y and door.is_open for door in doors))):
                player_pos = new_pos

    # Check for bonus triangle collisions
    for triangle in bonus_triangles[:]:
        dx = player_pos[0] - triangle[0]
        dy = player_pos[1] - triangle[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.3: # Player touched the triangle
            player_hp = min(100, player_hp + HEALTH_BONUS)
            bonus_triangles.remove(triangle)
            
            if triangles_spawned < max_triangles:
                spawn_bonus_triangle()

    for door in doors:
        door.update()
    
    if shoot:
        weapon_pos += 0.1
        if weapon_pos >= 1:
            shoot = False
            weapon_pos = 0
    elif weapon_pos > 0:
        weapon_pos -= 0.05
    
    curr_time = glutGet(GLUT_ELAPSED_TIME) / 1000
    for enemy in enemies:
        enemy.update(player_pos)
        
        dx = player_pos[0] - enemy.pos[0]
        dy = player_pos[1] - enemy.pos[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < 0.5 and curr_time - last_damage_time > DAMAGE_COOLDOWN:
             player_hp -= ENEMY_DAMAGE
             hit_flash_timer = 10  
             last_damage_time = curr_time
             if player_hp <= 0:
                  print("Game Over! You died.")
                  glutLeaveMainLoop()
    
    spawn_enemies()    # Spawn enemies when entering new areas
    
    bullets[:] = [bullet for bullet in bullets if not bullet.update()] # Update bullets
    
    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIDTH, HEIGHT)
    glutCreateWindow(b"BRACU Apocalypse")
    
    init()
    
    spawn_bonus_triangle()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_listener)
    glutMouseFunc(mouse_button)
    glutTimerFunc(0, update, 0)
    
    glutSetCursor(GLUT_CURSOR_NONE)
    glutWarpPointer(WIDTH//2, HEIGHT//2)
    
    glutMainLoop()

if __name__ == "__main__":

    main()

