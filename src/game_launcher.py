import pygame
import sys
import argparse
import os
import random

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
    def _init_(self, image, collision=False):
        self.image = image
        self.collision = collision

# ========================
# TILE MANAGER
# ========================
class TileManager:
    def _init_(self, tile_size, level):
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
                    (8, 8, 3, 5), (12, 12, 3, 5), (16, 16, 3, 5),
                    (20, 20, 3, 5), (24, 24, 3, 5), (28, 28, 3, 5),
                    (32, 32, 3, 5), (36, 36, 3, 5), (40, 40, 3, 5),
                    (44, 44, 3, 5), (48, 48, 3, 5), (52, 52, 3, 5),
                    (56, 56, 3, 5), (15, 30, 3, 5), (30, 15, 3, 5)
                ]
                objects_data_tree2 = [
                    (10, 10, 3, 5), (14, 14, 3, 5), (18, 18, 3, 5),
                    (22, 22, 3, 5), (26, 26, 3, 5), (30, 30, 3, 5),
                    (34, 34, 3, 5), (38, 38, 3, 5), (42, 42, 3, 5),
                    (46, 46, 3, 5), (50, 50, 3, 5), (54, 54, 3, 5),
                    (58, 58, 3, 5), (20, 35, 3, 5), (35, 20, 3, 5)
                ]
                objects_data_tree3 = [
                    (15, 15, 3, 5), (25, 25, 3, 5), (35, 35, 3, 5),
                    (45, 45, 3, 5), (55, 55, 3, 5)
                ]
                # Lixeiras para nível 2
                objects_data_organico_lix = [(10, 60, 1, 1, 'organico')]
                objects_data_metal_lix = [(15, 60, 1, 1, 'metal')]
                objects_data_vidro_lix = [(20, 60, 1, 1, 'vidro')]
                objects_data_plastico_lix = [(25, 60, 1, 1, 'plastico')]
                objects_data_papel_lix = [(30, 60, 1, 1, 'papel')]
            else:
                # Nível 3 - alguns objetos
                objects_data_tree = [
                    (5, 5, 3, 5), (10, 10, 3, 5), (15, 15, 3, 5),
                    (20, 20, 3, 5), (25, 25, 3, 5), (30, 30, 3, 5),
                    (35, 35, 3, 5), (40, 40, 3, 5), (45, 45, 3, 5),
                    (50, 50, 3, 5), (55, 55, 3, 5), (60, 60, 3, 5),
                    (8, 20, 3, 5), (12, 25, 3, 5), (18, 30, 3, 5),
                    (22, 35, 3, 5), (28, 40, 3, 5), (32, 45, 3, 5),
                    (38, 50, 3, 5), (42, 55, 3, 5)
                ]
                objects_data_tree2 = [
                    (7, 7, 3, 5), (12, 12, 3, 5), (17, 17, 3, 5),
                    (22, 22, 3, 5), (27, 27, 3, 5), (32, 32, 3, 5),
                    (37, 37, 3, 5), (42, 42, 3, 5), (47, 47, 3, 5),
                    (52, 52, 3, 5), (57, 57, 3, 5), (62, 62, 3, 5),
                    (10, 22, 3, 5), (14, 27, 3, 5), (20, 32, 3, 5),
                    (24, 37, 3, 5), (30, 42, 3, 5), (34, 47, 3, 5),
                    (40, 52, 3, 5), (44, 57, 3, 5)
                ]
                objects_data_tree3 = [
                    (20, 20, 3, 5), (30, 30, 3, 5), (40, 40, 3, 5),
                    (50, 50, 3, 5), (60, 60, 3, 5)
                ]
                # Lixeiras para nível 3
                objects_data_organico_lix = [(60, 10, 1, 1, 'organico')]
                objects_data_metal_lix = [(65, 10, 1, 1, 'metal')]
                objects_data_vidro_lix = [(70, 10, 1, 1, 'vidro')]
                objects_data_plastico_lix = [(75, 10, 1, 1, 'plastico')]
                objects_data_papel_lix = [(80, 10, 1, 1, 'papel')]

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
    def _init_(self):
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
    def _init_(self, game, skin_index=0):
        super()._init_()
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