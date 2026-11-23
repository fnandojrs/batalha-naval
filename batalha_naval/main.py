"""Batalha Naval A3 V6 — menu, nomes dos jogadores, jogada extra ao acertar e revanche."""
import math
import random
import sys
from pathlib import Path

import pygame
from assets import imagem, animacao, quadro_animacao, imagem_preencher, animacao_preencher
from game import Tabuleiro, FROTA, TAMANHO

pygame.init()
BASE_W, BASE_H = 800, 600
# Tela lógica de 800x600; a janela se ajusta ao monitor em que o jogo inicia.
# Mantém proporção 4:3, permitindo também redimensionamento manual.
monitor = pygame.display.Info()
area_w = max(360, monitor.current_w - 100)
area_h = max(270, monitor.current_h - 120)
escala_inicial = min(1.20, area_w / BASE_W, area_h / BASE_H)
janela_inicial = (max(320, int(BASE_W * escala_inicial)),
                  max(240, int(BASE_H * escala_inicial)))
JANELA = pygame.display.set_mode(janela_inicial, pygame.RESIZABLE)
TELA = pygame.Surface((BASE_W, BASE_H)).convert()
pygame.display.set_caption('Batalha Naval A3 - V6')
RELOGIO = pygame.time.Clock()
FONT = pygame.font.SysFont('arial', 16, bold=True)
SMALL = pygame.font.SysFont('arial', 13)
TINY = pygame.font.SysFont('arial', 11)
BIG = pygame.font.SysFont('arial', 28, bold=True)
HUGE = pygame.font.SysFont('arial', 44, bold=True)
WHITE = (241, 250, 255)
INK = (15, 36, 55)
BLUE = (22, 105, 167)
CYAN = (114, 217, 245)
YELLOW = (255, 215, 109)
RED = (247, 88, 77)
GREEN = (104, 229, 165)
CELL, GX, GY = 28, 119, 98
GRID = pygame.Rect(GX, GY, CELL * TAMANHO, CELL * TAMANHO)
SCREEN = pygame.Rect(78, 44, 596, 360)
CX = SCREEN.centerx  # centro horizontal da tela do monitor
PORTRAIT = pygame.Rect(4, 435, 163, 163)
ASSET_ROOT = Path(__file__).resolve().parent / 'assets'
MAX_NOME = 14

# Botões (coordenadas lógicas 800x600)
BTN_JOGAR = pygame.Rect(CX - 110, 220, 220, 42)
BTN_SAIR = pygame.Rect(CX - 110, 276, 220, 42)
CAMPOS_NOME = [pygame.Rect(CX - 170, 150, 340, 36), pygame.Rect(CX - 170, 230, 340, 36)]
BTN_CONFIRMAR_NOMES = pygame.Rect(CX - 110, 300, 220, 38)
BTN_REVANCHE = pygame.Rect(CX - 205, 292, 195, 32)
BTN_MENU = pygame.Rect(CX + 10, 292, 195, 32)

background = imagem('interface/fundo_principal.jpg', (800, 600))
portraits = [imagem_preencher(f'personagens/personagem{i}.jpg', PORTRAIT.size) for i in range(1, 5)]
portraits_large = [imagem_preencher(f'personagens/personagem{i}.jpg', (126, 132)) for i in range(1, 5)]
ship_file = {
    'Porta-avioes': 'porta_avioes.png', 'Encouracado': 'encouracado.png',
    'Cruzador': 'cruzador.png', 'Submarino': 'submarino.png',
    'Patrulha': 'patrulha.png'
}
def _load_original(path):
    arquivo = ASSET_ROOT / path
    try:
        return pygame.image.load(str(arquivo)).convert_alpha() if arquivo.is_file() else None
    except (pygame.error, OSError):
        return None


ship_originals = {key: _load_original('navios/' + filename) for key, filename in ship_file.items()}
_ship_cache = {}


def ship_sprite(nome, tamanho, vertical):
    """Arte do navio inteiro esticada sobre suas casas (girada 90° se vertical)."""
    chave = (nome, tamanho, vertical)
    if chave not in _ship_cache:
        original = ship_originals.get(nome)
        sprite = None
        if original:
            sprite = pygame.transform.smoothscale(original, (tamanho * CELL - 4, CELL - 6))
            if vertical:
                sprite = pygame.transform.rotate(sprite, 90)
        _ship_cache[chave] = sprite
    return _ship_cache[chave]


def ship_rect(casas):
    linhas = [l for l, _ in casas]
    colunas = [c for _, c in casas]
    x, y = GX + min(colunas) * CELL, GY + min(linhas) * CELL
    w = (max(colunas) - min(colunas) + 1) * CELL
    h = (max(linhas) - min(linhas) + 1) * CELL
    return pygame.Rect(x, y, w, h), len(set(linhas)) > 1


def draw_ship(nome, casas, alpha=255):
    rect, vertical = ship_rect(casas)
    sprite = ship_sprite(nome, len(casas), vertical)
    if sprite is None:
        pygame.draw.rect(TELA, (78, 95, 108), rect.inflate(-5, -9), border_radius=7)
        return
    if alpha < 255:
        sprite = sprite.copy()
        sprite.set_alpha(alpha)
    TELA.blit(sprite, sprite.get_rect(center=rect.center))
effect_frames = {typ: animacao('efeitos/' + typ, (70, 70))
                 for typ in ('agua', 'acertou', 'afundou')}
reaction_frames = {n: animacao_preencher(f'personagens/personagem{n}_atingido', PORTRAIT.size)
                   for n in range(1, 5)}
defeat_frames = {n: animacao_preencher(f'personagens/personagem{n}_derrota', PORTRAIT.size)
                 for n in range(1, 5)}
EFFECT_MS = {'agua': 900, 'acertou': 1100, 'afundou': 1600}

boards = [Tabuleiro(), Tabuleiro()]
selected = [None, None]  # 1..4
names = ['', '']
name_field = 0
active = 0
phase = 'menu'
next_phase = None
ship_index = 0
vertical = False
winner = None
notice = 'Bem-vindo! Pressione ENTER ou clique em JOGAR.'
last_shot = None  # (x, y, timestamp, result, defender)


def player_name(i):
    return names[i].strip() or f'Jogador {i + 1}'


def draw_text(txt, x, y, color=INK, font=SMALL):
    TELA.blit(font.render(str(txt), True, color), (x, y))


def draw_center(txt, y, color=INK, font=SMALL, cx=CX):
    img = font.render(str(txt), True, color)
    TELA.blit(img, (cx - img.get_width() // 2, y))


def panel(rect, color=(16, 42, 64), alpha=239, radius=9):
    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(overlay, (*color, alpha), overlay.get_rect(), border_radius=radius)
    TELA.blit(overlay, rect.topleft)


def button(label, r, active_button=True):
    mouse = logical_mouse()
    hover = mouse is not None and r.collidepoint(mouse)
    color = (58, 150, 205) if hover else (38, 125, 179)
    pygame.draw.rect(TELA, color if active_button else (102, 119, 132), r, border_radius=6)
    pygame.draw.rect(TELA, (102, 211, 241), r, width=1, border_radius=6)
    f = SMALL if len(label) < 22 else TINY
    label_img = f.render(label, True, WHITE)
    TELA.blit(label_img, label_img.get_rect(center=r.center))


def grid_cell(pos):
    if pos is not None and GRID.collidepoint(pos):
        return ((pos[1] - GY) // CELL, (pos[0] - GX) // CELL)
    return None


def draw_avatar(now):
    # Quadrado preto da arte é o espaço do personagem, sem deslocar o fundo.
    pygame.draw.rect(TELA, (11, 22, 34), PORTRAIT)
    avatar_index = selected[active]
    avatar_player = active
    active_frames = []
    if last_shot and phase in ('resultado', 'fim'):
        result, defender = last_shot[3], last_shot[4]
        if result != 'agua':
            # Embarcação atingida: mostra a reação do jogador que levou o tiro
            # durante toda a tela de resultado. Na derrota, usa a reação se não houver quadros próprios.
            avatar_player = defender
            avatar_index = selected[defender]
            active_frames = reaction_frames.get(avatar_index, [])
            if phase == 'fim':
                active_frames = defeat_frames.get(avatar_index, []) or active_frames
    if avatar_index:
        frame = (quadro_animacao(active_frames, now - last_shot[2], 160, repetir=False)
                 if active_frames and last_shot else None)
        art = frame or portraits[avatar_index - 1]
        if art:
            TELA.blit(art, PORTRAIT.topleft)
        caption = player_name(avatar_player).upper()
    else:
        draw_center('AGUARDANDO', 505, WHITE, FONT, PORTRAIT.centerx)
        caption = 'SEM COMANDANTE'
    # Legenda transparente sobre o rodapé da foto, sem diminuir o retrato.
    panel(pygame.Rect(7, 575, 157, 20), (10, 23, 39), 215, 0)
    draw_center(caption, 578, WHITE, TINY, PORTRAIT.centerx)


def draw_background(now):
    if background:
        TELA.blit(background, (0, 0))
    else:
        TELA.fill((36, 45, 63))
        pygame.draw.rect(TELA, (236, 242, 245), SCREEN)
    draw_avatar(now)


def screen_heading(title, subtitle=''):
    panel(pygame.Rect(86, 49, 580, 29), (12, 48, 78), 244, 3)
    draw_text(title, 101, 55, WHITE, FONT)
    if subtitle:
        img = TINY.render(subtitle, True, CYAN)
        TELA.blit(img, (657 - img.get_width(), 58))


def draw_menu(now):
    screen_heading('MENU PRINCIPAL', 'A3 - 2 JOGADORES')
    bob = int(4 * math.sin(now / 400))
    draw_center('BATALHA NAVAL', 110 + bob, BLUE, HUGE)
    draw_center('Dois jogadores no mesmo computador', 170, INK, SMALL)
    button('JOGAR (ENTER)', BTN_JOGAR)
    button('SAIR (ESC)', BTN_SAIR)
    draw_center('Acertou um navio? Jogue de novo!', 345, BLUE, SMALL)


def draw_names(now):
    screen_heading('NOMES DOS JOGADORES', 'INFORME OS NOMES')
    for i, r in enumerate(CAMPOS_NOME):
        draw_text(f'Nome do Jogador {i + 1}:', r.x, r.y - 22, INK, FONT)
        focused = i == name_field
        pygame.draw.rect(TELA, WHITE, r, border_radius=6)
        pygame.draw.rect(TELA, BLUE if focused else (150, 170, 185), r,
                         width=3 if focused else 1, border_radius=6)
        txt = names[i]
        if not txt and not focused:
            img = SMALL.render(f'Jogador {i + 1}', True, (150, 165, 175))
        else:
            img = FONT.render(txt, True, INK)
        TELA.blit(img, (r.x + 10, r.centery - img.get_height() // 2))
        if focused and (now // 500) % 2 == 0:
            x = r.x + 12 + (img.get_width() if txt else 0)
            pygame.draw.line(TELA, INK, (x, r.y + 8), (x, r.bottom - 8), 2)
    button('CONFIRMAR (ENTER)', BTN_CONFIRMAR_NOMES)
    draw_center('TAB ou clique troca de campo. Vazio = nome padrao.', 350, BLUE, TINY)


def draw_selection():
    screen_heading('SELECAO DE COMANDANTE', player_name(active).upper())
    draw_center(f'{player_name(active)}: clique em um personagem', 88, INK, FONT)
    for i in range(4):
        r = pygame.Rect(94 + i * 143, 118, 128, 188)
        available = (i + 1) not in selected
        pygame.draw.rect(TELA, (218, 231, 238) if available else (174, 177, 181), r, border_radius=7)
        img = portraits_large[i]
        if img:
            if not available:
                img = img.copy()
                img.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
            TELA.blit(img, (r.x + 1, r.y + 1))
        pygame.draw.rect(TELA, (43, 121, 170), r, width=2, border_radius=7)
        draw_center(f'PERSONAGEM {i + 1}', r.y + 140, INK, TINY, r.centerx)
        if not available:
            draw_center('JA ESCOLHIDO', r.y + 162, RED, TINY, r.centerx)
        else:
            draw_center('CLIQUE PARA ESCOLHER', r.y + 162, BLUE, TINY, r.centerx)
    draw_center('Cada jogador escolhe um personagem diferente.', 330, BLUE, SMALL)


def draw_privacy():
    box = pygame.Rect(91, 86, 567, 304)
    panel(box, (8, 32, 55), 251, 12)
    draw_center('TROCA DE JOGADOR', 122, YELLOW, BIG, box.centerx)
    draw_center(f'Passe o computador para {player_name(active)}.', 192, WHITE, FONT, box.centerx)
    draw_center('O adversario nao deve olhar a tela.', 228, CYAN, SMALL, box.centerx)
    button('ENTER OU ESPACO PARA CONTINUAR', pygame.Rect(box.centerx - 152, 285, 304, 39))


def draw_grid(board, show_ships, now, target=False):
    for i in range(TAMANHO):
        draw_center(chr(65 + i), GY + i * CELL + 7, INK, TINY, GX - 12)
        draw_center(i + 1, GY - 15, INK, TINY, GX + i * CELL + CELL // 2)
    for row in range(TAMANHO):
        for col in range(TAMANHO):
            r = pygame.Rect(GX + col * CELL, GY + row * CELL, CELL, CELL)
            wav = int(7 * math.sin(now / 450 + row * .8 + col * .4))
            pygame.draw.rect(TELA, (34, 119 + wav, 188 + wav), r)
            pygame.draw.rect(TELA, (154, 215, 241), r, 1)
    # Navios inteiros: os próprios sempre; os do adversário só depois de afundados.
    for ship in board.navios:
        if show_ships or ship.afundado:
            draw_ship(ship.nome, ship.casas)
    sunk_overlay = pygame.Surface((CELL - 2, CELL - 2), pygame.SRCALPHA)
    sunk_overlay.fill((150, 20, 20, 120))
    for row in range(TAMANHO):
        for col in range(TAMANHO):
            cell = (row, col)
            r = pygame.Rect(GX + col * CELL, GY + row * CELL, CELL, CELL)
            ship = board.navio_em(cell)
            if cell in board.tiros:
                if ship and ship.afundado:
                    # Navio afundado: arte do barco tingida de vermelho com X.
                    TELA.blit(sunk_overlay, (r.x + 1, r.y + 1))
                    pygame.draw.line(TELA, RED, (r.x + 7, r.y + 7), (r.right - 8, r.bottom - 8), 3)
                    pygame.draw.line(TELA, RED, (r.right - 8, r.y + 7), (r.x + 7, r.bottom - 8), 3)
                elif ship:
                    pygame.draw.circle(TELA, RED, r.center, 10)
                    pygame.draw.circle(TELA, YELLOW, r.center, 4)
                else:
                    pygame.draw.circle(TELA, WHITE, r.center, 6, 2)
    if target:
        mouse = logical_mouse()
        cell = grid_cell(mouse) if mouse is not None else None
        if cell:
            row, col = cell
            pygame.draw.rect(TELA, YELLOW, (GX + col * CELL, GY + row * CELL, CELL, CELL), 3)


def draw_effect(x, y, elapsed, result):
    """Efeito desenhado por código, usado quando não há quadros PNG em assets/efeitos."""
    t = elapsed / EFFECT_MS[result]
    if t >= 1:
        return
    fx = pygame.Surface((180, 180), pygame.SRCALPHA)
    c = 90
    if result == 'agua':
        for k in range(3):
            tk = t * 1.4 - k * 0.2
            if 0 < tk < 1:
                pygame.draw.circle(fx, (220, 245, 255, int(255 * (1 - tk))), (c, c),
                                   int(5 + tk * 32), 3)
        for i in range(8):
            ang = i * math.pi / 4
            d = t * 26
            h = math.sin(t * math.pi) * 18
            pygame.draw.circle(fx, (200, 235, 255, int(230 * (1 - t))),
                               (int(c + math.cos(ang) * d), int(c + math.sin(ang) * d * .5 - h)), 3)
    else:
        big = 1.6 if result == 'afundou' else 1.0
        flash = int((10 + t * 30) * big)
        pygame.draw.circle(fx, (255, 170, 60, int(220 * (1 - t))), (c, c), flash)
        pygame.draw.circle(fx, (255, 250, 210, int(255 * (1 - t))), (c, c), max(2, int(flash * .45)))
        for i in range(14):
            ang = i * 2 * math.pi / 14 + (i % 3) * .2
            d = t * 52 * big * (0.7 + (i % 4) * .12)
            pygame.draw.circle(fx, (255, 90 + (i % 3) * 50, 30, int(255 * (1 - t))),
                               (int(c + math.cos(ang) * d), int(c + math.sin(ang) * d)),
                               max(1, int(4 * big * (1 - t))))
        if result == 'afundou':
            pygame.draw.circle(fx, (70, 70, 70, int(160 * (1 - t))), (c, c), int(20 + t * 60), 6)
    TELA.blit(fx, (x - c, y - c))


def draw_result_banner(result, elapsed):
    if elapsed > 1400:
        return
    text = {'agua': 'AGUA!', 'acertou': 'ACERTOU!', 'afundou': 'AFUNDOU!'}[result]
    color = CYAN if result == 'agua' else (YELLOW if result == 'acertou' else RED)
    alpha = 255 if elapsed < 900 else int(255 * (1 - (elapsed - 900) / 500))
    for off, col in (((2, 2), INK), ((0, 0), color)):
        img = HUGE.render(text, True, col)
        img.set_alpha(max(0, alpha))
        TELA.blit(img, (GRID.centerx - img.get_width() // 2 + off[0],
                        GRID.centery - img.get_height() // 2 + off[1]))


def viewport():
    """Calcula letterbox 4:3, mesmo se a janela for esticada."""
    w, h = JANELA.get_size()
    scale = min(w / BASE_W, h / BASE_H)
    dw, dh = max(1, round(BASE_W * scale)), max(1, round(BASE_H * scale))
    return pygame.Rect((w - dw) // 2, (h - dh) // 2, dw, dh)


def to_logical(pos):
    dest = viewport()
    if not dest.collidepoint(pos):
        return None
    return (min(BASE_W - 1, int((pos[0] - dest.x) * BASE_W / dest.width)),
            min(BASE_H - 1, int((pos[1] - dest.y) * BASE_H / dest.height)))


def logical_mouse():
    return to_logical(pygame.mouse.get_pos())


def draw_sidebar(lines, footer, footer2=''):
    panel(pygame.Rect(417, 86, 235, 281), (13, 49, 78), 245, 10)
    y = 102
    for text, color in lines:
        draw_text(text, 430, y, color, SMALL)
        y += 29
    if footer:
        draw_text(footer, 430, 313, YELLOW, TINY)
    if footer2:
        draw_text(footer2, 430, 333, CYAN, TINY)


def draw_game(now):
    if phase == 'posicionar':
        screen_heading('POSICIONAR FROTA', player_name(active).upper())
        draw_grid(boards[active], True, now)
        if ship_index < len(FROTA):
            name, size = FROTA[ship_index]
            mouse = logical_mouse()
            cell = grid_cell(mouse) if mouse is not None else None
            if cell:
                valid = boards[active].pode_posicionar(*cell, size, vertical)
                if valid:
                    draw_ship(name, boards[active].casas_para(*cell, size, vertical), 150)
                for r, c in boards[active].casas_para(*cell, size, vertical):
                    if 0 <= r < 10 and 0 <= c < 10:
                        pygame.draw.rect(TELA, GREEN if valid else RED,
                            (GX+c*CELL+3, GY+r*CELL+3, CELL-6, CELL-6), 3)
            lines = [('SEU PROXIMO NAVIO', YELLOW), (name, WHITE),
                     (f'Tamanho: {size} casas', CYAN),
                     (f'Orientacao: {"VERTICAL" if vertical else "HORIZONTAL"}', WHITE),
                     (f'Posicionados: {ship_index}/{len(FROTA)}', GREEN),
                     ('Clique na grade para colocar', WHITE),
                     ('Deixe 1 casa livre entre navios', CYAN)]
        else:
            lines = [('FROTA COMPLETA!', GREEN), ('Pressione ENTER', WHITE),
                     ('para confirmar as posicoes.', CYAN)]
        draw_sidebar(lines, 'R: girar    A: automatico', 'BACKSPACE: desfazer   ENTER: ok')
    elif phase in ('jogar', 'resultado', 'fim'):
        enemy = boards[1 - active]
        afundados = sum(n.afundado for n in enemy.navios)
        screen_heading('BATALHA NAVAL', f'VEZ DE {player_name(active).upper()}')
        draw_grid(enemy, False, now, phase == 'jogar')
        lines = [(f'MAR DE {player_name(1 - active).upper()}', YELLOW),
                 (f'Vez de: {player_name(active)}', WHITE),
                 (f'Seus disparos: {len(enemy.tiros)}', CYAN),
                 (f'Navios afundados: {afundados}/{len(FROTA)}', GREEN)]
        if phase == 'jogar':
            lines.extend([('Clique no mar do', WHITE), ('adversario para disparar!', WHITE)])
        elif phase == 'resultado':
            again = last_shot[3] != 'agua'
            lines.extend([(notice, YELLOW),
                          ('Voce joga de novo!' if again else 'Fim da sua vez.', WHITE),
                          ('ENTER: atirar de novo' if again else 'ENTER: passar a vez', GREEN)])
        draw_sidebar(lines, 'Vermelho: acerto    X: afundado', 'Circulo branco: agua    ESC: sair')
        if last_shot and phase in ('resultado', 'fim') and last_shot[4] == 1 - active:
            x, y, start, result, _ = last_shot
            elapsed = now - start
            frames = effect_frames[result]
            if frames:
                if elapsed < len(frames) * 95:
                    TELA.blit(quadro_animacao(frames, elapsed, 95, repetir=False), (x - 35, y - 35))
            else:
                draw_effect(x, y, elapsed, result)
            if phase == 'resultado':
                draw_result_banner(result, elapsed)
        if phase == 'fim':
            box = pygame.Rect(129, 171, 491, 170)
            panel(box, (7, 35, 57), 249, 11)
            draw_center(f'{player_name(winner).upper()} VENCEU!', 192, YELLOW, BIG, box.centerx)
            draw_center('Todos os navios adversarios foram afundados.', 238, WHITE, SMALL, box.centerx)
            draw_center(f'Disparos: {len(boards[1 - winner].tiros)}', 260, CYAN, SMALL, box.centerx)
            button('R: REVANCHE', BTN_REVANCHE)
            button('M: MENU PRINCIPAL', BTN_MENU)


def random_place():
    global ship_index, notice
    board = boards[active]
    for name, size in FROTA[len(board.navios):]:
        options = [(r, c, v) for r in range(10) for c in range(10)
                   for v in (False, True) if board.pode_posicionar(r, c, size, v)]
        if not options:
            ship_index = len(board.navios)
            notice = 'Sem espaco para a frota. Use BACKSPACE para desfazer.'
            return
        r, c, v = random.choice(options)
        board.posicionar(name, size, r, c, v)
    ship_index = len(FROTA)
    notice = 'Frota posicionada. Pressione ENTER.'


def undo_ship():
    global ship_index, notice
    board = boards[active]
    if board.navios:
        removed = board.navios.pop()
        notice = f'{removed.nome} removido.'
    ship_index = len(board.navios)


def confirm_positions():
    global phase, next_phase, active, ship_index, notice
    if len(boards[active].navios) < len(FROTA):
        notice = 'Posicione todos os navios antes de confirmar.'
        return
    if active == 0:
        active, ship_index, next_phase = 1, 0, 'posicionar'
    else:
        active, next_phase = 0, 'jogar'
    phase = 'transicao'
    notice = 'Passe a vez ao proximo jogador.'


def new_match():
    """Revanche: mantém nomes e personagens, zera os tabuleiros."""
    global boards, active, phase, next_phase, ship_index, vertical, winner, notice, last_shot
    boards = [Tabuleiro(), Tabuleiro()]
    active, phase, next_phase, ship_index = 0, 'transicao', 'posicionar', 0
    vertical, winner, last_shot = False, None, None
    notice = 'Revanche! Posicionem as frotas novamente.'


def back_to_menu():
    global selected, names, name_field, phase, notice
    new_match()
    selected, names, name_field = [None, None], ['', ''], 0
    phase = 'menu'
    notice = 'Bem-vindo! Pressione ENTER ou clique em JOGAR.'


def start_names():
    global phase, name_field, notice
    phase, name_field = 'nomes', 0
    notice = 'Digite os nomes e pressione ENTER.'


def confirm_names():
    global phase, active, notice
    for i in range(2):
        names[i] = names[i].strip()[:MAX_NOME]
    active, phase = 0, 'selecionar'
    notice = f'{player_name(0)}: escolha seu comandante.'


def after_result():
    global active, phase, next_phase, notice
    if last_shot[3] == 'agua':
        active, phase, next_phase = 1 - active, 'transicao', 'jogar'
    else:
        phase = 'jogar'
        notice = f'{player_name(active)}, escolha o proximo alvo.'


def click(pos):
    global active, phase, next_phase, ship_index, notice, last_shot, winner, name_field
    if phase == 'menu':
        if BTN_JOGAR.collidepoint(pos):
            start_names()
        elif BTN_SAIR.collidepoint(pos):
            pygame.quit()
            sys.exit(0)
        return
    if phase == 'nomes':
        for i, r in enumerate(CAMPOS_NOME):
            if r.collidepoint(pos):
                name_field = i
        if BTN_CONFIRMAR_NOMES.collidepoint(pos):
            confirm_names()
        return
    if phase == 'fim':
        if BTN_REVANCHE.collidepoint(pos):
            new_match()
        elif BTN_MENU.collidepoint(pos):
            back_to_menu()
        return
    if phase == 'selecionar':
        for i in range(4):
            if pygame.Rect(94 + 143 * i, 118, 128, 188).collidepoint(pos):
                if i + 1 in selected:
                    notice = 'Personagem ja escolhido.'
                    return
                selected[active] = i + 1
                if active == 0:
                    active, phase, next_phase = 1, 'transicao', 'selecionar'
                    notice = f'{player_name(1)}: escolha seu comandante.'
                else:
                    active, phase, next_phase = 0, 'transicao', 'posicionar'
                    notice = f'{player_name(0)}: posicione sua frota.'
                return
    if phase == 'posicionar' and ship_index < len(FROTA):
        cell = grid_cell(pos)
        if cell:
            name, size = FROTA[ship_index]
            if boards[active].posicionar(name, size, *cell, vertical):
                ship_index += 1
                notice = 'Navio posicionado.'
            else:
                notice = 'Posicao invalida: fora da grade ou encostado em outro navio.'
    elif phase == 'jogar':
        cell = grid_cell(pos)
        if cell:
            enemy = boards[1 - active]
            result = enemy.atirar(*cell)
            if result is None:
                notice = 'Casa ja atacada. Escolha outra.'
                return
            now = pygame.time.get_ticks()
            last_shot = (GX + cell[1]*CELL + CELL//2,
                         GY + cell[0]*CELL + CELL//2, now, result, 1-active)
            if enemy.perdeu:
                winner, phase = active, 'fim'
                notice = f'{player_name(active)} venceu! R: revanche | M: menu'
            else:
                if result == 'afundou':
                    notice = f'{enemy.navio_em(cell).nome.upper()} AFUNDADO!'
                else:
                    notice = {'agua': 'TIRO NA AGUA!', 'acertou': 'ACERTOU UM NAVIO!'}[result]
                phase = 'resultado'


def on_names_key(event):
    global name_field
    if event.key == pygame.K_BACKSPACE:
        names[name_field] = names[name_field][:-1]
    elif event.key == pygame.K_TAB:
        name_field = 1 - name_field
    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        if name_field == 0:
            name_field = 1
        else:
            confirm_names()


def on_event(event):
    global phase, next_phase, active, vertical, notice
    if event.type == pygame.VIDEORESIZE:
        global JANELA
        JANELA = pygame.display.set_mode((max(320, event.w), max(240, event.h)), pygame.RESIZABLE)
        return
    if event.type == pygame.TEXTINPUT and phase == 'nomes':
        txt = ''.join(ch for ch in event.text if ch.isprintable())
        names[name_field] = (names[name_field] + txt)[:MAX_NOME]
        return
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)
        enter = event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
        if phase == 'nomes':
            on_names_key(event)
        elif phase == 'menu' and enter:
            start_names()
        elif phase == 'transicao' and (enter or event.key == pygame.K_SPACE):
            phase = next_phase
            notice = 'Pronto para continuar.'
        elif phase == 'posicionar':
            if event.key == pygame.K_r:
                vertical = not vertical
            elif event.key == pygame.K_a:
                random_place()
            elif event.key == pygame.K_BACKSPACE:
                undo_ship()
            elif enter:
                confirm_positions()
        elif phase == 'resultado' and (enter or event.key == pygame.K_SPACE):
            after_result()
        elif phase == 'fim':
            if event.key == pygame.K_r:
                new_match()
            elif event.key == pygame.K_m:
                back_to_menu()
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Respeita o tamanho atual da janela, que representa uma arte 800x600.
        pos = to_logical(event.pos)
        if pos is not None:
            click(pos)


def draw(now):
    draw_background(now)
    if phase == 'menu':
        draw_menu(now)
    elif phase == 'nomes':
        draw_names(now)
    elif phase == 'selecionar':
        draw_selection()
    elif phase == 'transicao':
        draw_privacy()
    else:
        draw_game(now)
    # Avisos discretos dentro da moldura inferior do monitor.
    panel(pygame.Rect(208, 408, 455, 27), (16, 31, 49), 252, 2)
    draw_text(notice[:70], 219, 414, YELLOW, TINY)
    JANELA.fill((8, 15, 27))
    dest = viewport()
    JANELA.blit(pygame.transform.smoothscale(TELA, dest.size), dest.topleft)
    pygame.display.flip()


def main():
    pygame.key.start_text_input()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            on_event(event)
        draw(pygame.time.get_ticks())
        RELOGIO.tick(60)


if __name__ == '__main__':
    main()
