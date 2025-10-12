import pygame
import sys
import argparse
import os

# ========================
# CONFIGURAÇÕES DE TELA
# ========================
TILE_ORIGINAL_SIZE = 16
SCALE = 3
TILE_SIZE = TILE_ORIGINAL_SIZE * SCALE  # 48x48
MAX_SCREEN_COL = 16
MAX_SCREEN_ROW = 12
SCREEN_WIDTH = TILE_SIZE * MAX_SCREEN_COL  # 768px
SCREEN_HEIGHT = TILE_SIZE * MAX_SCREEN_ROW  # 576px

# ========================
# CONFIGURAÇÕES DE MUNDO
# ========================
MAX_WORLD_COL = 64
MAX_WORLD_ROW = 64
WORLD_WIDTH = TILE_SIZE * MAX_WORLD_COL
WORLD_HEIGHT = TILE_SIZE * MAX_WORLD_ROW

FPS = 60

# ========================
# CLASSE TILE
# ========================
class Tile:
    def __init__(self, image, collision=False):
        self.image = image
        self.collision = collision

# ========================
# CLASSE OBJETO (ÁRVORES, ETC)
# ========================
class GameObject:
    def __init__(self, image_path, world_x, world_y, width_tiles=1, height_tiles=1, collision=False):
        try:
            self.original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(
                self.original_image,
                (width_tiles * TILE_SIZE, height_tiles * TILE_SIZE)
            )
            self.world_x = world_x
            self.world_y = world_y
            self.width_tiles = width_tiles
            self.height_tiles = height_tiles
            self.collision = collision
        except pygame.error as e:
            print(f"Erro ao carregar imagem {image_path}: {e}")
            self.image = pygame.Surface((width_tiles * TILE_SIZE, height_tiles * TILE_SIZE), pygame.SRCALPHA)
            self.image.fill((0, 0, 0, 0))
            if height_tiles > 1:
                crown = pygame.Surface((width_tiles * TILE_SIZE, (height_tiles - 1) * TILE_SIZE))
                crown.fill((34, 139, 34))
                self.image.blit(crown, (0, 0))
            trunk = pygame.Surface((TILE_SIZE, TILE_SIZE))
            trunk.fill((101, 67, 33))
            center_col = width_tiles // 2
            trunk_x = center_col * TILE_SIZE
            trunk_y = (height_tiles - 1) * TILE_SIZE
            self.image.blit(trunk, (trunk_x, trunk_y))

            self.world_x = world_x
            self.world_y = world_y
            self.width_tiles = width_tiles
            self.height_tiles = height_tiles
            self.collision = collision

        if self.collision:
            center_col = self.width_tiles // 2
            trunk_x_world = int(self.world_x + center_col * TILE_SIZE)
            trunk_y_world = int(self.world_y + (self.height_tiles - 1) * TILE_SIZE)
            self.collision_rect = pygame.Rect(
                trunk_x_world,
                trunk_y_world,
                TILE_SIZE,
                TILE_SIZE
            )
        else:
            self.collision_rect = None

    def update_collision_rect(self):
        if self.collision and self.collision_rect:
            center_col = self.width_tiles // 2
            self.collision_rect.x = int(self.world_x + center_col * TILE_SIZE)
            self.collision_rect.y = int(self.world_y + (self.height_tiles - 1) * TILE_SIZE)
            self.collision_rect.width = TILE_SIZE
            self.collision_rect.height = TILE_SIZE

    @property
    def bottom_y(self):
        return self.world_y + self.height_tiles * TILE_SIZE

    def draw(self, screen, camera_x, camera_y, debug=False):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y

        if (-self.width_tiles * TILE_SIZE <= screen_x < SCREEN_WIDTH and
            -self.height_tiles * TILE_SIZE <= screen_y < SCREEN_HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))

            if debug and self.collision_rect:
                pygame.draw.rect(screen, (255, 0, 0), (
                    self.collision_rect.x - camera_x,
                    self.collision_rect.y - camera_y,
                    self.collision_rect.width,
                    self.collision_rect.height
                ), 1)

# ========================
# TILE MANAGER
# ========================
class TileManager:
    def __init__(self, tile_size, level):
        self.tile_size = tile_size
        self.tiles = []
        self.map_tile_num = []
        self.objects = []
        self.level = level

        self.load_tiles()
        self.load_map()
        self.load_objects()

    def get_map_path(self):
        maps = {
            1: "res/maps/map01.txt",
            2: "res/maps/map02.txt",
            3: "res/maps/map03.txt"
        }
        return maps.get(self.level, "res/maps/map01.txt")

    def load_tiles(self):
        try:
            grass_path = "res/tiles/grass.png"
            if os.path.exists(grass_path):
                grass = pygame.image.load(grass_path).convert_alpha()
            else:
                grass = self.create_placeholder_tile((100, 200, 100))
            grass = pygame.transform.scale(grass, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(grass))

            sand_path = "res/tiles/sand.png"
            if os.path.exists(sand_path):
                sand = pygame.image.load(sand_path).convert_alpha()
            else:
                sand = self.create_placeholder_tile((210, 180, 140))
            sand = pygame.transform.scale(sand, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(sand))

            water_path = "res/tiles/water.png"
            if os.path.exists(water_path):
                water = pygame.image.load(water_path).convert_alpha()
            else:
                water = self.create_placeholder_tile((0, 0, 255))
            water = pygame.transform.scale(water, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(water, collision=True))

        except Exception as e:
            print(f"Erro ao carregar tiles: {e}")

    def create_placeholder_tile(self, color):
        surface = pygame.Surface((16, 16))
        surface.fill(color)
        return surface

    def load_map(self):
        map_path = self.get_map_path()
        try:
            if os.path.exists(map_path):
                with open(map_path, "r") as file:
                    for line in file.readlines():
                        row = [int(x) for x in line.strip().split()]
                        self.map_tile_num.append(row)
            else:
                print(f"Mapa {map_path} não encontrado. Criando mapa padrão...")
                self.create_default_map()
        except Exception as e:
            print(f"Erro ao carregar mapa {map_path}: {e}")
            self.create_default_map()

    def create_default_map(self):
        self.map_tile_num = []
        for row in range(MAX_WORLD_ROW):
            current_row = []
            for col in range(MAX_WORLD_COL):
                current_row.append(0)
            self.map_tile_num.append(current_row)

    def load_objects(self):
        try:
            tree_path = "res/objects/tree.png"

            if self.level == 1:
                objects_data = [
                    (5, 5, 3, 5), (15, 10, 3, 5), (25, 15, 3, 5),
                    (35, 20, 3, 5), (45, 25, 3, 5), (55, 30, 3, 5),
                    (10, 35, 3, 5), (20, 40, 3, 5), (30, 45, 3, 5),
                    (40, 50, 3, 5), (50, 55, 3, 5)
                ]
            elif self.level == 2:
                objects_data = [
                    (8, 8, 3, 5), (12, 12, 3, 5), (16, 16, 3, 5),
                    (20, 20, 3, 5), (24, 24, 3, 5), (28, 28, 3, 5),
                    (32, 32, 3, 5), (36, 36, 3, 5), (40, 40, 3, 5),
                    (44, 44, 3, 5), (48, 48, 3, 5), (52, 52, 3, 5),
                    (56, 56, 3, 5), (15, 30, 3, 5), (30, 15, 3, 5)
                ]
            else:
                objects_data = [
                    (5, 5, 3, 5), (10, 10, 3, 5), (15, 15, 3, 5),
                    (20, 20, 3, 5), (25, 25, 3, 5), (30, 30, 3, 5),
                    (35, 35, 3, 5), (40, 40, 3, 5), (45, 45, 3, 5),
                    (50, 50, 3, 5), (55, 55, 3, 5), (60, 60, 3, 5),
                    (8, 20, 3, 5), (12, 25, 3, 5), (18, 30, 3, 5),
                    (22, 35, 3, 5), (28, 40, 3, 5), (32, 45, 3, 5),
                    (38, 50, 3, 5), (42, 55, 3, 5)
                ]

            for data in objects_data:
                x, y, width, height = data
                tree = GameObject(
                    tree_path,
                    world_x=x * TILE_SIZE,
                    world_y=y * TILE_SIZE,
                    width_tiles=width,
                    height_tiles=height,
                    collision=True
                )
                tree.update_collision_rect()
                self.objects.append(tree)

        except Exception as e:
            print(f"Erro ao carregar objetos: {e}")

    def get_obstacles(self):
        rects = []
        for obj in self.objects:
            if obj.collision and obj.collision_rect:
                rects.append(obj.collision_rect.copy())
        return rects

    def draw_ground(self, screen, camera_x, camera_y):
        for row_index, row in enumerate(self.map_tile_num):
            for col_index, tile_index in enumerate(row):
                world_x = col_index * self.tile_size
                world_y = row_index * self.tile_size
                screen_x = world_x - camera_x
                screen_y = world_y - camera_y

                if (-self.tile_size <= screen_x < SCREEN_WIDTH and
                    -self.tile_size <= screen_y < SCREEN_HEIGHT):
                    screen.blit(self.tiles[tile_index].image, (screen_x, screen_y))

    def draw_objects(self, screen, camera_x, camera_y):
        for obj in self.objects:
            obj.draw(screen, camera_x, camera_y)

# ========================
# ENTITY BASE
# ========================
class Entity:
    def __init__(self):
        self.world_x = 0
        self.world_y = 0
        self.speed = 4
        self.direction = "down"
        self.sprite_counter = 0
        self.sprite_num = 1

# ========================
# PLAYER
# ========================
class Player(Entity):
    def __init__(self, game, skin_index=0):
        super().__init__()
        self.game = game
        self.world_x = TILE_SIZE * 20
        self.world_y = TILE_SIZE * 20
        self.skin_index = skin_index
        self.images = self.load_images()
        self.collected_items = 0
        self.max_items = 10
        self.width = TILE_SIZE
        self.height = TILE_SIZE

    def load_images(self):
        images = {"up": [], "down": [], "left": [], "right": []}

        try:
            folder = "res/player/"

            images["up"].append(self.load_and_scale_image(folder + "PlayerUp1.png"))
            images["up"].append(self.load_and_scale_image(folder + "PlayerUp2.png"))

            images["down"].append(self.load_and_scale_image(folder + "PlayerDown1.png"))
            images["down"].append(self.load_and_scale_image(folder + "PlayerDown2.png"))

            images["left"].append(self.load_and_scale_image(folder + "PlayerLeft1.png"))
            images["left"].append(self.load_and_scale_image(folder + "PlayerLeft2.png"))

            images["right"].append(self.load_and_scale_image(folder + "PlayerRight1.png"))
            images["right"].append(self.load_and_scale_image(folder + "PlayerRight2.png"))

        except Exception as e:
            print(f"Erro ao carregar imagens do player: {e}")
            images = self.create_fallback_sprites()

        return images

    def load_and_scale_image(self, path):
        if os.path.exists(path):
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        else:
            print(f"Imagem não encontrada: {path}")
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][self.skin_index % 4]
            pygame.draw.rect(surf, color, (0, 0, TILE_SIZE, TILE_SIZE))
            return surf

    def create_fallback_sprites(self):
        skin_colors = [
            [(255, 0, 0), (200, 0, 0)],
            [(0, 255, 0), (0, 200, 0)],
            [(0, 0, 255), (0, 0, 200)],
            [(255, 255, 0), (200, 200, 0)]
        ]

        base_color, dark_color = skin_colors[self.skin_index % len(skin_colors)]

        images = {"up": [], "down": [], "left": [], "right": []}
        size = TILE_SIZE

        for direction in images.keys():
            surf1 = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf1, base_color, (0, 0, size, size))
            pygame.draw.circle(surf1, (255, 255, 255), (size//2, size//3), size//6)
            images[direction].append(surf1)

            surf2 = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf2, dark_color, (0, 0, size, size))
            pygame.draw.circle(surf2, (255, 255, 255), (size//2, size//3), size//6)
            images[direction].append(surf2)

        return images

    def get_player_rect_at(self, x, y):
        return pygame.Rect(int(x), int(y), self.width, self.height)

    def check_collision(self, new_x, new_y, tile_manager):
        player_rect = self.get_player_rect_at(new_x, new_y)

        tile_x1 = int(new_x / TILE_SIZE)
        tile_y1 = int(new_y / TILE_SIZE)
        tile_x2 = int((new_x + TILE_SIZE - 1) / TILE_SIZE)
        tile_y2 = int((new_y + TILE_SIZE - 1) / TILE_SIZE)

        for y in range(tile_y1, tile_y2 + 1):
            for x in range(tile_x1, tile_x2 + 1):
                if 0 <= y < len(tile_manager.map_tile_num) and 0 <= x < len(tile_manager.map_tile_num[0]):
                    tile_index = tile_manager.map_tile_num[y][x]
                    if tile_manager.tiles[tile_index].collision:
                        print(f"Colisão com tile em ({x}, {y}) - tipo {tile_index}")
                        return True

        for obj in tile_manager.objects:
            if obj.collision and obj.collision_rect:
                if player_rect.colliderect(obj.collision_rect):
                    print(f"Colisão com objeto (tronco) em ({obj.world_x}, {obj.world_y})")
                    return True

        return False

    def update(self, keys, tile_manager):
        moved = False
        new_x, new_y = self.world_x, self.world_y

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction = "up"
            new_y -= self.speed
            moved = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction = "down"
            new_y += self.speed
            moved = True
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction = "left"
            new_x -= self.speed
            moved = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction = "right"
            new_x += self.speed
            moved = True

        if moved:
            print(f"Tentando mover para: ({new_x}, {new_y})")

        if not self.check_collision(new_x, new_y, tile_manager):
            self.world_x = new_x
            self.world_y = new_y
            self.world_x = max(0, min(self.world_x, WORLD_WIDTH - TILE_SIZE))
            self.world_y = max(0, min(self.world_y, WORLD_HEIGHT - TILE_SIZE))

            if moved:
                print(f"Movido para: ({self.world_x}, {self.world_y})")
        else:
            if moved:
                print("Movimento bloqueado por colisão!")

        if moved:
            self.sprite_counter += 1
            if self.sprite_counter > 7:
                self.sprite_num = 1 if self.sprite_num == 2 else 2
                self.sprite_counter = 0

    @property
    def bottom_y(self):
        return self.world_y + TILE_SIZE

    def draw(self, surface, camera_x, camera_y):
        img_list = self.images[self.direction]
        image = img_list[self.sprite_num - 1]
        screen_x = SCREEN_WIDTH // 2 - TILE_SIZE // 2
        screen_y = SCREEN_HEIGHT // 2 - TILE_SIZE // 2
        surface.blit(image, (screen_x, screen_y))

# ========================
# ITEM PARA COLETAR
# ========================
class Collectible:
    def __init__(self, x, y):
        self.world_x = x * TILE_SIZE
        self.world_y = y * TILE_SIZE
        self.collected = False
        self.size = TILE_SIZE // 2
        self.color = (255, 215, 0)

    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            screen_x = self.world_x - camera_x + TILE_SIZE // 4
            screen_y = self.world_y - camera_y + TILE_SIZE // 4
            pygame.draw.circle(screen, self.color, (screen_x, screen_y), self.size // 2)

    def check_collision(self, player_x, player_y):
        if self.collected:
            return False

        player_rect = pygame.Rect(player_x, player_y, TILE_SIZE, TILE_SIZE)
        item_rect = pygame.Rect(self.world_x + TILE_SIZE // 4, self.world_y + TILE_SIZE // 4,
                              self.size, self.size)
        return player_rect.colliderect(item_rect)

# ========================
# GAME
# ========================
class Game:
    def __init__(self, nickname, skin_index, level):
        self.nickname = nickname
        self.skin_index = skin_index
        self.level = level

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(f"2D Game - {nickname} - Nível {level}")
        self.clock = pygame.time.Clock()

        self.tile_size = TILE_SIZE
        self.player = Player(self, skin_index)
        self.tile_manager = TileManager(TILE_SIZE, level)

        self.camera_x = 0
        self.camera_y = 0

        self.collectibles = self.generate_collectibles()
        self.score = 0
        self.max_score = 200
        self.start_time = pygame.time.get_ticks()
        self.game_duration = 600000
        self.game_over = False
        self.level_completed = False

        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.debug_draw_collision = False

        print(f"Player iniciado em: ({self.player.world_x}, {self.player.world_y})")

    def generate_collectibles(self):
        collectibles = []
        if self.level == 1:
            positions = [
                (15, 35), (25, 40), (35, 45), (45, 30), (55, 35),
                (30, 50), (40, 25), (50, 40), (60, 45), (35, 30)
            ]
        elif self.level == 2:
            positions = [(12, 32), (22, 42), (32, 52), (42, 32), (52, 42),
                        (18, 38), (28, 28), (38, 48), (48, 38), (58, 48)]
        else:
            positions = [(10, 30), (20, 40), (30, 50), (40, 30), (50, 40),
                        (15, 35), (25, 25), (35, 45), (45, 35), (55, 45)]

        for pos in positions:
            collectibles.append(Collectible(pos[0], pos[1]))

        return collectibles

    def update_camera(self):
        target_x = self.player.world_x - SCREEN_WIDTH // 2 + TILE_SIZE // 2
        target_y = self.player.world_y - SCREEN_HEIGHT // 2 + TILE_SIZE // 2

        self.camera_x = max(0, min(target_x, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, WORLD_HEIGHT - SCREEN_HEIGHT))

    def check_collectibles(self):
        for collectible in self.collectibles:
            if collectible.check_collision(self.player.world_x, self.player.world_y):
                if not collectible.collected:
                    collectible.collected = True
                    self.player.collected_items += 1
                    self.score += 20
                    print(f"Item coletado! Total: {self.player.collected_items}")

                    if self.player.collected_items >= self.player.max_items:
                        self.level_completed = True
                        print("Nível completado!")

    def draw_hud(self):
        time_left = max(0, self.game_duration - (pygame.time.get_ticks() - self.start_time))
        minutes = time_left // 60000
        seconds = (time_left % 60000) // 1000

        time_text = self.font.render(f"Tempo: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        score_text = self.font.render(f"Pontuação: {self.score}/{self.max_score}", True, (255, 255, 255))
        items_text = self.font.render(f"Itens: {self.player.collected_items}/{self.player.max_items}", True, (255, 255, 255))
        level_text = self.font.render(f"Nível: {self.level}", True, (255, 255, 255))
        player_text = self.font.render(f"Jogador: {self.nickname}", True, (255, 255, 255))

        self.screen.blit(time_text, (10, 10))
        self.screen.blit(score_text, (10, 50))
        self.screen.blit(items_text, (10, 90))
        self.screen.blit(level_text, (10, 130))
        self.screen.blit(player_text, (10, 170))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font.render("TEMPO ESGOTADO!", True, (255, 0, 0))
        restart_text = self.small_font.render("Pressione ESC para sair", True, (255, 255, 255))

        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))

    def draw_level_complete(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        complete_text = self.font.render("NÍVEL CONCLUÍDO!", True, (0, 255, 0))
        score_text = self.font.render(f"Pontuação: {self.score}/{self.max_score}", True, (255, 255, 255))
        continue_text = self.small_font.render("Pressione ESC para continuar", True, (255, 255, 255))

        self.screen.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
        self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
        self.screen.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

    def run(self):
        running = True

        while running:
            current_time = pygame.time.get_ticks()
            time_elapsed = current_time - self.start_time

            if time_elapsed >= self.game_duration and not self.level_completed:
                self.game_over = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        self.debug_draw_collision = not self.debug_draw_collision

            if not self.game_over and not self.level_completed:
                keys = pygame.key.get_pressed()
                self.player.update(keys, self.tile_manager)
                self.update_camera()
                self.check_collectibles()

            self.screen.fill((0, 0, 0))

            self.tile_manager.draw_ground(self.screen, self.camera_x, self.camera_y)

            for collectible in self.collectibles:
                collectible.draw(self.screen, self.camera_x, self.camera_y)

            drawables = []
            for obj in self.tile_manager.objects:
                obj.update_collision_rect()
                drawables.append(obj)
            drawables.append(self.player)

            def get_bottom(o):
                if hasattr(o, "bottom_y"):
                    return o.bottom_y
                return getattr(o, "world_y", 0) + TILE_SIZE

            drawables.sort(key=get_bottom)

            for d in drawables:
                if isinstance(d, GameObject):
                    d.draw(self.screen, self.camera_x, self.camera_y, debug=self.debug_draw_collision)
                elif isinstance(d, Player):
                    d.draw(self.screen, self.camera_x, self.camera_y)

            self.draw_hud()

            if self.game_over:
                self.draw_game_over()
            elif self.level_completed:
                self.draw_level_complete()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

        success = self.level_completed and self.score >= 140
        print(f"\n=== RESULTADO ===")
        print(f"Jogador: {self.nickname}")
        print(f"Nível: {self.level}")
        print(f"Pontuação: {self.score}/{self.max_score}")
        print(f"Itens coletados: {self.player.collected_items}/{self.player.max_items}")
        print(f"Status: {'APROVADO' if success else 'REPROVADO'}")

        return success

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nickname', required=True)
    parser.add_argument('--skin', type=int, required=True)
    parser.add_argument('--level', type=int, required=True)

    args = parser.parse_args()

    print("=== INICIANDO JOGO 2D COM TILES ===")
    print(f"Jogador: {args.nickname}")
    print(f"Skin: {args.skin}")
    print(f"Nível: {args.level}")

    game = Game(args.nickname, args.skin, args.level)
    success = game.run()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()