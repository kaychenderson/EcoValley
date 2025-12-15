import pygame
import sys
import argparse
import os
import random
import json
import requests

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
MAX_WORLD_COL = 92
MAX_WORLD_ROW = 73
WORLD_WIDTH = TILE_SIZE * MAX_WORLD_COL
WORLD_HEIGHT = TILE_SIZE * MAX_WORLD_ROW

FPS = 60

# Tipos de lixo e cores correspondentes
TRASH_TYPES = ['metal', 'organico', 'papel', 'plastico', 'vidro']
TRASH_COLORS = {
    'metal': (0, 0, 255),      # Azul
    'organico': (139, 69, 19), # Marrom
    'papel': (255, 255, 255),  # Branco
    'plastico': (255, 255, 0), # Amarelo
    'vidro': (0, 255, 0)       # Verde
}

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
# CLASSE LIXO
# ========================
class Trash:
    def __init__(self, x, y, trash_type, image_path):
        self.world_x = x * TILE_SIZE
        self.world_y = y * TILE_SIZE
        self.trash_type = trash_type
        self.collected = False
        self.size = TILE_SIZE  # Agora ocupa 1 tile completo
        self.color = TRASH_COLORS.get(trash_type, (128, 128, 128))
        
        # Carregar imagem do lixo
        self.image = None
        try:
            if os.path.exists(image_path):
                self.image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.size, self.size))
            else:
                print(f"Imagem de lixo não encontrada: {image_path}")
        except Exception as e:
            print(f"Erro ao carregar imagem do lixo {image_path}: {e}")

    def draw(self, screen, camera_x, camera_y):
        if not self.collected:
            screen_x = self.world_x - camera_x
            screen_y = self.world_y - camera_y
            
            if self.image:
                screen.blit(self.image, (screen_x, screen_y))
            else:
                # Desenhar placeholder colorido ocupando o tile completo
                pygame.draw.rect(screen, self.color, (screen_x, screen_y, self.size, self.size))
                
                # Mostrar tipo do lixo
                font = pygame.font.Font(None, 20)
                text = font.render(self.trash_type.upper(), True, (0, 0, 0))
                text_rect = text.get_rect(center=(screen_x + self.size//2, screen_y + self.size//2))
                screen.blit(text, text_rect)

    def check_collision(self, player_x, player_y):
        if self.collected:
            return False

        player_rect = pygame.Rect(player_x, player_y, TILE_SIZE, TILE_SIZE)
        trash_rect = pygame.Rect(self.world_x, self.world_y, self.size, self.size)
        return player_rect.colliderect(trash_rect)

    @property
    def bottom_y(self):
        """Y da base do lixo (usado para depth-sorting)"""
        return self.world_y + self.size

# ========================
# CLASSE LIXEIRA
# ========================
class TrashBin(GameObject):
    def __init__(self, image_path, world_x, world_y, trash_type, width_tiles=1, height_tiles=1):
        super().__init__(image_path, world_x, world_y, width_tiles, height_tiles, collision=True)
        self.trash_type = trash_type

# ========================
# TILE MANAGER
# ========================
class TileManager:
    def __init__(self, tile_size, level):
        self.tile_size = tile_size
        self.tiles = []
        self.map_tile_num = []
        self.objects = []  # Lista de objetos (árvores, etc)
        self.trash_bins = []  # Lista de lixeiras
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

            # Índice 3 = lago_maior1x1
            lago_maior1x1_path = "res/tiles/lago_maior1x1.png"
            if os.path.exists(lago_maior1x1_path):
                lago_maior1x1 = pygame.image.load(lago_maior1x1_path).convert_alpha()
            else:
                lago_maior1x1 = self.create_placeholder_tile((0, 100, 200))  # Azul médio
            lago_maior1x1 = pygame.transform.scale(lago_maior1x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior1x1, collision=True))

            # Índice 4 = lago_maior1x2
            lago_maior1x2_path = "res/tiles/lago_maior1x2.png"
            if os.path.exists(lago_maior1x2_path):
                lago_maior1x2 = pygame.image.load(lago_maior1x2_path).convert_alpha()
            else:
                lago_maior1x2 = self.create_placeholder_tile((0, 110, 210))  # Azul médio
            lago_maior1x2 = pygame.transform.scale(lago_maior1x2, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior1x2, collision=True))

            # Índice 5 = lago_maior1x3
            lago_maior1x3_path = "res/tiles/lago_maior1x3.png"
            if os.path.exists(lago_maior1x3_path):
                lago_maior1x3 = pygame.image.load(lago_maior1x3_path).convert_alpha()
            else:
                lago_maior1x3 = self.create_placeholder_tile((0, 120, 220))  # Azul médio
            lago_maior1x3 = pygame.transform.scale(lago_maior1x3, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior1x3, collision=True))

            # Índice 6 = lago_maior2x1
            lago_maior2x1_path = "res/tiles/lago_maior2x1.png"
            if os.path.exists(lago_maior2x1_path):
                lago_maior2x1 = pygame.image.load(lago_maior2x1_path).convert_alpha()
            else:
                lago_maior2x1 = self.create_placeholder_tile((10, 100, 200))  # Azul médio
            lago_maior2x1 = pygame.transform.scale(lago_maior2x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior2x1, collision=True))

            # Índice 7 = lago_maior2x2
            lago_maior2x2_path = "res/tiles/lago_maior2x2.png"
            if os.path.exists(lago_maior2x2_path):
                lago_maior2x2 = pygame.image.load(lago_maior2x2_path).convert_alpha()
            else:
                lago_maior2x2 = self.create_placeholder_tile((10, 110, 210))  # Azul médio
            lago_maior2x2 = pygame.transform.scale(lago_maior2x2, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior2x2, collision=True))

            # Índice 8 = lago_maior2x3
            lago_maior2x3_path = "res/tiles/lago_maior2x3.png"
            if os.path.exists(lago_maior2x3_path):
                lago_maior2x3 = pygame.image.load(lago_maior2x3_path).convert_alpha()
            else:
                lago_maior2x3 = self.create_placeholder_tile((10, 120, 220))  # Azul médio
            lago_maior2x3 = pygame.transform.scale(lago_maior2x3, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior2x3, collision=True))

            # Índice 9 = lago_maior3x1
            lago_maior3x1_path = "res/tiles/lago_maior3x1.png"
            if os.path.exists(lago_maior3x1_path):
                lago_maior3x1 = pygame.image.load(lago_maior3x1_path).convert_alpha()
            else:
                lago_maior3x1 = self.create_placeholder_tile((20, 100, 200))  # Azul médio
            lago_maior3x1 = pygame.transform.scale(lago_maior3x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior3x1, collision=True))

            # Índice 10 = lago_maior3x3
            lago_maior3x3_path = "res/tiles/lago_maior3x3.png"
            if os.path.exists(lago_maior3x3_path):
                lago_maior3x3 = pygame.image.load(lago_maior3x3_path).convert_alpha()
            else:
                lago_maior3x3 = self.create_placeholder_tile((20, 120, 220))  # Azul médio
            lago_maior3x3 = pygame.transform.scale(lago_maior3x3, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior3x3, collision=True))

            # Índice 11 = lago_maior4x1
            lago_maior4x1_path = "res/tiles/lago_maior4x1.png"
            if os.path.exists(lago_maior4x1_path):
                lago_maior4x1 = pygame.image.load(lago_maior4x1_path).convert_alpha()
            else:
                lago_maior4x1 = self.create_placeholder_tile((30, 100, 200))  # Azul médio
            lago_maior4x1 = pygame.transform.scale(lago_maior4x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior4x1, collision=True))

            # Índice 12 = lago_maior4x2
            lago_maior4x2_path = "res/tiles/lago_maior4x2.png"
            if os.path.exists(lago_maior4x2_path):
                lago_maior4x2 = pygame.image.load(lago_maior4x2_path).convert_alpha()
            else:
                lago_maior4x2 = self.create_placeholder_tile((30, 110, 210))  # Azul médio
            lago_maior4x2 = pygame.transform.scale(lago_maior4x2, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior4x2, collision=True))

            # Índice 13 = lago_maior4x3
            lago_maior4x3_path = "res/tiles/lago_maior4x3.png"
            if os.path.exists(lago_maior4x3_path):
                lago_maior4x3 = pygame.image.load(lago_maior4x3_path).convert_alpha()
            else:
                lago_maior4x3 = self.create_placeholder_tile((30, 120, 220))  # Azul médio
            lago_maior4x3 = pygame.transform.scale(lago_maior4x3, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_maior4x3, collision=True))

            # Índice 14 = lago_menor_down_center
            lago_menor_down_center_path = "res/tiles/lago_menor_down_center.png"
            if os.path.exists(lago_menor_down_center_path):
                lago_menor_down_center = pygame.image.load(lago_menor_down_center_path).convert_alpha()
            else:
                lago_menor_down_center = self.create_placeholder_tile((100, 150, 200))  # Azul claro
            lago_menor_down_center = pygame.transform.scale(lago_menor_down_center, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_down_center, collision=True))

            # Índice 15 = lago_menor_entorno1
            lago_menor_entorno1_path = "res/tiles/lago_menor_entorno1.png"
            if os.path.exists(lago_menor_entorno1_path):
                lago_menor_entorno1 = pygame.image.load(lago_menor_entorno1_path).convert_alpha()
            else:
                lago_menor_entorno1 = self.create_placeholder_tile((110, 160, 210))  # Azul claro
            lago_menor_entorno1 = pygame.transform.scale(lago_menor_entorno1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_entorno1, collision=False))

            # Índice 16 = lago_menor_entorno2
            lago_menor_entorno2_path = "res/tiles/lago_menor_entorno2.png"
            if os.path.exists(lago_menor_entorno2_path):
                lago_menor_entorno2 = pygame.image.load(lago_menor_entorno2_path).convert_alpha()
            else:
                lago_menor_entorno2 = self.create_placeholder_tile((120, 170, 220))  # Azul claro
            lago_menor_entorno2 = pygame.transform.scale(lago_menor_entorno2, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_entorno2, collision=False))

            # Índice 17 = lago_menor_in_algas
            lago_menor_in_algas_path = "res/tiles/lago_menor_in_algas.png"
            if os.path.exists(lago_menor_in_algas_path):
                lago_menor_in_algas = pygame.image.load(lago_menor_in_algas_path).convert_alpha()
            else:
                lago_menor_in_algas = self.create_placeholder_tile((50, 150, 100))  # Verde-azulado
            lago_menor_in_algas = pygame.transform.scale(lago_menor_in_algas, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_in_algas, collision=True))

            # Índice 18 = lago_menor_in_clean
            lago_menor_in_clean_path = "res/tiles/lago_menor_in_clean.png"
            if os.path.exists(lago_menor_in_clean_path):
                lago_menor_in_clean = pygame.image.load(lago_menor_in_clean_path).convert_alpha()
            else:
                lago_menor_in_clean = self.create_placeholder_tile((100, 200, 250))  # Azul muito claro
            lago_menor_in_clean = pygame.transform.scale(lago_menor_in_clean, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_in_clean, collision=True))

            # Índice 19 = lago_menor_in_concha
            lago_menor_in_concha_path = "res/tiles/lago_menor_in_concha.png"
            if os.path.exists(lago_menor_in_concha_path):
                lago_menor_in_concha = pygame.image.load(lago_menor_in_concha_path).convert_alpha()
            else:
                lago_menor_in_concha = self.create_placeholder_tile((200, 180, 120))  # Cor de concha
            lago_menor_in_concha = pygame.transform.scale(lago_menor_in_concha, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_in_concha, collision=True))

            # Índice 20 = lago_menor_in_holes
            lago_menor_in_holes_path = "res/tiles/lago_menor_in_holes.png"
            if os.path.exists(lago_menor_in_holes_path):
                lago_menor_in_holes = pygame.image.load(lago_menor_in_holes_path).convert_alpha()
            else:
                lago_menor_in_holes = self.create_placeholder_tile((80, 80, 120))  # Azul escuro com buracos
            lago_menor_in_holes = pygame.transform.scale(lago_menor_in_holes, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_in_holes, collision=True))

            # Índice 21 = lago_menor_in_rock
            lago_menor_in_rock_path = "res/tiles/lago_menor_in_rock.png"
            if os.path.exists(lago_menor_in_rock_path):
                lago_menor_in_rock = pygame.image.load(lago_menor_in_rock_path).convert_alpha()
            else:
                lago_menor_in_rock = self.create_placeholder_tile((120, 120, 120))  # Cinza de pedra
            lago_menor_in_rock = pygame.transform.scale(lago_menor_in_rock, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_in_rock, collision=True))

            # Índice 22 = lago_menor_left_center
            lago_menor_left_center_path = "res/tiles/lago_menor_left_center.png"
            if os.path.exists(lago_menor_left_center_path):
                lago_menor_left_center = pygame.image.load(lago_menor_left_center_path).convert_alpha()
            else:
                lago_menor_left_center = self.create_placeholder_tile((130, 180, 230))  # Azul claro
            lago_menor_left_center = pygame.transform.scale(lago_menor_left_center, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_left_center, collision=True))

            # Índice 23 = lago_menor_right_center
            lago_menor_right_center_path = "res/tiles/lago_menor_right_center.png"
            if os.path.exists(lago_menor_right_center_path):
                lago_menor_right_center = pygame.image.load(lago_menor_right_center_path).convert_alpha()
            else:
                lago_menor_right_center = self.create_placeholder_tile((140, 190, 240))  # Azul claro
            lago_menor_right_center = pygame.transform.scale(lago_menor_right_center, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_right_center, collision=True))

            # Índice 24 = lago_menor_top_center
            lago_menor_top_center_path = "res/tiles/lago_menor_top_center.png"
            if os.path.exists(lago_menor_top_center_path):
                lago_menor_top_center = pygame.image.load(lago_menor_top_center_path).convert_alpha()
            else:
                lago_menor_top_center = self.create_placeholder_tile((150, 200, 250))  # Azul claro
            lago_menor_top_center = pygame.transform.scale(lago_menor_top_center, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor_top_center, collision=True))

            # Índice 25 = lago_menor1x1
            lago_menor1x1_path = "res/tiles/lago_menor1x1.png"
            if os.path.exists(lago_menor1x1_path):
                lago_menor1x1 = pygame.image.load(lago_menor1x1_path).convert_alpha()
            else:
                lago_menor1x1 = self.create_placeholder_tile((160, 210, 255))  # Azul muito claro
            lago_menor1x1 = pygame.transform.scale(lago_menor1x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor1x1, collision=True))

            # Índice 26 = lago_menor1x6
            lago_menor1x6_path = "res/tiles/lago_menor1x6.png"
            if os.path.exists(lago_menor1x6_path):
                lago_menor1x6 = pygame.image.load(lago_menor1x6_path).convert_alpha()
            else:
                lago_menor1x6 = self.create_placeholder_tile((170, 220, 255))  # Azul muito claro
            lago_menor1x6 = pygame.transform.scale(lago_menor1x6, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor1x6, collision=True))

            # Índice 27 = lago_menor6x1
            lago_menor6x1_path = "res/tiles/lago_menor6x1.png"
            if os.path.exists(lago_menor6x1_path):
                lago_menor6x1 = pygame.image.load(lago_menor6x1_path).convert_alpha()
            else:
                lago_menor6x1 = self.create_placeholder_tile((180, 230, 255))  # Azul muito claro
            lago_menor6x1 = pygame.transform.scale(lago_menor6x1, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor6x1, collision=True))

            # Índice 28 = lago_menor6x6
            lago_menor6x6_path = "res/tiles/lago_menor6x6.png"
            if os.path.exists(lago_menor6x6_path):
                lago_menor6x6 = pygame.image.load(lago_menor6x6_path).convert_alpha()
            else:
                lago_menor6x6 = self.create_placeholder_tile((190, 240, 255))  # Azul muito claro
            lago_menor6x6 = pygame.transform.scale(lago_menor6x6, (self.tile_size, self.tile_size))
            self.tiles.append(Tile(lago_menor6x6, collision=True))

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
            tree2_path = "res/objects/tree2.png"
            tree3_path = "res/objects/tree3.png"
            trunk_path = "res/objects/trunk.png"
            rock_path = "res/objects/rock.png"
            rocks_path = "res/objects/rocks.png"
            bush_path = "res/objects/bush.png"
            plant_path = "res/objects/plant.png"
            blueflower_path = "res/objects/blueflower.png"
            purpleflower_path = "res/objects/purpleflower.png"
            mushroom_path = "res/objects/mushroom.png"
            lamppost_path = "res/objects/lamp_post.png"
            fence_path = "res/objects/fence.png"
            rockwall_path = "res/objects/rockwall.png"
            woodhouse_path = "res/objects/woodhouse.png"
            metal_lixeira_path = "res/objects/metal_lixeira.png"
            papel_lixeira_path = "res/objects/papel_lixeira.png"
            plastico_lixeira_path = "res/objects/plastico_lixeira.png"
            vidro_lixeira_path = "res/objects/vidro_lixeira.png"
            organico_lixeira_path = "res/objects/organic_lixeira.png"

            aux_x = 6
            aux_y = 5
            # Objetos diferentes para cada nível
            if self.level == 1:
                # Nível 1 - menos objetos (evitar área inicial do player)
                objects_data_tree = [
                    (aux_x+6, aux_y+4, 3, 5), (aux_x+4, aux_y+13, 3, 5), (aux_x+10, aux_y+10, 3, 5),
                    (aux_x+16, aux_y+6, 3, 5), (aux_x+13, aux_y+12, 3, 5), (aux_x+10, aux_y+20, 3, 5),
                    (aux_x+20, aux_y+17, 3, 5), (aux_x+22, aux_y+13, 3, 5), (aux_x+7, aux_y+25, 3, 5),
                    (aux_x+15, aux_y+25, 3, 5), (aux_x+23, aux_y+25, 3, 5), (aux_x+33, aux_y+12, 3, 5),
                    (aux_x+35, aux_y+23, 3, 5), (aux_x+41, aux_y+9, 3, 5), (aux_x+40, aux_y+16, 3, 5),
                    (aux_x+41, aux_y+21, 3, 5), (aux_x+43, aux_y+24, 3, 5), (aux_x+47, aux_y+14, 3, 5), 
                    (aux_x+49, aux_y+20, 3, 5), (aux_x+52, aux_y+21, 3, 5), (aux_x+51, aux_y+25, 3, 5),
                    (aux_x+47, aux_y+27, 3, 5), (aux_x+56, aux_y+26, 3, 5), (aux_x+59, aux_y+24, 3, 5),
                    (aux_x+41, aux_y+34, 3, 5), (aux_x+65, aux_y+2, 3, 5), (aux_x+64, aux_y+36, 3, 5),
                    (aux_x+57, aux_y+40, 3, 5), (aux_x+46, aux_y+41, 3, 5)
                ]
                objects_data_tree2 = [
                    (aux_x+5, aux_y+8, 3, 5), (aux_x+7, aux_y+10, 3, 5), (aux_x+11, aux_y+5, 3, 5),
                    (aux_x+9, aux_y+14, 3, 5), (aux_x+15, aux_y+17, 3, 5), (aux_x+19, aux_y+14, 3, 5),
                    (aux_x+24, aux_y+19, 3, 5), (aux_x+18, aux_y+9, 3, 5), (aux_x+18, aux_y+22, 3, 5), 
                    (aux_x+34, aux_y+4, 3, 5), (aux_x+43, aux_y+4, 3, 5), (aux_x+16, aux_y+2, 3, 5),
                    (aux_x+39, aux_y+12, 3, 5), (aux_x+43, aux_y+11, 3, 5), (aux_x+44, aux_y+19, 3, 5), 
                    (aux_x+46, aux_y+22, 3, 5), (aux_x+54, aux_y+2, 3, 5), (aux_x+39, aux_y+24, 3, 5),
                    (aux_x+37, aux_y+29, 3, 5), (aux_x+41, aux_y+27, 3, 5), (aux_x+43, aux_y+31, 3, 5),
                    (aux_x+43, aux_y+38, 3, 5), (aux_x+50, aux_y+42, 3, 5), (aux_x+52, aux_y+29, 3, 5),
                    (aux_x+62, aux_y+39, 3, 5), (aux_x+57, aux_y+30, 3, 5), (aux_x+54, aux_y+24, 3, 5),
                    (aux_x+65, aux_y+30, 3, 5), (aux_x+67, aux_y+34, 3, 5), (aux_x+68, aux_y+17, 3, 5),
                    (aux_x+70, aux_y+54, 3, 5), (aux_x+73, aux_y+52, 3, 5)
                ]
                objects_data_tree3 = [
                    (aux_x+14, aux_y+3, 3, 5), (aux_x+20, aux_y+3, 3, 5), (aux_x+8, aux_y+18, 3, 5), 
                    (aux_x+12, aux_y+18, 3, 5), (aux_x+12, aux_y+24, 3, 5), (aux_x+21, aux_y+23, 3, 5),
                    (aux_x+6, aux_y+31, 3, 5), (aux_x+15, aux_y+30, 3, 5), (aux_x+9, aux_y+32, 3, 5),
                    (aux_x+7, aux_y+35, 3, 5), (aux_x+5, aux_y+38, 3, 5), (aux_x+14, aux_y+34, 3, 5),
                    (aux_x+18, aux_y+34, 3, 5), (aux_x+22, aux_y+34, 3, 5), (aux_x+10, aux_y+40, 3, 5),
                    (aux_x+13, aux_y+39, 3, 5), (aux_x+23, aux_y+39, 3, 5), (aux_x+9, aux_y+43, 3, 5),
                    (aux_x+7, aux_y+43, 3, 5), (aux_x+21, aux_y+43, 3, 5), (aux_x+26, aux_y+44, 3, 5),
                    (aux_x+16, aux_y+47, 3, 5), (aux_x+19, aux_y+46, 3, 5), (aux_x+24, aux_y+46, 3, 5),
                    (aux_x+5, aux_y+52, 3, 5), (aux_x+8, aux_y+53, 3, 5), (aux_x+11, aux_y+50, 3, 5),
                    (aux_x+14, aux_y+53, 3, 5), (aux_x+17, aux_y+51, 3, 5), (aux_x+21, aux_y+54, 3, 5),
                    (aux_x+29, aux_y+52, 3, 5), (aux_x+41, aux_y+41, 3, 5), (aux_x+40, aux_y+31, 3, 5),
                    (aux_x+32, aux_y+25, 3, 5), (aux_x+55, aux_y+42, 3, 5), (aux_x+60, aux_y+43, 3, 5), 
                    (aux_x+66, aux_y+39, 3, 5), (aux_x+62, aux_y+28, 3, 5), (aux_x+70, aux_y+33, 3, 5),
                    (aux_x+50, aux_y+7, 3, 5)
                ]
                # Lixeiras - posicionadas estrategicamente
                objects_data_organico_lix = [(aux_x+76, aux_y+8, 1, 1, 'organico')]
                objects_data_metal_lix = [(aux_x+74, aux_y+8, 1, 1, 'metal')]
                objects_data_vidro_lix = [(aux_x+72, aux_y+8, 1, 1, 'vidro')]
                objects_data_plastico_lix = [(aux_x+70, aux_y+8, 1, 1, 'plastico')]
                objects_data_papel_lix = [(aux_x+68, aux_y+8, 1, 1, 'papel')]
                
            elif self.level == 2:
                # Nível 2 - alguns objetos
                objects_data_tree = [
                    (aux_x+6, aux_y+4, 3, 5), (aux_x+4, aux_y+13, 3, 5), (aux_x+10, aux_y+10, 3, 5),
                    (aux_x+16, aux_y+6, 3, 5), (aux_x+13, aux_y+12, 3, 5), (aux_x+10, aux_y+20, 3, 5),
                    (aux_x+20, aux_y+17, 3, 5), (aux_x+22, aux_y+13, 3, 5), (aux_x+7, aux_y+25, 3, 5),
                    (aux_x+15, aux_y+25, 3, 5), (aux_x+23, aux_y+25, 3, 5), (aux_x+33, aux_y+12, 3, 5),
                    (aux_x+35, aux_y+23, 3, 5), (aux_x+41, aux_y+9, 3, 5), (aux_x+40, aux_y+16, 3, 5),
                    (aux_x+41, aux_y+21, 3, 5), (aux_x+43, aux_y+24, 3, 5), (aux_x+47, aux_y+14, 3, 5), 
                    (aux_x+49, aux_y+20, 3, 5), (aux_x+52, aux_y+21, 3, 5), (aux_x+51, aux_y+25, 3, 5),
                    (aux_x+47, aux_y+27, 3, 5), (aux_x+56, aux_y+26, 3, 5), (aux_x+59, aux_y+24, 3, 5),
                    (aux_x+41, aux_y+34, 3, 5), (aux_x+65, aux_y+2, 3, 5), (aux_x+64, aux_y+36, 3, 5),
                    (aux_x+57, aux_y+40, 3, 5), (aux_x+46, aux_y+41, 3, 5)
                ]
                objects_data_tree2 = [
                    (aux_x+5, aux_y+8, 3, 5), (aux_x+7, aux_y+10, 3, 5), (aux_x+11, aux_y+5, 3, 5),
                    (aux_x+9, aux_y+14, 3, 5), (aux_x+15, aux_y+17, 3, 5), (aux_x+19, aux_y+14, 3, 5),
                    (aux_x+24, aux_y+19, 3, 5), (aux_x+18, aux_y+9, 3, 5), (aux_x+18, aux_y+22, 3, 5), 
                    (aux_x+34, aux_y+4, 3, 5), (aux_x+43, aux_y+4, 3, 5), (aux_x+16, aux_y+2, 3, 5),
                    (aux_x+39, aux_y+12, 3, 5), (aux_x+43, aux_y+11, 3, 5), (aux_x+44, aux_y+19, 3, 5), 
                    (aux_x+46, aux_y+22, 3, 5), (aux_x+54, aux_y+2, 3, 5), (aux_x+39, aux_y+24, 3, 5),
                    (aux_x+37, aux_y+29, 3, 5), (aux_x+41, aux_y+27, 3, 5), (aux_x+43, aux_y+31, 3, 5),
                    (aux_x+43, aux_y+38, 3, 5), (aux_x+50, aux_y+42, 3, 5), (aux_x+52, aux_y+29, 3, 5),
                    (aux_x+62, aux_y+39, 3, 5), (aux_x+57, aux_y+30, 3, 5), (aux_x+54, aux_y+24, 3, 5),
                    (aux_x+65, aux_y+30, 3, 5), (aux_x+67, aux_y+34, 3, 5), (aux_x+68, aux_y+17, 3, 5),
                    (aux_x+70, aux_y+54, 3, 5), (aux_x+73, aux_y+52, 3, 5)
                ]
                objects_data_tree3 = [
                    (aux_x+14, aux_y+3, 3, 5), (aux_x+20, aux_y+3, 3, 5), (aux_x+8, aux_y+18, 3, 5), 
                    (aux_x+12, aux_y+18, 3, 5), (aux_x+12, aux_y+24, 3, 5), (aux_x+21, aux_y+23, 3, 5),
                    (aux_x+6, aux_y+31, 3, 5), (aux_x+15, aux_y+30, 3, 5), (aux_x+9, aux_y+32, 3, 5),
                    (aux_x+7, aux_y+35, 3, 5), (aux_x+5, aux_y+38, 3, 5), (aux_x+14, aux_y+34, 3, 5),
                    (aux_x+18, aux_y+34, 3, 5), (aux_x+22, aux_y+34, 3, 5), (aux_x+10, aux_y+40, 3, 5),
                    (aux_x+13, aux_y+39, 3, 5), (aux_x+23, aux_y+39, 3, 5), (aux_x+9, aux_y+43, 3, 5),
                    (aux_x+7, aux_y+43, 3, 5), (aux_x+21, aux_y+43, 3, 5), (aux_x+26, aux_y+44, 3, 5),
                    (aux_x+16, aux_y+47, 3, 5), (aux_x+19, aux_y+46, 3, 5), (aux_x+24, aux_y+46, 3, 5),
                    (aux_x+5, aux_y+52, 3, 5), (aux_x+8, aux_y+53, 3, 5), (aux_x+11, aux_y+50, 3, 5),
                    (aux_x+14, aux_y+53, 3, 5), (aux_x+17, aux_y+51, 3, 5), (aux_x+21, aux_y+54, 3, 5),
                    (aux_x+29, aux_y+52, 3, 5), (aux_x+41, aux_y+41, 3, 5), (aux_x+40, aux_y+31, 3, 5),
                    (aux_x+32, aux_y+25, 3, 5), (aux_x+55, aux_y+42, 3, 5), (aux_x+60, aux_y+43, 3, 5), 
                    (aux_x+66, aux_y+39, 3, 5), (aux_x+62, aux_y+28, 3, 5), (aux_x+70, aux_y+33, 3, 5),
                    (aux_x+50, aux_y+7, 3, 5)
                ]
                # Lixeiras - posicionadas estrategicamente
                objects_data_organico_lix = [(aux_x+76, aux_y+8, 1, 1, 'organico')]
                objects_data_metal_lix = [(aux_x+74, aux_y+8, 1, 1, 'metal')]
                objects_data_vidro_lix = [(aux_x+72, aux_y+8, 1, 1, 'vidro')]
                objects_data_plastico_lix = [(aux_x+70, aux_y+8, 1, 1, 'plastico')]
                objects_data_papel_lix = [(aux_x+68, aux_y+8, 1, 1, 'papel')]
            else:
                # Nível 3 - alguns objetos
                objects_data_tree = [
                    (aux_x+6, aux_y+4, 3, 5), (aux_x+4, aux_y+13, 3, 5), (aux_x+10, aux_y+10, 3, 5),
                    (aux_x+16, aux_y+6, 3, 5), (aux_x+13, aux_y+12, 3, 5), (aux_x+10, aux_y+20, 3, 5),
                    (aux_x+20, aux_y+17, 3, 5), (aux_x+22, aux_y+13, 3, 5), (aux_x+7, aux_y+25, 3, 5),
                    (aux_x+15, aux_y+25, 3, 5), (aux_x+23, aux_y+25, 3, 5), (aux_x+33, aux_y+12, 3, 5),
                    (aux_x+35, aux_y+23, 3, 5), (aux_x+41, aux_y+9, 3, 5), (aux_x+40, aux_y+16, 3, 5),
                    (aux_x+41, aux_y+21, 3, 5), (aux_x+43, aux_y+24, 3, 5), (aux_x+47, aux_y+14, 3, 5), 
                    (aux_x+49, aux_y+20, 3, 5), (aux_x+52, aux_y+21, 3, 5), (aux_x+51, aux_y+25, 3, 5),
                    (aux_x+47, aux_y+27, 3, 5), (aux_x+56, aux_y+26, 3, 5), (aux_x+59, aux_y+24, 3, 5),
                    (aux_x+41, aux_y+34, 3, 5), (aux_x+65, aux_y+2, 3, 5), (aux_x+64, aux_y+36, 3, 5),
                    (aux_x+57, aux_y+40, 3, 5), (aux_x+46, aux_y+41, 3, 5)
                ]
                objects_data_tree2 = [
                    (aux_x+5, aux_y+8, 3, 5), (aux_x+7, aux_y+10, 3, 5), (aux_x+11, aux_y+5, 3, 5),
                    (aux_x+9, aux_y+14, 3, 5), (aux_x+15, aux_y+17, 3, 5), (aux_x+19, aux_y+14, 3, 5),
                    (aux_x+24, aux_y+19, 3, 5), (aux_x+18, aux_y+9, 3, 5), (aux_x+18, aux_y+22, 3, 5), 
                    (aux_x+34, aux_y+4, 3, 5), (aux_x+43, aux_y+4, 3, 5), (aux_x+16, aux_y+2, 3, 5),
                    (aux_x+39, aux_y+12, 3, 5), (aux_x+43, aux_y+11, 3, 5), (aux_x+44, aux_y+19, 3, 5), 
                    (aux_x+46, aux_y+22, 3, 5), (aux_x+54, aux_y+2, 3, 5), (aux_x+39, aux_y+24, 3, 5),
                    (aux_x+37, aux_y+29, 3, 5), (aux_x+41, aux_y+27, 3, 5), (aux_x+43, aux_y+31, 3, 5),
                    (aux_x+43, aux_y+38, 3, 5), (aux_x+50, aux_y+42, 3, 5), (aux_x+52, aux_y+29, 3, 5),
                    (aux_x+62, aux_y+39, 3, 5), (aux_x+57, aux_y+30, 3, 5), (aux_x+54, aux_y+24, 3, 5),
                    (aux_x+65, aux_y+30, 3, 5), (aux_x+67, aux_y+34, 3, 5), (aux_x+68, aux_y+17, 3, 5),
                    (aux_x+70, aux_y+54, 3, 5), (aux_x+73, aux_y+52, 3, 5)
                ]
                objects_data_tree3 = [
                    (aux_x+14, aux_y+3, 3, 5), (aux_x+20, aux_y+3, 3, 5), (aux_x+8, aux_y+18, 3, 5), 
                    (aux_x+12, aux_y+18, 3, 5), (aux_x+12, aux_y+24, 3, 5), (aux_x+21, aux_y+23, 3, 5),
                    (aux_x+6, aux_y+31, 3, 5), (aux_x+15, aux_y+30, 3, 5), (aux_x+9, aux_y+32, 3, 5),
                    (aux_x+7, aux_y+35, 3, 5), (aux_x+5, aux_y+38, 3, 5), (aux_x+14, aux_y+34, 3, 5),
                    (aux_x+18, aux_y+34, 3, 5), (aux_x+22, aux_y+34, 3, 5), (aux_x+10, aux_y+40, 3, 5),
                    (aux_x+13, aux_y+39, 3, 5), (aux_x+23, aux_y+39, 3, 5), (aux_x+9, aux_y+43, 3, 5),
                    (aux_x+7, aux_y+43, 3, 5), (aux_x+21, aux_y+43, 3, 5), (aux_x+26, aux_y+44, 3, 5),
                    (aux_x+16, aux_y+47, 3, 5), (aux_x+19, aux_y+46, 3, 5), (aux_x+24, aux_y+46, 3, 5),
                    (aux_x+5, aux_y+52, 3, 5), (aux_x+8, aux_y+53, 3, 5), (aux_x+11, aux_y+50, 3, 5),
                    (aux_x+14, aux_y+53, 3, 5), (aux_x+17, aux_y+51, 3, 5), (aux_x+21, aux_y+54, 3, 5),
                    (aux_x+29, aux_y+52, 3, 5), (aux_x+41, aux_y+41, 3, 5), (aux_x+40, aux_y+31, 3, 5),
                    (aux_x+32, aux_y+25, 3, 5), (aux_x+55, aux_y+42, 3, 5), (aux_x+60, aux_y+43, 3, 5), 
                    (aux_x+66, aux_y+39, 3, 5), (aux_x+62, aux_y+28, 3, 5), (aux_x+70, aux_y+33, 3, 5),
                    (aux_x+50, aux_y+7, 3, 5)
                ]
                # Lixeiras - posicionadas estrategicamente
                objects_data_organico_lix = [(aux_x+76, aux_y+8, 1, 1, 'organico')]
                objects_data_metal_lix = [(aux_x+74, aux_y+8, 1, 1, 'metal')]
                objects_data_vidro_lix = [(aux_x+72, aux_y+8, 1, 1, 'vidro')]
                objects_data_plastico_lix = [(aux_x+70, aux_y+8, 1, 1, 'plastico')]
                objects_data_papel_lix = [(aux_x+68, aux_y+8, 1, 1, 'papel')]

            # Carregando árvores:
            for data in objects_data_tree:
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

            for data in objects_data_tree2:
                x, y, width, height = data
                tree2 = GameObject(
                    tree2_path,
                    world_x=x * TILE_SIZE,
                    world_y=y * TILE_SIZE,
                    width_tiles=width,
                    height_tiles=height,
                    collision=True
                )
                tree2.update_collision_rect()
                self.objects.append(tree2)

            for data in objects_data_tree3:
                x, y, width, height = data
                tree3 = GameObject(
                    tree3_path,
                    world_x=x * TILE_SIZE,
                    world_y=y * TILE_SIZE,
                    width_tiles=width,
                    height_tiles=height,
                    collision=True
                )
                tree3.update_collision_rect()
                self.objects.append(tree3)

            # Carregar lixeiras
            lixeira_paths = {
                'organico': organico_lixeira_path,
                'metal': metal_lixeira_path,
                'vidro': vidro_lixeira_path,
                'plastico': plastico_lixeira_path,
                'papel': papel_lixeira_path
            }

            for data_list, trash_type in [
                (objects_data_organico_lix, 'organico'),
                (objects_data_metal_lix, 'metal'),
                (objects_data_vidro_lix, 'vidro'),
                (objects_data_plastico_lix, 'plastico'),
                (objects_data_papel_lix, 'papel')
            ]:
                for data in data_list:
                    x, y, width, height, _ = data
                    lixeira = TrashBin(
                        lixeira_paths[trash_type],
                        x * TILE_SIZE,
                        y * TILE_SIZE,
                        trash_type,
                        width,
                        height
                    )
                    lixeira.update_collision_rect()
                    self.trash_bins.append(lixeira)
                    self.objects.append(lixeira)

            print(f"Carregadas {len(self.objects)} objetos no total")
            print(f"Carregadas {len(self.trash_bins)} lixeiras")

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

        # Sistema de inventário
        self.inventory = [None] * 5  # 5 slots de inventário
        self.selected_slot = 0
        self.max_items = 5

        self.width = TILE_SIZE
        self.height = TILE_SIZE

    def load_images(self):
        """Carrega as imagens reais do player da pasta res/"""
        images = {"up": [], "down": [], "left": [], "right": []}

        try:
            # skin_index 0 = personagem padrão
            folder = "res/player/"

            # Carregar imagens
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

    def get_collision_rect(self, x=None, y=None):
        """Retorna o retângulo de colisão com as dimensões personalizadas"""
        if x is None:
            x = self.world_x
        if y is None:
            y = self.world_y
        
        # Calcula a largura
        collision_width = int(self.width)
        # Calcula a altura (metade da altura)
        collision_height = int(self.height / 2)
        
        # Centraliza o retângulo de colisão horizontalmente
        collision_x = x + (self.width - collision_width) // 2
        # Coloca o retângulo de colisão na parte inferior do sprite
        collision_y = y + (self.height - collision_height)
        
        return pygame.Rect(int(collision_x), int(collision_y), collision_width, collision_height)

    def check_collision(self, new_x, new_y, tile_manager):
        """Verifica colisão com tiles e objetos usando a área de colisão personalizada"""
        # Usar o retângulo de colisão personalizado
        player_rect = self.get_collision_rect(new_x, new_y)

        # Verificar colisão com tiles de colisão
        tile_x1 = int(new_x / TILE_SIZE)
        tile_y1 = int(new_y / TILE_SIZE)
        tile_x2 = int((new_x + TILE_SIZE - 1) / TILE_SIZE)
        tile_y2 = int((new_y + TILE_SIZE - 1) / TILE_SIZE)

        for y in range(tile_y1, tile_y2 + 1):
            for x in range(tile_x1, tile_x2 + 1):
                if 0 <= y < len(tile_manager.map_tile_num) and 0 <= x < len(tile_manager.map_tile_num[0]):
                    tile_index = tile_manager.map_tile_num[y][x]
                    if tile_manager.tiles[tile_index].collision:
                        # Criar rect do tile
                        tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if player_rect.colliderect(tile_rect):
                            return True

        # Verificar colisão com objetos usando collision_rect
        for obj in tile_manager.objects:
            if obj.collision and obj.collision_rect:
                if player_rect.colliderect(obj.collision_rect):
                    return True

        return False

    def add_to_inventory(self, trash):
        """Adiciona lixo ao primeiro slot vazio do inventário"""
        for i in range(len(self.inventory)):
            if self.inventory[i] is None:
                self.inventory[i] = trash
                return True
        return False  # Inventário cheio

    def remove_from_inventory(self, slot):
        """Remove lixo do slot especificado"""
        if 0 <= slot < len(self.inventory) and self.inventory[slot] is not None:
            removed_trash = self.inventory[slot]
            self.inventory[slot] = None
            return removed_trash
        return None

    def get_inventory_count(self):
        """Retorna quantos slots estão ocupados"""
        return sum(1 for item in self.inventory if item is not None)

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

        # Seleção de slots do inventário
        if keys[pygame.K_1]:
            self.selected_slot = 0
        elif keys[pygame.K_2]:
            self.selected_slot = 1
        elif keys[pygame.K_3]:
            self.selected_slot = 2
        elif keys[pygame.K_4]:
            self.selected_slot = 3
        elif keys[pygame.K_5]:
            self.selected_slot = 4

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
        self.trashes = self.generate_trashes()
        self.score = 0
        self.max_score = 200
        self.start_time = pygame.time.get_ticks()
        
        self.game_duration = 600000  # 10 minutos em milissegundos
        self.game_over = False
        self.level_completed = False
        self.trash_collected = 0
        self.total_trashes = 20

        # Estado de pausa
        self.paused = False
        self.pause_start_time = 0
        self.total_paused_time = 0  # Acumula o tempo que o jogo ficou pausado

        # Para mostrar tempo de conclusão
        self.show_completion_time = False
        self.completion_time_display = 0
        self.completion_display_timer = 0

        # Fontes
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Debug flag: desenhar rects de colisão
        self.debug_draw_collision = False

        print(f"Player iniciado em: ({self.player.world_x}, {self.player.world_y})")

    def toggle_pause(self):
        """Alterna o estado de pausa e ajusta o temporizador"""
        if not self.game_over and not self.level_completed:
            self.paused = not self.paused
            
            if self.paused:
                # Inicia a pausa
                self.pause_start_time = pygame.time.get_ticks()
                print("Jogo pausado´em: {self.pause_start_time}ms")
            else:
                if self.pause_start_time > 0:
                    # Termina a pausa e acumula o tempo pausado
                    pause_duration = pygame.time.get_ticks() - self.pause_start_time

                    self.total_paused_time += pause_duration
                    
                    print(f"   Jogo despausado. Pausa: {pause_duration}ms")
                    print(f"   Tempo total pausado: {self.total_paused_time}ms")

                self.pause_start_time = 0

    def get_adjusted_time(self):
        """Retorna o tempo de jogo ajustado (excluindo o tempo pausado)"""
        try:
            current_time = pygame.time.get_ticks()

            if self.paused:
                current_time = self.pause_start_time
            
            elapsed = current_time - self.start_time - self.total_paused_time

            if elapsed < 0:
                print(f"⚠️ get_adjusted_time: tempo negativo! {elapsed}ms")
                print(f"  current_time: {current_time}")
                print(f"  start_time: {self.start_time}")
                print(f"  total_paused_time: {self.total_paused_time}")
            
            return max(0, elapsed)  # Nunca retornar negativo
        
        except Exception as e:
            print(f"Erro em get_adjusted_time: {e}")
            return 45000


    def load_trash_images(self):
        """Carrega todas as imagens de lixo das pastas organizadas"""
        trash_images = {trash_type: [] for trash_type in TRASH_TYPES}
        
        for trash_type in TRASH_TYPES:
            trash_folder = f"res/trashes/{trash_type}"
            if os.path.exists(trash_folder):
                try:
                    # Listar todos os arquivos PNG da pasta
                    for file in os.listdir(trash_folder):
                        if file.lower().endswith('.png'):
                            image_path = os.path.join(trash_folder, file)
                            trash_images[trash_type].append(image_path)
                    print(f"Carregadas {len(trash_images[trash_type])} imagens para {trash_type}")
                except Exception as e:
                    print(f"Erro ao carregar imagens de {trash_type}: {e}")
            else:
                print(f"Pasta não encontrada: {trash_folder}")
        
        return trash_images

    def is_valid_position(self, x, y, used_positions, buffer=2):
        """Verifica se a posição é válida (evita cantos, objetos e áreas inacessíveis)"""
        # Evitar cantos do mapa
        if x < 3 or x >= MAX_WORLD_COL - 3 or y < 3 or y >= MAX_WORLD_ROW - 3:
            return False
        
        # Evitar posições muito próximas (buffer reduzido pois os lixos são maiores)
        for used_x, used_y in used_positions:
            if abs(x - used_x) < buffer and abs(y - used_y) < buffer:
                return False
        
        # Verificar colisão com objetos (árvores, etc) - agora considerando tamanho completo
        world_x = x * TILE_SIZE
        world_y = y * TILE_SIZE
        trash_rect = pygame.Rect(world_x, world_y, TILE_SIZE, TILE_SIZE)
        
        # Verificar colisão com objetos
        for obj in self.tile_manager.objects:
            if obj.collision and obj.collision_rect:
                if trash_rect.colliderect(obj.collision_rect):
                    return False
        
        # Verificar colisão com tiles de água/obstáculos
        tile_x = x
        tile_y = y
        
        if 0 <= tile_y < len(self.tile_manager.map_tile_num) and 0 <= tile_x < len(self.tile_manager.map_tile_num[0]):
            tile_index = self.tile_manager.map_tile_num[tile_y][tile_x]
            if tile_index >= 2 and tile_index <= 28:  # Tiles
                if self.tile_manager.tiles[tile_index].collision:
                    return False
        
        return True

    def generate_trashes(self):
        """Gera 20 lixos (4 de cada tipo) em posições válidas no mapa"""
        trash_images = self.load_trash_images()
        trashes = []
        used_positions = set()
        
        # Para cada tipo de lixo, gerar 4 instâncias
        for trash_type in TRASH_TYPES:
            images_for_type = trash_images[trash_type]
            if not images_for_type:
                print(f"⚠️ Nenhuma imagem encontrada para {trash_type}, usando placeholder")
                # Criar algumas imagens placeholder se não houver imagens
                images_for_type = [None] * 4
            
            for i in range(4):  # 4 lixos de cada tipo
                attempts = 0
                max_attempts = 100  # Evitar loop infinito
                
                while attempts < max_attempts:
                    x = random.randint(5, MAX_WORLD_COL - 5)
                    y = random.randint(5, MAX_WORLD_ROW - 5)
                    
                    if (x, y) not in used_positions and self.is_valid_position(x, y, used_positions):
                        # Escolher uma imagem aleatória para este tipo
                        if images_for_type:
                            image_path = random.choice(images_for_type)
                        else:
                            image_path = None
                        
                        trash = Trash(x, y, trash_type, image_path)
                        trashes.append(trash)
                        used_positions.add((x, y))
                        print(f"✅ Lixo {trash_type} posicionado em ({x}, {y})")
                        break
                    
                    attempts += 1
                
                if attempts >= max_attempts:
                    print(f"⚠️ Não foi possível encontrar posição válida para {trash_type} {i+1}")
        
        print(f"🎯 Total de lixos gerados: {len(trashes)}")
        return trashes
    
    def start_game_timer(self):
        """Inicia o timer do jogo - deve ser chamado quando o jogo realmente começa"""
        if self.start_time is None:
            self.start_time = pygame.time.get_ticks()
            print(f"⏱️ Timer do jogo iniciado em: {self.start_time}ms")
            return True
        return False

    def update_camera(self):
        """Atualiza a posição da câmera para seguir o player"""
        target_x = self.player.world_x - SCREEN_WIDTH // 2 + TILE_SIZE // 2
        target_y = self.player.world_y - SCREEN_HEIGHT // 2 + TILE_SIZE // 2

        self.camera_x = max(0, min(target_x, WORLD_WIDTH - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, WORLD_HEIGHT - SCREEN_HEIGHT))

    def check_trash_collision(self):
        """Verifica colisão com lixos"""
        for trash in self.trashes:
            if trash.check_collision(self.player.world_x, self.player.world_y):
                if not trash.collected and self.player.get_inventory_count() < self.player.max_items:
                    if self.player.add_to_inventory(trash):
                        trash.collected = True
                        self.trash_collected += 1
                        print(f"Lixo coletado! Tipo: {trash.trash_type}. Total: {self.trash_collected}")

    def check_trash_bin_interaction(self):
        """Verifica interação com lixeiras"""
        player_rect = pygame.Rect(self.player.world_x, self.player.world_y, TILE_SIZE, TILE_SIZE)
        
        for trash_bin in self.tile_manager.trash_bins:
            if player_rect.colliderect(trash_bin.collision_rect):
                # Verificar se há lixo selecionado no inventário
                selected_trash = self.player.inventory[self.player.selected_slot]
                if selected_trash:
                    if selected_trash.trash_type == trash_bin.trash_type:
                        # Lixo correto - adicionar pontos
                        self.score += 10
                        self.player.remove_from_inventory(self.player.selected_slot)
                        print(f"Lixo descartado corretamente! +10 pontos. Total: {self.score}")

                        # CAPTURAR TEMPO EXATO QUANDO ATINGIR 160 PONTOS
                        if self.score == 160 and not self.level_completed:
                            # Capturar o tempo exato neste momento
                            current_time = self.get_adjusted_time()
                            print(f"🎯 PONTUAÇÃO 160 ATINGIDA! Tempo atual: {current_time}ms")
                            
                            # Marcar como completado
                            self.level_completed = True
                            
                            # Formatar e mostrar o tempo
                            minutes = current_time // 60000
                            seconds = (current_time % 60000) // 1000
                            milliseconds = current_time % 1000
                            print(f"🏁 NÍVEL COMPLETADO em: {minutes:02d}:{seconds:02d}.{milliseconds:03d}")
                            
                            # Mostrar tempo na tela por 3 segundos
                            self.show_completion_time = True
                            self.completion_time_display = current_time
                        
                        # Verificar se nível foi completado
                        if self.score >= self.max_score * 0.8:  # 80% do máximo
                            self.level_completed = True
                    else:
                        # Lixo errado - remove do inventário SEM penalidade
                        self.player.remove_from_inventory(self.player.selected_slot)
                        print(f"Lixo descartado incorretamente! Lixeira: {trash_bin.trash_type}, Lixo: {selected_trash.trash_type}. Lixo removido do inventário.")
                        # A pontuação permanece a mesma, sem subtração

    def draw_completion_time(self):
        """Mostra o tempo de conclusão na tela por alguns segundos"""
        if self.show_completion_time and self.completion_time_display > 0:
            # Formatar o tempo
            minutes = self.completion_time_display // 60000
            seconds = (self.completion_time_display % 60000) // 1000
            milliseconds = self.completion_time_display % 1000
            time_text = f"Tempo: {minutes:02d}:{seconds:02d}.{milliseconds:03d}"
            
            # Criar overlay
            overlay = pygame.Surface((400, 100))
            overlay.set_alpha(200)
            overlay.fill((0, 50, 0))
            overlay_rect = overlay.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            self.screen.blit(overlay, overlay_rect)
            
            # Textos
            title = self.font.render("NÍVEL COMPLETADO!", True, (0, 255, 0))
            time_render = self.font.render(time_text, True, (255, 255, 255))
            
            self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//2 - 30))
            self.screen.blit(time_render, (SCREEN_WIDTH//2 - time_render.get_width()//2, SCREEN_HEIGHT//2 + 10))
            
            # Contador para esconder após 3 segundos
            self.completion_display_timer += 1
            if self.completion_display_timer > 180:  # 3 segundos a 60 FPS
                self.show_completion_time = False

    def draw_inventory(self):
        """Desenha o inventário na tela"""
        inventory_width = 350 
        inventory_height = 80  
        inventory_x = (SCREEN_WIDTH - inventory_width) // 2
        inventory_y = SCREEN_HEIGHT - inventory_height - 10
        
        # Fundo do inventário
        inventory_bg = pygame.Surface((inventory_width, inventory_height))
        inventory_bg.set_alpha(200)
        inventory_bg.fill((50, 50, 50))
        self.screen.blit(inventory_bg, (inventory_x, inventory_y))
        
        slot_width = 60  
        slot_height = 60
        slot_spacing = 10
        start_x = inventory_x + (inventory_width - (5 * slot_width + 4 * slot_spacing)) // 2
        
        for i in range(5):
            slot_x = start_x + i * (slot_width + slot_spacing)
            slot_y = inventory_y + 10
            
            # Desenhar slot
            slot_color = (200, 200, 100) if i == self.player.selected_slot else (100, 100, 100)
            pygame.draw.rect(self.screen, slot_color, (slot_x, slot_y, slot_width, slot_height))
            pygame.draw.rect(self.screen, (255, 255, 255), (slot_x, slot_y, slot_width, slot_height), 2)
            
            # Desenhar número do slot
            number_text = self.small_font.render(str(i + 1), True, (255, 255, 255))
            self.screen.blit(number_text, (slot_x + 5, slot_y + 5))
            
            # Desenhar lixo no slot, se houver
            trash = self.player.inventory[i]
            if trash:
                if trash.image:
                    # Redimensionar imagem para caber no slot maior
                    trash_img = pygame.transform.scale(trash.image, (slot_width - 10, slot_height - 10))
                    self.screen.blit(trash_img, (slot_x + 5, slot_y + 5))
                else:
                    pygame.draw.rect(self.screen, trash.color, 
                                (slot_x + 5, slot_y + 5, slot_width - 10, slot_height - 10))
                
                # Mostrar tipo do lixo
                type_text = self.small_font.render(trash.trash_type[:3], True, (255, 255, 255))
                self.screen.blit(type_text, (slot_x + slot_width // 2 - 10, slot_y + slot_height - 15))

    def draw_hud(self):
        """HUD moderna, equilibrada e sem fundo opaco"""
        # --- Cores ---
        text_color = (255, 255, 255)
        shadow_color = (0, 0, 0)
        bar_bg_color = (60, 60, 60)
        bar_fill_color = (0, 200, 100)

        # --- Cálculos principais ---
        time_elapsed = self.get_adjusted_time()
        time_left = max(0, self.game_duration - time_elapsed)
        minutes = time_left // 60000
        seconds = (time_left % 60000) // 1000
        time_text = f"Tempo: {minutes:02d}:{seconds:02d}"
        score_text = f"Pontos: {self.score}/{self.max_score}"
        items_text = f"Lixos: {self.trash_collected}/{self.total_trashes}"
        level_text = f"Nível {self.level}"
        player_text = f"{self.nickname}"

        # --- Barra centralizada ---
        collected_ratio = self.score / self.max_score
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

    def draw_pause_screen(self):
        """Desenha a tela de pausa"""
        # Overlay semi-transparente
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Caixa de pausa
        pause_box = pygame.Surface((400, 200))
        pause_box.set_alpha(220)
        pause_box.fill((40, 40, 60))
        pause_box_rect = pause_box.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(pause_box, pause_box_rect)
        
        # Textos
        pause_text = self.font.render("JOGO PAUSADO", True, (255, 255, 100))
        instructions = [
            "CONTROLES:",
            "WASD / Setas - Movimentar",
            "1-5 - Selecionar slot do inventário",
            "P - Pausar/Despausar",
            "ESC - Sair do jogo"
        ]
        
        self.screen.blit(pause_text, (SCREEN_WIDTH//2 - pause_text.get_width()//2, pause_box_rect.top + 30))
        
        # Instruções
        y_offset = pause_box_rect.top + 80
        for instruction in instructions:
            inst_text = self.small_font.render(instruction, True, (200, 200, 255))
            self.screen.blit(inst_text, (SCREEN_WIDTH//2 - inst_text.get_width()//2, y_offset))
            y_offset += 25

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

    def get_debug_times(self):
        """Retorna informações detalhadas sobre os tempos para debug"""
        current_time = pygame.time.get_ticks()
        elapsed_since_start = current_time - self.start_time
        adjusted_time = self.get_adjusted_time()
        
        print(f"\n🔍 DEBUG DETALHADO DE TEMPOS:")
        print(f"  Tempo atual do sistema: {current_time}ms")
        print(f"  Tempo de início do jogo: {self.start_time}ms")
        print(f"  Tempo desde o início: {elapsed_since_start}ms ({elapsed_since_start/1000:.1f}s)")
        print(f"  Tempo total pausado: {self.total_paused_time}ms")
        print(f"  Tempo ajustado (sem pausas): {adjusted_time}ms ({adjusted_time/1000:.1f}s)")
        print(f"  Jogo pausado? {self.paused}")
        if self.paused:
            print(f"  Tempo de início da pausa: {self.pause_start_time}ms")
        
        return adjusted_time

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Toggle pause com a tecla P
                    elif event.key == pygame.K_p:
                        self.toggle_pause()
                    # Toggle debug para visualizar rects de colisão
                    elif event.key == pygame.K_F1:
                        self.debug_draw_collision = not self.debug_draw_collision

            if not self.game_over and not self.level_completed and not self.paused:
                keys = pygame.key.get_pressed()
                self.player.update(keys, self.tile_manager)
                self.update_camera()
                self.check_trash_collision()
                self.check_trash_bin_interaction()
                
                # Verificar fim de jogo por tempo (usando tempo ajustado)
                time_elapsed = self.get_adjusted_time()
                if time_elapsed >= self.game_duration:
                    self.game_over = True

            # Renderização
            self.screen.fill((0, 0, 0))

            # 1. Terreno
            self.tile_manager.draw_ground(self.screen, self.camera_x, self.camera_y)

            # 2. Lixos
            for trash in self.trashes:
                trash.draw(self.screen, self.camera_x, self.camera_y)

            # 3+4. Depth-sorting: ordenar e desenhar objetos e player com base em bottom_y
            # Construir lista de drawables (objetos + player + lixos)
            drawables = []
            # adicionar objetos
            for obj in self.tile_manager.objects:
                # garantir collision_rect atualizado
                obj.update_collision_rect()
                drawables.append(obj)
            # adicionar lixos não coletados
            for trash in self.trashes:
                if not trash.collected:
                    drawables.append(trash)
            # adicionar player
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
                elif isinstance(d, Trash):
                    d.draw(self.screen, self.camera_x, self.camera_y)
                elif isinstance(d, Player):
                    d.draw(self.screen, self.camera_x, self.camera_y)

            # 5. Inventário
            self.draw_inventory()

            # 6. HUD
            self.draw_hud()

            # 6.5. Mostrar tempo de conclusão (se aplicável)
            if self.show_completion_time:
                self.draw_completion_time()

            # 7. Telas de pausa/fim de jogo
            if self.paused:
                self.draw_pause_screen()
            elif self.game_over:
                self.draw_game_over()
            elif self.level_completed:
                self.draw_level_complete()

            pygame.display.flip()
            self.clock.tick(FPS)

        # CAPTURAR O TEMPO FINAL ANTES DE FECHAR O PYGAME
        if self.level_completed:
            # Capturar o tempo ANTES de pygame.quit()
            final_time = self.get_adjusted_time()
            print(f"\n⏱️ TEMPO FINAL CAPTURADO ANTES DE FECHAR: {final_time}ms")
            
            # Se o tempo for 0 ou muito baixo, usar um tempo real estimado
            if final_time < 100:  # Menos de 0.1 segundos
                print(f"⚠️ Tempo inválido detectado: {final_time}ms")
                
                # Tentar calcular baseado no tempo do sistema
                import time
                # Estimar baseado no tempo real de execução
                # Vamos usar 45 segundos como padrão para jogos completados
                final_time = 45000  # 45 segundos
                print(f"⚠️ Usando tempo estimado de 45 segundos: {final_time}ms")
        else:
            final_time = 600000  # Tempo máximo se não completou

        pygame.quit()

        # Garantir que o tempo seja válido
        if final_time < 30000 and self.level_completed:
            print(f"⚠️ Ajustando tempo mínimo para 30 segundos")
            final_time = 30000

        # Formatar o tempo
        minutes = final_time // 60000
        seconds = (final_time % 60000) // 1000
        milliseconds = final_time % 1000
        time_formatted = f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        
        # DEBUG: Mostrar informações
        print(f"\n=== TEMPO FINAL CALCULADO ===")
        print(f"Tempo em milissegundos: {final_time}ms")
        print(f"Tempo formatado: {time_formatted}")
        print(f"Tempo em segundos: {final_time/1000:.1f}s")
        print(f"Nível completado: {self.level_completed}")
        print(f"Pontuação: {self.score}/{self.max_score}")

        # Retornar resultado
        success = self.level_completed and self.score >= 160
        print(f"\n=== RESULTADO ===")
        print(f"Jogador: {self.nickname}")
        print(f"Nível: {self.level}")
        print(f"Pontuação: {self.score}/{self.max_score}")
        print(f"Tempo de conclusão: {time_formatted}")
        print(f"Status: {'APROVADO' if success else 'REPROVADO'}")

        # Se o nível foi completado com sucesso, salvar o tempo
        if success:
            # Aqui você pode enviar os dados para o servidor
            # Vamos usar um arquivo temporário para comunicação
            import json
            import os
            import time as system_time

            result_data = {
                'nickname': self.nickname,
                'level': self.level,
                'completion_time': int(final_time),
                'score': self.score,
                'success': success,
                'timestamp': system_time.time()
            }
            
            try:
                # Salvar em um arquivo que o servidor pode ler
                with open('game_result.json', 'w') as f:
                    json.dump(result_data, f, indent=2)
                print("Resultado salvo em game_result.json: {result_data}")
                print(f"Conteudo do arquivo: {result_data}")

                if os.path.exists('game_result.json'):
                    file_size = os.path.getsize('game_result.json')
                    print(f"Tamanho do arquivo salvo: {file_size} bytes")
                else:
                    print("Arquivo não foi criado.")

            except Exception as e:
                print(f"Erro ao salvar resultado: {e}")
                import traceback
                traceback.print_exc()

        return success

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--nickname', required=True)
    parser.add_argument('--skin', type=int, required=True)
    parser.add_argument('--level', type=int, required=True)

    args = parser.parse_args()

    print("=== INICIANDO ECOVALLEY ===")
    print(f"Jogador: {args.nickname}")
    print(f"Skin: {args.skin}")
    print(f"Nível: {args.level}")

    game = Game(args.nickname, args.skin, args.level)
    success = game.run()

    if success:
        import json
        import requests
        import os 
        import sys

        try:
            result_file = 'game_result.json'
            if os.path.exists(result_file):
                print("Tentando enviar resultado para o servidor...")

                with open('game_result.json', 'r') as f:
                    result_data = json.load(f)

                print("Dados a serem enviados: {result_data}")
                
                try:
                    # Enviar para o servidor
                    response = requests.post(
                        'http://localhost:5000/api/save-ranking',
                        json=result_data,
                        timeout=10
                    )

                    print(f"Resposta do servidor: {response.status_code} - {response.text}")

                    if response.status_code == 200:
                        response_data = response.json()
                        print(f"Resposta do servidor: {response_data}")

                        if response_data.get('success'):
                            print("Resultado enviado com sucesso para o servidor!")

                        else:
                            print(f"Servidor respondeu com erro: {response_data}")
                    else:
                        print(f"Erro HTTP {response.status_code}")
                        print(f"Detalhes: {response.text}")

                except requests.exceptions.ConnectionError:
                    print("Não foi possível conectar ao servidor (ConnectionError).")
                except requests.exceptions.Timeout:
                    print("Tempo de conexão esgotado (Timeout).")
                except Exception as e:
                    print(f"Erro ao enviar resultado: {e}")
                    import traceback
                    traceback.print_exc()
                
                #Limpar arquivo
                try:
                    os.remove(result_file)
                    print("Arquivo temporário removido.")
                except:
                    print("Não foi possível remover o arquivo temporário.")
            else:
                print("Arquivo de resultado não encontrado: {result_file}")

        except Exception as e:
            print(f"Erro ao processar resultado salvo: {e}")
            import traceback
            traceback.print_exc()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()