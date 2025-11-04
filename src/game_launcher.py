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