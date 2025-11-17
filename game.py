#!/usr/bin/env python3
# game.py - Simple Soul Knight-like game using Pygame

import pygame
import sys
import math
import random
import os

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 10
ENEMY_SPEED = 2
PLAYER_SIZE = 20
ENEMY_SIZE = 15
BULLET_SIZE = 5
COIN_SIZE = 8
POWERUP_SIZE = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
DARK_BLUE = (20, 20, 50)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Soul Knight Clone")
clock = pygame.time.Clock()

# Classes
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 100
        self.max_health = 100
        self.speed = PLAYER_SPEED
        self.weapon = 0  # 0: pistol, 1: shotgun, 2: machine gun, 3: sniper
        self.sword_cooldown = 2000  # ms
        self.last_sword_time = 0

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed

        # Keep in bounds
        self.x = max(0, min(SCREEN_WIDTH - PLAYER_SIZE, self.x))
        self.y = max(0, min(SCREEN_HEIGHT - PLAYER_SIZE, self.y))

    def draw(self, screen):
        pygame.draw.circle(screen, BLUE, (int(self.x + PLAYER_SIZE//2), int(self.y + PLAYER_SIZE//2)), PLAYER_SIZE//2)

class Enemy:
    def __init__(self, x, y, enemy_type=0):
        self.x = x
        self.y = y
        self.type = enemy_type
        if self.type == 0:  # normal
            self.speed = ENEMY_SPEED
            self.color = RED
            self.size = ENEMY_SIZE
            self.health = 1
        elif self.type == 1:  # fast
            self.speed = ENEMY_SPEED * 1.5
            self.color = (255, 100, 100)
            self.size = ENEMY_SIZE - 3
            self.health = 1
        elif self.type == 2:  # slow but big
            self.speed = ENEMY_SPEED * 0.7
            self.color = GREEN
            self.size = ENEMY_SIZE + 5
            self.health = 2
        elif self.type == 3:  # armored
            self.speed = ENEMY_SPEED * 0.5
            self.color = (100, 100, 100)
            self.size = ENEMY_SIZE + 3
            self.health = 3
        elif self.type == 4:  # boss
            self.speed = ENEMY_SPEED * 0.3
            self.color = PURPLE
            self.size = ENEMY_SIZE + 10
            self.health = 10
        self.max_health = self.health

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x + self.size//2), int(self.y + self.size//2)), self.size//2)
        # Health bar
        bar_width = self.size
        bar_height = 5
        bar_x = self.x
        bar_y = self.y - 10
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, bar_width * (self.health / self.max_health), bar_height))

class Bullet:
    def __init__(self, x, y, target_x, target_y, damage=10):
        self.x = x
        self.y = y
        self.damage = damage
        dx = target_x - x
        dy = target_y - y
        dist = math.sqrt(dx**2 + dy**2)
        if dist > 0:
            self.dx = (dx / dist) * BULLET_SPEED
            self.dy = (dy / dist) * BULLET_SPEED
        else:
            self.dx = 0
            self.dy = 0

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), BULLET_SIZE)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, (int(self.x), int(self.y)), COIN_SIZE)

class PowerUp:
    def __init__(self, x, y, type_):
        self.x = x
        self.y = y
        self.type = type_  # 0: health, 1: speed
        self.color = GREEN if self.type == 0 else BLUE

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), POWERUP_SIZE)

class Particle:
    def __init__(self, x, y, dx, dy, color, lifetime):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.age += 1

    def draw(self, screen):
        if self.age < self.lifetime:
            alpha = 255 * (1 - self.age / self.lifetime)
            color = (self.color[0], self.color[1], self.color[2], int(alpha))
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 2)

class Room:
    def __init__(self, room_id, enemies=None, boss=False):
        self.id = room_id
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.enemies = enemies or []
        self.coins = []
        self.powerups = []
        self.doors = []  # list of (x, y, target_room_id)
        self.cleared = False
        self.boss = boss
        if room_id == 0:  # start room
            self.doors = [(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, 1)]
        elif room_id == 1:  # enemy room
            self.doors = [(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50, 2)]
        elif room_id == 2:  # boss room
            self.doors = []  # no doors, level end

class Level:
    def __init__(self, level_num):
        self.num = level_num
        self.rooms = []
        self.current_room_id = 0
        self.generate_level()

    def generate_level(self):
        # Simple fixed level
        room0 = Room(0)
        room1 = Room(1, enemies=[Enemy(random.randint(100,700), random.randint(100,500), random.choices([0,1,2,3], weights=[5,3,2,1])[0]) for _ in range(5)])
        room2 = Room(2, enemies=[Enemy(SCREEN_WIDTH//2, 100, 4)], boss=True)
        self.rooms = [room0, room1, room2]

# Main game function
def main():
    high_score_file = 'high_score.txt'
    if os.path.exists(high_score_file):
        with open(high_score_file, 'r') as f:
            high_score = int(f.read().strip())
    else:
        high_score = 0

    level = Level(1)
    current_room = level.rooms[level.current_room_id]
    enemies = current_room.enemies

    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    bullets = []
    coins = []
    powerups = []
    particles = []
    stars = [(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]
    score = 0
    running = True
    paused = False
    game_state = 'playing'  # playing, level_complete
    last_powerup_spawn = 0
    powerup_spawn_rate = 10000  # ms
    last_machine_gun_time = 0
    machine_gun_rate = 100  # ms

    while running:
        dt = clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    player.weapon = (player.weapon + 1) % 4  # switch weapon
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_e:
                    if current_time - player.last_sword_time > player.sword_cooldown:
                        player.last_sword_time = current_time
                        # Sword slash: damage enemies in front
                        slash_range = 50
                        slash_damage = 50
                        for enemy in enemies[:]:
                            dx = enemy.x + enemy.size//2 - (player.x + PLAYER_SIZE//2)
                            dy = enemy.y + enemy.size//2 - (player.y + PLAYER_SIZE//2)
                            dist = math.sqrt(dx**2 + dy**2)
                            if dist < slash_range:
                                enemy.health -= slash_damage
                                if enemy.health <= 0:
                                    enemies.remove(enemy)
                                    score += 10
                                    kills_this_wave += 1
                                    coins.append(Coin(enemy.x + enemy.size//2, enemy.y + enemy.size//2))
                                    if kills_this_wave >= 10:
                                        wave += 1
                                        kills_this_wave = 0
                                        enemy_spawn_rate = max(500, enemy_spawn_rate - 200)
                        # Add slash particles
                        for _ in range(10):
                            angle = random.uniform(0, 2*math.pi)
                            speed = random.uniform(1, 3)
                            particles.append(Particle(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, math.cos(angle)*speed, math.sin(angle)*speed, ORANGE, 30))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if player.weapon == 0:  # pistol
                        bullets.append(Bullet(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, mouse_x, mouse_y, 10))
                        # Add muzzle flash
                        for _ in range(5):
                            angle = random.uniform(0, 2*math.pi)
                            speed = random.uniform(0.5, 2)
                            particles.append(Particle(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, math.cos(angle)*speed, math.sin(angle)*speed, YELLOW, 20))
                    elif player.weapon == 1:  # shotgun
                        for angle in [-0.2, 0, 0.2]:
                            rad = math.atan2(mouse_y - (player.y + PLAYER_SIZE//2), mouse_x - (player.x + PLAYER_SIZE//2)) + angle
                            tx = player.x + PLAYER_SIZE//2 + math.cos(rad) * 100
                            ty = player.y + PLAYER_SIZE//2 + math.sin(rad) * 100
                            bullets.append(Bullet(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, tx, ty, 5))
                        # Add particles
                        for _ in range(10):
                            angle = random.uniform(0, 2*math.pi)
                            speed = random.uniform(1, 3)
                            particles.append(Particle(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, math.cos(angle)*speed, math.sin(angle)*speed, ORANGE, 30))
                    elif player.weapon == 2:  # machine gun
                        pass  # handled in update
                    elif player.weapon == 3:  # sniper
                        bullets.append(Bullet(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, mouse_x, mouse_y, 50))
                        # Add particles
                        for _ in range(3):
                            angle = random.uniform(0, 2*math.pi)
                            speed = random.uniform(0.5, 1.5)
                            particles.append(Particle(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, math.cos(angle)*speed, math.sin(angle)*speed, PURPLE, 40))

        if not paused and game_state == 'playing':
            # Keys
            keys = pygame.key.get_pressed()
            player.move(keys)

            # Spawn powerups
            if current_time - last_powerup_spawn > powerup_spawn_rate:
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                type_ = random.choice([0, 1])
                powerups.append(PowerUp(x, y, type_))
                last_powerup_spawn = current_time

            # Update enemies
            for enemy in enemies[:]:
                enemy.move_towards(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2)

                # Check collision with player
                if (enemy.x < player.x + PLAYER_SIZE and enemy.x + enemy.size > player.x and
                    enemy.y < player.y + PLAYER_SIZE and enemy.y + enemy.size > player.y):
                    player.health -= 10
                    enemies.remove(enemy)
                    if player.health <= 0:
                        running = False

            # Update bullets
            for bullet in bullets[:]:
                bullet.move()
                # Remove if off screen
                if (bullet.x < 0 or bullet.x > SCREEN_WIDTH or
                    bullet.y < 0 or bullet.y > SCREEN_HEIGHT):
                    bullets.remove(bullet)
                else:
                    # Check collision with enemies
                    for enemy in enemies[:]:
                        if (bullet.x - BULLET_SIZE < enemy.x + enemy.size and bullet.x + BULLET_SIZE > enemy.x and
                            bullet.y - BULLET_SIZE < enemy.y + enemy.size and bullet.y + BULLET_SIZE > enemy.y):
                            enemy.health -= bullet.damage
                            bullets.remove(bullet)
                            if enemy.health <= 0:
                                # explosion
                                num_particles = 20 if enemy.type == 4 else 10
                                for _ in range(num_particles):
                                    angle = random.uniform(0, 2*math.pi)
                                    speed = random.uniform(1, 4)
                                    particles.append(Particle(enemy.x + enemy.size//2, enemy.y + enemy.size//2, math.cos(angle)*speed, math.sin(angle)*speed, ORANGE, 40))
                                enemies.remove(enemy)
                                score += 10
                                # spawn coin
                                coins.append(Coin(enemy.x + enemy.size//2, enemy.y + enemy.size//2))
                            break

            # Machine gun
            if player.weapon == 2 and pygame.mouse.get_pressed()[0] and current_time - last_machine_gun_time > machine_gun_rate:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                bullets.append(Bullet(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, mouse_x, mouse_y, 5))
                last_machine_gun_time = current_time
                # Add particles
                for _ in range(3):
                    angle = random.uniform(0, 2*math.pi)
                    speed = random.uniform(0.5, 1.5)
                    particles.append(Particle(player.x + PLAYER_SIZE//2, player.y + PLAYER_SIZE//2, math.cos(angle)*speed, math.sin(angle)*speed, RED, 15))

            # Update coins
            for coin in coins[:]:
                if (coin.x - COIN_SIZE < player.x + PLAYER_SIZE and coin.x + COIN_SIZE > player.x and
                    coin.y - COIN_SIZE < player.y + PLAYER_SIZE and coin.y + COIN_SIZE > player.y):
                    coins.remove(coin)
                    score += 5

            # Update powerups
            for powerup in powerups[:]:
                if (powerup.x - POWERUP_SIZE < player.x + PLAYER_SIZE and powerup.x + POWERUP_SIZE > player.x and
                    powerup.y - POWERUP_SIZE < player.y + PLAYER_SIZE and powerup.y + POWERUP_SIZE > player.y):
                    if powerup.type == 0:
                        player.health = min(player.max_health, player.health + 20)
                    elif powerup.type == 1:
                        player.speed += 1
                    powerups.remove(powerup)

            # Check transition
            if current_room.cleared:
                for door_x, door_y, next_id in current_room.doors:
                    dx = player.x + PLAYER_SIZE//2 - door_x
                    dy = player.y + PLAYER_SIZE//2 - door_y
                    if math.sqrt(dx**2 + dy**2) < 50:
                        level.current_room_id = next_id
                        current_room = level.rooms[next_id]
                        enemies = current_room.enemies
                        player.x = SCREEN_WIDTH//2
                        player.y = SCREEN_HEIGHT//2
                        break
            else:
                # Check room clear
                if not enemies:
                    current_room.cleared = True
                    if current_room.boss:
                        game_state = 'level_complete'


            # Update particles
            for particle in particles[:]:
                particle.update()
                if particle.age > particle.lifetime:
                    particles.remove(particle)

        # Draw
        screen.fill(DARK_BLUE)
        for star in stars:
            pygame.draw.circle(screen, WHITE, star, 1)
        player.draw(screen)
        for door_x, door_y, _ in current_room.doors:
            color = GREEN if current_room.cleared else RED
            pygame.draw.circle(screen, color, (door_x, door_y), 20)
        for enemy in enemies:
            enemy.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for coin in coins:
            coin.draw(screen)
        for powerup in powerups:
            powerup.draw(screen)
        for particle in particles:
            particle.draw(screen)

        # UI
        font = pygame.font.SysFont(None, 24)
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        score_text = font.render(f"Score: {score}", True, WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)
        level_text = font.render(f"Level: {level.num}", True, WHITE)
        room_text = font.render(f"Room: {current_room.id}", True, WHITE)
        weapon_names = ['Pistol', 'Shotgun', 'Machine Gun', 'Sniper']
        weapon_text = font.render(f"Weapon: {weapon_names[player.weapon]}", True, WHITE)
        speed_text = font.render(f"Speed: {player.speed}", True, WHITE)
        screen.blit(health_text, (10, 10))
        screen.blit(score_text, (10, 40))
        screen.blit(high_score_text, (10, 160))
        screen.blit(level_text, (10, 70))
        screen.blit(room_text, (10, 100))
        screen.blit(weapon_text, (10, 130))
        screen.blit(speed_text, (10, 190))

        if paused:
            pause_font = pygame.font.SysFont(None, 48)
            pause_text = pause_font.render("Paused - Press P to Resume", True, WHITE)
            screen.blit(pause_text, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 - 24))
        elif game_state == 'level_complete':
            complete_font = pygame.font.SysFont(None, 48)
            complete_text = complete_font.render("Level Complete!", True, GREEN)
            screen.blit(complete_text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2 - 24))

        pygame.display.flip()

        if game_state == 'level_complete':
            pygame.time.wait(2000)
            # Next level
            level = Level(level.num + 1)
            current_room = level.rooms[0]
            enemies = current_room.enemies
            game_state = 'playing'
            player.x = SCREEN_WIDTH//2
            player.y = SCREEN_HEIGHT//2

    # Game over
    if score > high_score:
        high_score = score
        with open(high_score_file, 'w') as f:
            f.write(str(high_score))
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 48)
    game_over_text = font.render("Game Over", True, RED)
    final_score_text = font.render(f"Final Score: {score} (High: {high_score})", True, WHITE)
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
    screen.blit(final_score_text, (SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2))
    pygame.display.flip()
    pygame.time.wait(3000)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
