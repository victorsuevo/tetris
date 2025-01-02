import random
import time
import pygame
import pygame.mixer

# Inicialização do Pygame
pygame.init()
pygame.mixer.init()

# Constantes
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 800
GRID_SIZE = 30
GRID_WIDTH, GRID_HEIGHT = SCREEN_WIDTH // GRID_SIZE, SCREEN_HEIGHT // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FALL_INTERVAL = 15.9
KEY_REPEAT_INTERVAL = 100
KEY_REPEAT_DELAY = 300
FAST_MOVE_INTERVAL = 50  # Intervalo para movimento rápido contínuo

# Efeitos sonoros
try:
    MOVE_SOUND = pygame.mixer.Sound("move.wav")
except pygame.error as e:
    print("Erro ao carregar move.wav:", e)
try:
    LINE_CLEAR_SOUND = pygame.mixer.Sound("line_clear.wav")
except pygame.error as e:
    print("Erro ao carregar line_clear.wav:", e)
try:
    GAME_OVER_SOUND = pygame.mixer.Sound("game_over.wav")
except pygame.error as e:
    print("Erro ao carregar game_over.wav:", e)
try:
    BOTTOM_HIT_SOUND = pygame.mixer.Sound("bottom_hit.wav")
except pygame.error as e:
    print("Erro ao carregar bottom_hit.wav:", e)

# Configuração da tela
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")

# Define as peças do Tetris (formas)
TETROMINOS = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1, 1], [1, 0, 0]],
    [[1, 1, 1], [0, 0, 1]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]]
]

# Função para criar uma peça aleatória
def new_piece():
    shape = random.choice(TETROMINOS)
    color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
    piece = {'shape': shape, 'color': color, 'x': GRID_WIDTH // 2 - len(shape[0]) // 2, 'y': 0}
    return piece

# Função para desenhar o tabuleiro
def draw_board(board):
    for row in range(GRID_HEIGHT):
        for col in range(GRID_WIDTH):
            if board[row][col] != 0:
                pygame.draw.rect(SCREEN, board[row][col], (col * GRID_SIZE, row * GRID_SIZE, GRID_SIZE, GRID_SIZE))

# Função para limpar as linhas completas
def clear_lines(board):
    lines_to_clear = []
    for row in range(GRID_HEIGHT):
        if all(board[row]):
            lines_to_clear.append(row)

    if lines_to_clear:
        LINE_CLEAR_SOUND.play()
        lines_to_clear.reverse()  # Inverta a ordem para evitar problemas de índice
        for row in lines_to_clear:
            del board[row]
            board.insert(0, [0] * GRID_WIDTH)

    return len(lines_to_clear)

# Função para atualizar a pontuação na tela
def update_score(score):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Score: {score}", True, BLACK)
    SCREEN.blit(text, (10, 10))

# Tela de "Game Over"
def game_over_screen():
    font = pygame.font.Font(None, 72)
    text = font.render("Game Over", True, BLACK)
    text_rect = text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    SCREEN.blit(text, text_rect)
    pygame.display.flip()

    # Pare a música de fundo
    pygame.mixer.music.stop()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

# Função para apagar a posição anterior da peça
def erase_piece(piece):
    for row in range(len(piece['shape'])):
        for col in range(len(piece['shape'][0])):
            if piece['shape'][row][col]:
                pygame.draw.rect(
                    SCREEN,
                    WHITE,
                    (piece['x'] * GRID_SIZE + col * GRID_SIZE, piece['y'] * GRID_SIZE + row * GRID_SIZE,
                     GRID_SIZE, GRID_SIZE)
                )

# Verifica se a peça pode se mover para a posição especificada
def can_move(piece, board, dx, dy):
    for r in range(len(piece['shape'])):
        for c in range(len(piece['shape'][0])):
            if piece['shape'][r][c]:
                board_row = piece['y'] + r + dy
                board_col = piece['x'] + c + dx
                if (
                        board_row < 0
                        or board_row >= GRID_HEIGHT
                        or board_col < 0
                        or board_col >= GRID_WIDTH
                        or board[board_row][board_col] != 0
                ):
                    return False
    return True

# Função para mover a peça
def move_piece(piece, board, dx, dy):
    if can_move(piece, board, dx, dy):
        erase_piece(piece)
        piece['x'] += dx
        piece['y'] += dy
        MOVE_SOUND.play()
    elif dy == 1:
        place_piece(piece, board)
        BOTTOM_HIT_SOUND.play()
        return True  # A peça atingiu o fundo
    return False

# Função para colocar a peça no tabuleiro
def place_piece(piece, board):
    for r in range(len(piece['shape'])):
        for c in range(len(piece['shape'][0])):
            if piece['shape'][r][c]:
                board_row = piece['y'] + r
                board_col = piece['x'] + c
                board[board_row][board_col] = piece['color']

# Função principal do jogo
def main():
    clock = pygame.time.Clock()
    piece = new_piece()
    game_over = False
    score = 0
    # Variáveis para controle de nível de dificuldade
    current_level = 0
    level_speed = FALL_INTERVAL

    # Variáveis para controle de power-ups
    power_up_active = False
    power_up_timer = 0
    power_up_duration = 5000

    # Música de fundo
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.play(-1)  # Repetição infinita

    # Controle de movimento rápido contínuo
    move_left_continuous = False
    move_right_continuous = False
    move_down_continuous = False

    # Variável para controle de queda
    fall_counter = 0

    # Variável para controlar o último tempo de movimento
    last_move_time = 0  # Adicione esta linha

    # Crie uma matriz vazia para representar o tabuleiro
    board = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]  # Mova esta linha para fora do loop

    while not game_over:
        current_time = pygame.time.get_ticks()
        # Verifique se é hora de aumentar o nível de dificuldade
        if score >= (current_level + 1) * 1000:
            current_level += 1
            level_speed -= 1  # Aumenta a velocidade de queda das peças

        # Verifique o tempo restante do power-up
        if power_up_active:
            power_up_timer += clock.get_rawtime()
            if power_up_timer >= power_up_duration:
                power_up_active = False
                power_up_timer = 0
                # Restaure as configurações normais do jogo

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_over = True
                elif event.key == pygame.K_LEFT:
                    move_left = move_piece(piece, board, -1, 0)
                    if not move_left:
                        move_left_continuous = True
                        last_move_time = current_time  # Atualize o tempo aqui
                elif event.key == pygame.K_RIGHT:
                    move_right = move_piece(piece, board, 1, 0)
                    if not move_right:
                        move_right_continuous = True
                        last_move_time = current_time  # Atualize o tempo aqui
                elif event.key == pygame.K_DOWN:
                    move_down = move_piece(piece, board, 0, 1)
                    if not move_down:
                        move_down_continuous = True
                        last_move_time = current_time  # Atualize o tempo aqui
                elif event.key == pygame.K_UP:
                    rotated_shape = list(zip(*reversed(piece['shape'])))
                    if (
                            can_move(piece, board, 0, 0)
                            and piece['x'] + len(rotated_shape[0]) <= GRID_WIDTH
                            and piece['y'] + len(rotated_shape) <= GRID_HEIGHT
                    ):
                        erase_piece(piece)
                        piece['shape'] = rotated_shape
                        MOVE_SOUND.play()
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    move_left_continuous = False
                elif event.key == pygame.K_RIGHT:
                    move_right_continuous = False
                elif event.key == pygame.K_DOWN:
                    move_down_continuous = False

        # Movimentação com repetição de tecla
        if move_left_continuous and current_time - last_move_time > FAST_MOVE_INTERVAL:
            move_left_continuous = move_piece(piece, board, -1, 0)
            if move_left_continuous:
                last_move_time = current_time
        if move_right_continuous and current_time - last_move_time > FAST_MOVE_INTERVAL:
            move_right_continuous = move_piece(piece, board, 1, 0)
            if move_right_continuous:
                last_move_time = current_time
        if move_down_continuous and current_time - last_move_time > FAST_MOVE_INTERVAL:
            move_down_continuous = move_piece(piece, board, 0, 1)
            if move_down_continuous:
                last_move_time = current_time

        # Verifique e elimine linhas completas
        lines_to_clear = clear_lines(board)
        if lines_to_clear > 0:
            score += lines_to_clear * 10

        # Lógica para mover a peça para baixo automaticamente
        fall_counter += 1
        if fall_counter >= level_speed:
            move_down = move_piece(piece, board, 0, 1)
            if move_down:
                piece = new_piece()
                if not can_move(piece, board, 0, 0):
                    GAME_OVER_SOUND.play()
                    game_over = True
            fall_counter = 0

        # Verifique se uma tecla está sendo mantida pressionada
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            move_left_continuous = move_piece(piece, board, -1, 0)
            last_move_time = current_time
        if keys[pygame.K_RIGHT]:
            move_right_continuous = move_piece(piece, board, 1, 0)
            last_move_time = current_time
        if keys[pygame.K_DOWN]:
            move_down_continuous = move_piece(piece, board, 0, 1)
            last_move_time = current_time

        # Desenhe o fundo
        SCREEN.fill(WHITE)
        # Desenhe o tabuleiro
        draw_board(board)
        # Desenhe a peça atual
        for row in range(len(piece['shape'])):
            for col in range(len(piece['shape'][0])):
                if piece['shape'][row][col]:
                    pygame.draw.rect(
                        SCREEN,
                        piece['color'],
                        (piece['x'] * GRID_SIZE + col * GRID_SIZE, piece['y'] * GRID_SIZE + row * GRID_SIZE,
                         GRID_SIZE, GRID_SIZE)
                    )
        # Atualize a pontuação na tela
        update_score(score)

        pygame.display.update()
        clock.tick(10)

    # Quando o jogo acabar, mostre a tela de "Game Over"
    game_over_screen()

if __name__ == '__main__':
    main()
