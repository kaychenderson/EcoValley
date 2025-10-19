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
            # Redimensiona baseado no número de tiles que ocupa
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
            # Criar uma imagem placeholder se o arquivo não existir
            self.image = pygame.Surface((width_tiles * TILE_SIZE, height_tiles * TILE_SIZE), pygame.SRCALPHA)
            # Placeholder simples (copa + tronco central)
            self.image.fill((0, 0, 0, 0))
            # Desenhar copa ocupando as (height_tiles - 1) linhas superiores e todas as colunas
            if height_tiles > 1:
                crown = pygame.Surface((width_tiles * TILE_SIZE, (height_tiles - 1) * TILE_SIZE))
                crown.fill((34, 139, 34))
                self.image.blit(crown, (0, 0))
            # Desenhar tronco apenas no tile central da base (1 tile de largura)
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

        # Criar rect de colisão **apenas no tronco central da base**
        # Tronco fica na coluna central (largura = 1 tile) e na última linha (altura = 1 tile)
        if self.collision:
            center_col = self.width_tiles // 2
            trunk_x_world = int(self.world_x + center_col * TILE_SIZE)
            trunk_y_world = int(self.world_y + (self.height_tiles - 1) * TILE_SIZE)
            self.collision_rect = pygame.Rect(
                trunk_x_world,
                trunk_y_world,
                TILE_SIZE,           # largura: apenas 1 tile (tronco central)
                TILE_SIZE            # altura: 1 tile (linha da base)
            )
        else:
            self.collision_rect = None

    def update_collision_rect(self):
        """Atualiza collision_rect caso world_x/world_y mudem (se necessário)."""
        if self.collision and self.collision_rect:
            center_col = self.width_tiles // 2
            self.collision_rect.x = int(self.world_x + center_col * TILE_SIZE)
            self.collision_rect.y = int(self.world_y + (self.height_tiles - 1) * TILE_SIZE)
            self.collision_rect.width = TILE_SIZE
            self.collision_rect.height = TILE_SIZE

    @property
    def bottom_y(self):
        """Retorna y da base (usado para depth-sorting)."""
        return self.world_y + self.height_tiles * TILE_SIZE

    def draw(self, screen, camera_x, camera_y, debug=False):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y

        # Só desenha se estiver dentro da área visível
        if (-self.width_tiles * TILE_SIZE <= screen_x < SCREEN_WIDTH and
            -self.height_tiles * TILE_SIZE <= screen_y < SCREEN_HEIGHT):
            screen.blit(self.image, (screen_x, screen_y))

            # Debug: desenha rect de colisão (apenas o tronco central)
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
        self.objects = []  # Lista de objetos (árvores, etc)
        self.level = level

        self.load_tiles()
        self.load_map()
        self.load_objects()

    def get_map_path(self):
        """Retorna o caminho do mapa baseado no nível"""
        maps = {
            1: "res/maps/map01.txt",
            2: "res/maps/map02.txt",
            3: "res/maps/map03.txt"
        }
        return maps.get(self.level, "res/maps/map01.txt")

    def load_tiles(self):
        """Carrega e redimensiona os tiles para o tamanho definido em self.tile_size"""
        try:
            # Índice 0 = grama
            grass_path = "res/tiles/grass.png"
            if os.path.exists(grass_path):
                grass = pygame.image.load(grass_path).convert_alpha()
            else:
                grass = self.create_placeholder_tile((100, 200, 100))  # Verde
            grass = pygame.transform.scale(grass, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(grass))

            # Índice 1 = areia
            sand_path = "res/tiles/sand.png"
            if os.path.exists(sand_path):
                sand = pygame.image.load(sand_path).convert_alpha()
            else:
                sand = self.create_placeholder_tile((210, 180, 140))  # Marrom claro
            sand = pygame.transform.scale(sand, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(sand))

            # Índice 2 = água
            water_path = "res/tiles/water.png"
            if os.path.exists(water_path):
                water = pygame.image.load(water_path).convert_alpha()
            else:
                water = self.create_placeholder_tile((0, 0, 255))  # Azul
            water = pygame.transform.scale(water, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(water, collision=True))

        except Exception as e:
            print(f"Erro ao carregar tiles: {e}")

    def create_placeholder_tile(self, color):
        """Cria um tile placeholder com a cor especificada"""
        surface = pygame.Surface((16, 16))
        surface.fill(color)
        return surface

    def load_map(self):
        """Carrega o mapa a partir de um arquivo de texto"""
        map_path = self.get_map_path()
        try:
            if os.path.exists(map_path):
                with open(map_path, "r") as file:
                    for line in file.readlines():
                        row = [int(x) for x in line.strip().split()]
                        self.map_tile_num.append(row)
            else:
                # Criar um mapa padrão se o arquivo não existir
                print(f"Mapa {map_path} não encontrado. Criando mapa padrão...")
                self.create_default_map()
        except Exception as e:
            print(f"Erro ao carregar mapa {map_path}: {e}")
            self.create_default_map()

    def create_default_map(self):
        """Cria um mapa padrão SEM ÁGUA NAS BORDAS para teste"""
        self.map_tile_num = []
        for row in range(MAX_WORLD_ROW):
            current_row = []
            for col in range(MAX_WORLD_COL):
                # Cria um mapa TODO DE GRAMA para teste (sem colisões)
                current_row.append(0)  # Grama em todos os lugares
            self.map_tile_num.append(current_row)

    def load_objects(self):
        """Carrega objetos como árvores, pedras, etc"""
        try:
            tree_path = "res/objects/tree.png"

            # Objetos diferentes para cada nível
            if self.level == 1:
                # Nível 1 - menos objetos (evitar área inicial do player)
                objects_data = [
                    (5, 5, 3, 5), (15, 10, 3, 5), (25, 15, 3, 5),
                    (35, 20, 3, 5), (45, 25, 3, 5), (55, 30, 3, 5),
                    (10, 35, 3, 5), (20, 40, 3, 5), (30, 45, 3, 5),
                    (40, 50, 3, 5), (50, 55, 3, 5)
                ]
            elif self.level == 2:
                # Nível 2 - alguns objetos
                objects_data = [
                    (8, 8, 3, 5), (12, 12, 3, 5), (16, 16, 3, 5),
                    (20, 20, 3, 5), (24, 24, 3, 5), (28, 28, 3, 5),
                    (32, 32, 3, 5), (36, 36, 3, 5), (40, 40, 3, 5),
                    (44, 44, 3, 5), (48, 48, 3, 5), (52, 52, 3, 5),
                    (56, 56, 3, 5), (15, 30, 3, 5), (30, 15, 3, 5)
                ]
            else:
                # Nível 3 - alguns objetos
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
                # Atualiza collision rect caso haja necessidade
                tree.update_collision_rect()
                self.objects.append(tree)

        except Exception as e:
            print(f"Erro ao carregar objetos: {e}")

    def get_obstacles(self):
        # Retorna lista de rects de colisão (apenas a base dos objetos)
        rects = []
        for obj in self.objects:
            if obj.collision and obj.collision_rect:
                rects.append(obj.collision_rect.copy())
        return rects

    def draw_ground(self, screen, camera_x, camera_y):
        """Desenha apenas o terreno (camada inferior)"""
        for row_index, row in enumerate(self.map_tile_num):
            for col_index, tile_index in enumerate(row):
                # Calcula a posição mundial do tile
                world_x = col_index * self.tile_size
                world_y = row_index * self.tile_size

                # Calcula a posição na tela subtraindo a posição da câmera
                screen_x = world_x - camera_x
                screen_y = world_y - camera_y

                # Só desenha se o tile estiver dentro da área visível da tela
                if (-self.tile_size <= screen_x < SCREEN_WIDTH and
                    -self.tile_size <= screen_y < SCREEN_HEIGHT):
                    screen.blit(self.tiles[tile_index].image, (screen_x, screen_y))

    # Nota: draw_objects original não será usado diretamente porque fazemos depth-sorting no Game.run
    def draw_objects(self, screen, camera_x, camera_y):
        """Desenha os objetos (camada superior)"""
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
        # POSIÇÃO INICIAL MAIS SEGURA (longe de objetos)
        self.world_x = TILE_SIZE * 20
        self.world_y = TILE_SIZE * 20
        self.skin_index = skin_index
        self.images = self.load_images()

        # Sistema de coleta
        self.collected_items = 0
        self.max_items = 10

        # Precomputar rect de colisão do player (top-left = world_x, world_y)
        self.width = TILE_SIZE
        self.height = TILE_SIZE

    def load_images(self):
        """Carrega as imagens reais do player da pasta res/"""
        images = {"up": [], "down": [], "left": [], "right": []}

        try:
            # skin_index 0 = personagem padrão
            folder = "res/player/"

            # Carregar imagens reais
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
            # Fallback para sprites coloridas
            images = self.create_fallback_sprites()

        return images

    def load_and_scale_image(self, path):
        """Carrega e redimensiona uma imagem para o tamanho do tile"""
        if os.path.exists(path):
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        else:
            # Criar placeholder se a imagem não existir
            print(f"Imagem não encontrada: {path}")
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)][self.skin_index % 4]
            pygame.draw.rect(surf, color, (0, 0, TILE_SIZE, TILE_SIZE))
            return surf

    def create_fallback_sprites(self):
        """Cria sprites de fallback caso as imagens não carreguem (é só um plano B)"""
        skin_colors = [
            [(255, 0, 0), (200, 0, 0)],    # Vermelho
            [(0, 255, 0), (0, 200, 0)],    # Verde  
            [(0, 0, 255), (0, 0, 200)],    # Azul
            [(255, 255, 0), (200, 200, 0)] # Amarelo
        ]

        base_color, dark_color = skin_colors[self.skin_index % len(skin_colors)]

        images = {"up": [], "down": [], "left": [], "right": []}
        size = TILE_SIZE

        for direction in images.keys():
            # Sprite 1
            surf1 = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf1, base_color, (0, 0, size, size))
            pygame.draw.circle(surf1, (255, 255, 255), (size//2, size//3), size//6)
            images[direction].append(surf1)

            # Sprite 2 (animação)
            surf2 = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.rect(surf2, dark_color, (0, 0, size, size))
            pygame.draw.circle(surf2, (255, 255, 255), (size//2, size//3), size//6)
            images[direction].append(surf2)

        return images

    def get_player_rect_at(self, x, y):
        """Retorna rect do player dada a posição top-left (x,y)"""
        return pygame.Rect(int(x), int(y), self.width, self.height)

    def check_collision(self, new_x, new_y, tile_manager):
        """Verifica colisão com tiles e objetos - agora usando apenas a base (collision_rect) dos objetos"""
        # Criar rect do player na nova posição (top-left)
        player_rect = self.get_player_rect_at(new_x, new_y)

        # Verificar colisão com tiles de colisão (apenas água por enquanto)
        tile_x1 = int(new_x / TILE_SIZE)
        tile_y1 = int(new_y / TILE_SIZE)
        tile_x2 = int((new_x + TILE_SIZE - 1) / TILE_SIZE)
        tile_y2 = int((new_y + TILE_SIZE - 1) / TILE_SIZE)

        for y in range(tile_y1, tile_y2 + 1):
            for x in range(tile_x1, tile_x2 + 1):
                if 0 <= y < len(tile_manager.map_tile_num) and 0 <= x < len(tile_manager.map_tile_num[0]):
                    tile_index = tile_manager.map_tile_num[y][x]
                    if tile_manager.tiles[tile_index].collision:
                        # Colidiu com tile "impossível"
                        # (mantive o print para debug)
                        print(f"Colisão com tile em ({x}, {y}) - tipo {tile_index}")
                        return True

        # Verificar colisão com objetos usando collision_rect (apenas tronco)
        for obj in tile_manager.objects:
            if obj.collision and obj.collision_rect:
                # Não esquecer: colisão_rect está em coordenadas world
                if player_rect.colliderect(obj.collision_rect):
                    print(f"Colisão com objeto (tronco) em ({obj.world_x}, {obj.world_y})")
                    return True

        return False

    def update(self, keys, tile_manager):
        """Atualiza a posição do player - com colisão por eixo (corrige bug de travar)"""
        move_x, move_y = 0, 0

        # Direção
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_y = -1
            self.direction = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_y = 1
            self.direction = "down"

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_x = -1
            self.direction = "left"
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_x = 1
            self.direction = "right"

        # Normaliza movimento diagonal
        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071

        # --- Movimenta e checa colisão eixo X ---
        new_x = self.world_x + move_x * self.speed
        if not self.check_collision(new_x, self.world_y, tile_manager):
            self.world_x = new_x

        # --- Movimenta e checa colisão eixo Y ---
        new_y = self.world_y + move_y * self.speed
        if not self.check_collision(self.world_x, new_y, tile_manager):
            self.world_y = new_y

        # Limites do mundo
        self.world_x = max(0, min(self.world_x, WORLD_WIDTH - TILE_SIZE))
        self.world_y = max(0, min(self.world_y, WORLD_HEIGHT - TILE_SIZE))

        # --- Animação ---
        if move_x != 0 or move_y != 0:
            self.sprite_counter += 1
            if self.sprite_counter > 7:
                self.sprite_num = 1 if self.sprite_num == 2 else 2
                self.sprite_counter = 0


    @property
    def bottom_y(self):
        """Y da base do player (usado para depth-sorting)"""
        return self.world_y + TILE_SIZE

    def draw(self, surface, camera_x, camera_y):
        img_list = self.images[self.direction]
        image = img_list[self.sprite_num - 1]

        # Calcula a posição do player na tela (sempre centralizado)
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
        self.color = (255, 215, 0)  # Dourado

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

        # Variáveis da câmera
        self.camera_x = 0
        self.camera_y = 0

        # Sistema de jogo
        self.collectibles = self.generate_collectibles()
        self.score = 0
        self.max_score = 200
        self.start_time = pygame.time.get_ticks()
        self.game_duration = 600000  # 10 minutos em milissegundos
        self.game_over = False
        self.level_completed = False

        # Fontes
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Debug flag: desenhar rects de colisão
        self.debug_draw_collision = False

        print(f"Player iniciado em: ({self.player.world_x}, {self.player.world_y})")

    def generate_collectibles(self):
        """Gera itens para coletar baseado no nível - EVITANDO ÁREA INICIAL"""
        collectibles = []
        if self.level == 1:
            # Itens longe da posição inicial do player (20, 20)
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
        """Atualiza a posição da câmera para seguir o player"""
        target_x = self.player.world_x - SCREEN_WIDTH // 2 + TILE_SIZE // 2
        target_y = self.player.world_y - SCREEN_HEIGHT // 2 + TILE_SIZE // 2

        self.camera_x = max(0, min(target_x, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, WORLD_HEIGHT - SCREEN_HEIGHT))

    def check_collectibles(self):
        """Verifica colisão com itens coletáveis"""
        for collectible in self.collectibles:
            if collectible.check_collision(self.player.world_x, self.player.world_y):
                if not collectible.collected:
                    collectible.collected = True
                    self.player.collected_items += 1
                    self.score += 20  # 20 pontos por item
                    print(f"Item coletado! Total: {self.player.collected_items}")

                    # Verificar se completou o nível
                    if self.player.collected_items >= self.player.max_items:
                        self.level_completed = True
                        print("Nível completado!")

    def draw_hud(self):
        """HUD moderna, equilibrada e sem fundo opaco"""
        # --- Cores ---
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        bar_bg_color = (60, 60, 60)
        bar_fill_color = (0, 200, 100)

        # --- Cálculos principais ---
        time_left = max(0, self.game_duration - (pygame.time.get_ticks() - self.start_time))
        minutes = time_left // 60000
        seconds = (time_left % 60000) // 1000
        time_text = f"Tempo: {minutes:02d}:{seconds:02d}"
        score_text = f"Pontos: {self.score}/{self.max_score}"
        items_text = f"Coletados: {self.player.collected_items}/{self.player.max_items}"
        level_text = f"Nível {self.level}"
        player_text = f"{self.nickname}"

        # --- Barra centralizada ---
        collected_ratio = self.player.collected_items / self.player.max_items
        bar_width = 260
        bar_height = 16
        bar_x = (SCREEN_WIDTH - bar_width) // 2
        bar_y = 40

        pygame.draw.rect(self.screen, bar_bg_color, (bar_x, bar_y, bar_width, bar_height), border_radius=8)
        pygame.draw.rect(self.screen, bar_fill_color, (bar_x, bar_y, int(bar_width * collected_ratio), bar_height), border_radius=8)

        # --- Nome e nível acima da barra ---
        title_text = f"{player_text}  |  {level_text}"
        title_surface = self.small_font.render(title_text, True, text_color)
        title_shadow = self.small_font.render(title_text, True, shadow_color)
        self.screen.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2 + 1, bar_y - 18 + 1))
        self.screen.blit(title_surface, (SCREEN_WIDTH // 2 - title_surface.get_width() // 2, bar_y - 18))

        # --- Textos no canto superior esquerdo ---
        def draw_text_with_shadow(text, pos_y, font):
            shadow = font.render(text, True, shadow_color)
            text_render = font.render(text, True, text_color)
            self.screen.blit(shadow, (21, pos_y + 1))
            self.screen.blit(text_render, (20, pos_y))

        draw_text_with_shadow(time_text, 80, self.font)
        draw_text_with_shadow(score_text, 110, self.font)
        draw_text_with_shadow(items_text, 145, self.small_font)

    def draw_game_over(self):
        """Desenha tela de game over"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        game_over_text = self.font.render("TEMPO ESGOTADO!", True, (255, 0, 0))
        restart_text = self.small_font.render("Pressione ESC para sair", True, (255, 255, 255))

        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))

    def draw_level_complete(self):
        """Desenha tela de nível completo"""
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

            # Verificar fim de jogo por tempo
            if time_elapsed >= self.game_duration and not self.level_completed:
                self.game_over = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Toggle debug para visualizar rects de colisão
                    elif event.key == pygame.K_F1:
                        self.debug_draw_collision = not self.debug_draw_collision

            if not self.game_over and not self.level_completed:
                keys = pygame.key.get_pressed()
                self.player.update(keys, self.tile_manager)
                self.update_camera()
                self.check_collectibles()

            # Renderização
            self.screen.fill((0, 0, 0))

            # 1. Terreno
            self.tile_manager.draw_ground(self.screen, self.camera_x, self.camera_y)

            # 2. Itens coletáveis
            for collectible in self.collectibles:
                collectible.draw(self.screen, self.camera_x, self.camera_y)

            # 3+4. Depth-sorting: ordenar e desenhar objetos e player com base em bottom_y
            # Construir lista de drawables (objetos + player)
            drawables = []
            # adicionar objetos
            for obj in self.tile_manager.objects:
                # garantir collision_rect atualizado
                obj.update_collision_rect()
                drawables.append(obj)
            # adicionar player (objeto com bottom_y)
            drawables.append(self.player)

            # ordenar pela coordenada de base/bottom y
            def get_bottom(o):
                # se tiver atributo bottom_y usar ele, senão usar world_y + TILE_SIZE
                if hasattr(o, "bottom_y"):
                    return o.bottom_y
                return getattr(o, "world_y", 0) + TILE_SIZE

            drawables.sort(key=get_bottom)

            # desenhar na ordem
            for d in drawables:
                if isinstance(d, GameObject):
                    d.draw(self.screen, self.camera_x, self.camera_y, debug=self.debug_draw_collision)
                elif isinstance(d, Player):
                    d.draw(self.screen, self.camera_x, self.camera_y)

            # 5. HUD
            self.draw_hud()

            # 6. Telas de fim de jogo
            if self.game_over:
                self.draw_game_over()
            elif self.level_completed:
                self.draw_level_complete()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

        # Retornar resultado
        success = self.level_completed and self.score >= 160  # 80% de 200
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