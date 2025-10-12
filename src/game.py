import pygame
import sys
import math
import requests
import threading
import time

# Inicialização do Pygame
pygame.init()

# Configurações da tela
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Game - Python")

# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# Configurações do jogo
TILE_SIZE = 48
PLAYER_SPEED = 5
GAME_TIME = 600  # 10 minutos em segundos

class Entity:
    def __init__(self, x, y):
        self.world_x = x
        self.world_y = y
        self.speed = PLAYER_SPEED
        self.direction = "down"
        self.sprite_counter = 0
        self.sprite_num = 1

class Player(Entity):
    def __init__(self, x, y, skin_index):
        super().__init__(x, y)
        self.skin_index = skin_index
        self.width = TILE_SIZE
        self.height = TILE_SIZE
        self.load_skins()
    
    def load_skins(self):
        # Criar skins básicas (em um projeto real, carregaria imagens)
        self.skins = []
        colors = [RED, GREEN, BLUE, (255, 255, 0)]  # Diferentes cores para skins
        
        for color in colors:
            # Criar surface para cada skin
            skin_surface = pygame.Surface((TILE_SIZE, TILE_SIZE))
            skin_surface.fill(color)
            # Adicionar detalhes para diferenciar as skins
            pygame.draw.circle(skin_surface, WHITE, (TILE_SIZE//2, TILE_SIZE//3), 8)
            pygame.draw.rect(skin_surface, BLACK, (TILE_SIZE//4, TILE_SIZE//2, TILE_SIZE//2, TILE_SIZE//3))
            self.skins.append(skin_surface)
    
    def update(self, keys, obstacles):
        new_x, new_y = self.world_x, self.world_y
        
        if keys[pygame.K_w]:
            self.direction = "up"
            new_y -= self.speed
        elif keys[pygame.K_s]:
            self.direction = "down"
            new_y += self.speed
        elif keys[pygame.K_a]:
            self.direction = "left"
            new_x -= self.speed
        elif keys[pygame.K_d]:
            self.direction = "right"
            new_x += self.speed
        
        # Verificar colisões antes de atualizar posição
        if not self.check_collision(new_x, new_y, obstacles):
            self.world_x = new_x
            self.world_y = new_y
        
        # Animação
        if any([keys[pygame.K_w], keys[pygame.K_s], keys[pygame.K_a], keys[pygame.K_d]]):
            self.sprite_counter += 1
            if self.sprite_counter > 7:
                self.sprite_num = 2 if self.sprite_num == 1 else 1
                self.sprite_counter = 0
    
    def check_collision(self, x, y, obstacles):
        # Criar rect do jogador na nova posição
        player_rect = pygame.Rect(x, y, self.width, self.height)
        
        for obstacle in obstacles:
            if player_rect.colliderect(obstacle):
                return True
        return False
    
    def draw(self, surface, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        
        # Desenhar a skin selecionada
        if 0 <= self.skin_index < len(self.skins):
            surface.blit(self.skins[self.skin_index], (screen_x, screen_y))
        else:
            pygame.draw.rect(surface, RED, (screen_x, screen_y, self.width, self.height))

class GameObject:
    def __init__(self, x, y, width, height, color, collision=True):
        self.world_x = x
        self.world_y = y
        self.width = width * TILE_SIZE
        self.height = height * TILE_SIZE
        self.color = color
        self.collision = collision
    
    def draw(self, surface, camera_x, camera_y):
        screen_x = self.world_x - camera_x
        screen_y = self.world_y - camera_y
        pygame.draw.rect(surface, self.color, (screen_x, screen_y, self.width, self.height))
    
    def get_rect(self):
        return pygame.Rect(self.world_x, self.world_y, self.width, self.height)

class TileManager:
    def __init__(self, level):
        self.level = level
        self.tiles = []
        self.objects = []
        self.load_level()
    
    def load_level(self):
        # Configurações diferentes para cada nível
        if self.level == 1:
            self.load_level_1()
        elif self.level == 2:
            self.load_level_2()
        elif self.level == 3:
            self.load_level_3()
    
    def load_level_1(self):
        # Árvores (obstáculos)
        self.objects.append(GameObject(3 * TILE_SIZE, 3 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(10 * TILE_SIZE, 8 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(15 * TILE_SIZE, 5 * TILE_SIZE, 2, 3, (34, 139, 34)))
        
        # Pedras
        self.objects.append(GameObject(7 * TILE_SIZE, 12 * TILE_SIZE, 1, 1, (128, 128, 128)))
        self.objects.append(GameObject(20 * TILE_SIZE, 15 * TILE_SIZE, 1, 1, (128, 128, 128)))
        
        # Água (obstáculo)
        self.objects.append(GameObject(12 * TILE_SIZE, 2 * TILE_SIZE, 4, 2, (0, 0, 255)))
    
    def load_level_2(self):
        # Mais obstáculos para nível 2
        self.objects.append(GameObject(5 * TILE_SIZE, 5 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(12 * TILE_SIZE, 10 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(18 * TILE_SIZE, 7 * TILE_SIZE, 2, 3, (34, 139, 34)))
        
        # Mais água
        self.objects.append(GameObject(8 * TILE_SIZE, 3 * TILE_SIZE, 3, 2, (0, 0, 255)))
        self.objects.append(GameObject(15 * TILE_SIZE, 12 * TILE_SIZE, 2, 3, (0, 0, 255)))
    
    def load_level_3(self):
        # Nível 3 ainda mais desafiador
        self.objects.append(GameObject(4 * TILE_SIZE, 4 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(10 * TILE_SIZE, 8 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(16 * TILE_SIZE, 12 * TILE_SIZE, 2, 3, (34, 139, 34)))
        self.objects.append(GameObject(22 * TILE_SIZE, 6 * TILE_SIZE, 2, 3, (34, 139, 34)))
        
        # Muita água
        self.objects.append(GameObject(6 * TILE_SIZE, 2 * TILE_SIZE, 4, 2, (0, 0, 255)))
        self.objects.append(GameObject(14 * TILE_SIZE, 4 * TILE_SIZE, 3, 3, (0, 0, 255)))
        self.objects.append(GameObject(20 * TILE_SIZE, 10 * TILE_SIZE, 2, 4, (0, 0, 255)))
    
    def get_obstacles(self):
        return [obj.get_rect() for obj in self.objects if obj.collision]
    
    def draw(self, surface, camera_x, camera_y):
        # Desenhar fundo (grama)
        for x in range(0, SCREEN_WIDTH + TILE_SIZE, TILE_SIZE):
            for y in range(0, SCREEN_HEIGHT + TILE_SIZE, TILE_SIZE):
                world_x = x + camera_x - (camera_x % TILE_SIZE)
                world_y = y + camera_y - (camera_y % TILE_SIZE)
                
                # Padrão xadrez para visualização do movimento
                if ((world_x // TILE_SIZE) + (world_y // TILE_SIZE)) % 2 == 0:
                    color = (100, 200, 100)  # Verde claro
                else:
                    color = (80, 180, 80)    # Verde escuro
                
                screen_x = world_x - camera_x
                screen_y = world_y - camera_y
                
                pygame.draw.rect(surface, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
        
        # Desenhar objetos
        for obj in self.objects:
            obj.draw(surface, camera_x, camera_y)

class Game:
    def __init__(self, nickname, skin_index, level):
        self.nickname = nickname
        self.skin_index = skin_index
        self.level = level
        
        # Inicializar componentes do jogo
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, skin_index)
        self.tile_manager = TileManager(level)
        self.camera_x = 0
        self.camera_y = 0
        
        # Sistema de pontuação e tempo
        self.score = 0
        self.max_score = 200
        self.start_time = time.time()
        self.elapsed_time = 0
        self.game_over = False
        self.level_completed = False
        
        # Coletáveis
        self.collectibles = self.generate_collectibles()
        
        # Fonte para texto
        self.font = pygame.font.Font(None, 36)
    
    def generate_collectibles(self):
        collectibles = []
        positions = [
            (5 * TILE_SIZE, 5 * TILE_SIZE),
            (15 * TILE_SIZE, 8 * TILE_SIZE),
            (8 * TILE_SIZE, 15 * TILE_SIZE),
            (20 * TILE_SIZE, 12 * TILE_SIZE),
            (12 * TILE_SIZE, 20 * TILE_SIZE)
        ]
        
        for pos in positions:
            collectibles.append(pygame.Rect(pos[0], pos[1], 20, 20))
        
        return collectibles
    
    def update_camera(self):
        # Camera segue o jogador
        target_x = self.player.world_x - SCREEN_WIDTH // 2
        target_y = self.player.world_y - SCREEN_HEIGHT // 2
        
        # Limitar câmera aos limites do mundo (simplificado)
        world_width = SCREEN_WIDTH * 3
        world_height = SCREEN_HEIGHT * 3
        
        self.camera_x = max(0, min(target_x, world_width - SCREEN_WIDTH))
        self.camera_y = max(0, min(target_y, world_height - SCREEN_HEIGHT))
    
    def check_collectible_collision(self):
        player_rect = pygame.Rect(self.player.world_x, self.player.world_y, 
                                 self.player.width, self.player.height)
        
        for collectible in self.collectibles[:]:
            if player_rect.colliderect(collectible):
                self.collectibles.remove(collectible)
                self.score += 40  # 40 pontos por coletável (Posso mudar depois)
                
                if self.score >= self.max_score * 0.8:  # 80% do máximo (Posso mudar depois)
                    self.level_completed = True
    
    def update(self, keys):
        if self.game_over or self.level_completed:
            return
        
        # Atualizar tempo
        self.elapsed_time = time.time() - self.start_time
        
        if self.elapsed_time >= GAME_TIME:
            self.game_over = True
            return
        
        # Atualizar jogador
        obstacles = self.tile_manager.get_obstacles()
        self.player.update(keys, obstacles)
        
        # Verificar colisões com coletáveis
        self.check_collectible_collision()
        
        # Atualizar câmera
        self.update_camera()
    
    def draw(self, surface):
        # Limpar tela
        surface.fill(BLACK)
        
        # Desenhar mundo
        self.tile_manager.draw(surface, self.camera_x, self.camera_y)
        
        # Desenhar coletáveis
        for collectible in self.collectibles:
            screen_x = collectible.x - self.camera_x
            screen_y = collectible.y - self.camera_y
            pygame.draw.circle(surface, (255, 215, 0),  # Cor +/- dourada
                             (screen_x + 10, screen_y + 10), 10)
        
        # Desenhar jogador
        self.player.draw(surface, self.camera_x, self.camera_y)
        
        # Desenhar HUD
        self.draw_hud(surface)
        
        # Mensagens de fim de jogo
        if self.game_over:
            self.draw_game_over(surface)
        elif self.level_completed:
            self.draw_level_completed(surface)
    
    def draw_hud(self, surface):
        # Tempo restante
        time_left = max(0, GAME_TIME - self.elapsed_time)
        minutes = int(time_left // 60)
        seconds = int(time_left % 60)
        time_text = self.font.render(f"Tempo: {minutes:02d}:{seconds:02d}", True, WHITE)
        surface.blit(time_text, (10, 10))
        
        # Pontuação
        score_text = self.font.render(f"Pontuação: {self.score}/{self.max_score}", True, WHITE)
        surface.blit(score_text, (10, 50))
        
        # Nível
        level_text = self.font.render(f"Nível: {self.level}", True, WHITE)
        surface.blit(level_text, (10, 90))
        
        # Progresso
        progress = min(100, int((self.score / self.max_score) * 100))
        progress_text = self.font.render(f"Progresso: {progress}%", True, WHITE)
        surface.blit(progress_text, (10, 130))
    
    def draw_game_over(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("TEMPO ESGOTADO!", True, RED)
        restart_text = self.font.render("Pressione R para reiniciar ou ESC para sair", True, WHITE)
        
        surface.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
        surface.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 20))
    
    def draw_level_completed(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        surface.blit(overlay, (0, 0))
        
        complete_text = self.font.render("NÍVEL CONCLUÍDO!", True, GREEN)
        score_text = self.font.render(f"Pontuação final: {self.score}/{self.max_score}", True, WHITE)
        continue_text = self.font.render("Pressione C para continuar ou ESC para sair", True, WHITE)
        
        surface.blit(complete_text, (SCREEN_WIDTH//2 - complete_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
        surface.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
        surface.blit(continue_text, (SCREEN_WIDTH//2 - continue_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

def start_game(nickname, skin_index, level):
    game = Game(nickname, skin_index, level)
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif game.game_over and event.key == pygame.K_r:
                    # Reiniciar jogo
                    return start_game(nickname, skin_index, level)
                elif game.level_completed and event.key == pygame.K_c:
                    # Atualizar progresso no servidor
                    if game.level_completed and game.score >= 140:  # 70% de 200 (posso mudar depois)
                        new_level = level + 1
                        try:
                            requests.post('http://localhost:5000/api/update-level-progress', 
                                        json={'level_unlocked': new_level, 'score': game.score})
                        except:
                            print("Erro ao atualizar progresso no servidor")
                    return
        
        # Obter teclas pressionadas
        keys = pygame.key.get_pressed()
        
        # Atualizar jogo
        game.update(keys)
        
        # Desenhar
        game.draw(screen)
        
        # Atualizar display
        pygame.display.flip()
        
        # Controlar FPS
        clock.tick(60)
    
    pygame.quit()

def start_server():
    import subprocess
    subprocess.Popen([sys.executable, "server.py"])

if __name__ == "__main__":
    print("Iniciando servidor web...")
    start_server()
    print("Servidor iniciado em http://localhost:5000")
    print("Acesse o jogo através do navegador!")
    
    # Manter o programa rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")