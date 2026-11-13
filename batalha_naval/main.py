"""Batalha Naval A3 V4 — layout original da turma, seleção de personagem e 2 jogadores locais."""
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
pygame.display.set_caption('Batalha Naval A3 - V5 | Janela responsiva')
RELOGIO = pygame.time.Clock()
FONT = pygame.font.SysFont('arial', 16, bold=True)
SMALL = pygame.font.SysFont('arial', 13)
TINY = pygame.font.SysFont('arial', 11)
BIG = pygame.font.SysFont('arial', 28, bold=True)
WHITE = (241, 250, 255)
INK = (15, 36, 55)
BLUE = (22, 105, 167)
CYAN = (114, 217, 245)
YELLOW = (255, 215, 109)
RED = (247, 88, 77)
GREEN = (104, 229, 165)
CELL, GX, GY = 28, 119, 86
GRID = pygame.Rect(GX, GY, CELL * TAMANHO, CELL * TAMANHO)
SCREEN = pygame.Rect(78, 44, 596, 360)
PORTRAIT = pygame.Rect(4, 435, 163, 163)
ASSET_ROOT = Path(__file__).resolve().parent / 'assets'

background = imagem('interface/fundo_principal.jpg', (800, 600))
portraits = [imagem_preencher(f'personagens/personagem{i}.jpg', PORTRAIT.size) for i in range(1, 5)]
portraits_large = [imagem(f'personagens/personagem{i}.jpg', (126, 102)) for i in range(1, 5)]
ship_file = {
    'Porta-avioes': 'porta_avioes.png', 'Encouracado': 'encouracado.png',
    'Cruzador': 'cruzador.png', 'Submarino': 'submarino.png',
    'Patrulha': 'patrulha.png'
}
ship_images = {key: imagem('navios/' + filename, (CELL - 4, CELL - 9))
               for key, filename in ship_file.items()}
ship_fallback = imagem('navios/navio.png', (CELL - 4, CELL - 9))
effect_frames = {typ: animacao('efeitos/' + typ, (70, 70))
                 for typ in ('agua', 'acertou', 'afundou')}
reaction_frames = {n: animacao_preencher(f'personagens/personagem{n}_atingido', PORTRAIT.size)
                   for n in range(1, 5)}
defeat_frames = {n: animacao_preencher(f'personagens/personagem{n}_derrota', PORTRAIT.size)
                 for n in range(1, 5)}

boards = [Tabuleiro(), Tabuleiro()]
selected = [None, None]  # 1..4
active = 0
phase = 'selecionar'
next_phase = None
ship_index = 0
vertical = False
winner = None
notice = 'Jogador 1: escolha seu comandante.'
last_shot = None  # (x, y, timestamp, result, target_player)


def draw_text(txt, x, y, color=INK, font=SMALL):
    TELA.blit(font.render(str(txt), True, color), (x, y))


def panel(rect, color=(16, 42, 64), alpha=239, radius=9):
    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(overlay, (*color, alpha), overlay.get_rect(), border_radius=radius)
    TELA.blit(overlay, rect.topleft)


def button(label, r, active_button=True):
    pygame.draw.rect(TELA, (38, 125, 179) if active_button else (102, 119, 132), r, border_radius=6)
    pygame.draw.rect(TELA, (102, 211, 241), r, width=1, border_radius=6)
    f = SMALL if len(label) < 18 else TINY
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
        _, _, shot_time, result, defender = last_shot
        elapsed = now - shot_time
        if result != 'agua':
            if phase == 'fim':
                avatar_player = defender
                avatar_index = selected[defender]
                active_frames = defeat_frames.get(avatar_index, [])
            elif elapsed < 2500:
                avatar_player = defender
                avatar_index = selected[defender]
                active_frames = reaction_frames.get(avatar_index, [])
    if avatar_index:
        frame = (quadro_animacao(active_frames, now - last_shot[2], 160, repetir=False)
                 if active_frames and last_shot else None)
        art = frame or portraits[avatar_index - 1]
        if art:
            TELA.blit(art, PORTRAIT.topleft)
    else:
        draw_text('AGUARDANDO', 26, 505, WHITE, FONT)
    # Legenda transparente sobre o rodapé da foto, sem diminuir o retrato.
    panel(pygame.Rect(7, 575, 157, 20), (10, 23, 39), 215, 0)
    draw_text(f'J{avatar_player + 1} - COMANDANTE {avatar_index or "?"}', 12, 578, WHITE, TINY)


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


def draw_selection():
    screen_heading('SELECAO DE COMANDANTE', f'JOGADOR {active + 1}')
    draw_text(f'Jogador {active + 1}: clique em um personagem', 112, 89, INK, FONT)
    for i in range(4):
        r = pygame.Rect(94 + i * 143, 124, 128, 182)
        available = (i + 1) not in selected
        pygame.draw.rect(TELA, (218, 231, 238) if available else (174, 177, 181), r, border_radius=7)
        pygame.draw.rect(TELA, (43, 121, 170), r, width=2, border_radius=7)
        img = portraits_large[i]
        if img:
            TELA.blit(img, (r.x + 1, r.y + 4))
        draw_text(f'PERSONAGEM {i + 1}', r.x + 11, r.y + 145, INK, TINY)
        if not available:
            draw_text('JA ESCOLHIDO', r.x + 15, r.y + 164, RED, TINY)
        else:
            draw_text('CLIQUE PARA ESCOLHER', r.x + 4, r.y + 164, BLUE, TINY)
    draw_text('Cada jogador escolhe um personagem diferente.', 182, 337, BLUE, SMALL)
    draw_text('ESC: sair', 576, 377, INK, TINY)


def draw_privacy():
    panel(pygame.Rect(91, 86, 567, 304), (8, 32, 55), 251, 12)
    draw_text('TROCA DE JOGADOR', 233, 122, YELLOW, BIG)
    draw_text(f'Passe o computador ao Jogador {active + 1}.', 218, 192, WHITE, FONT)
    draw_text('O adversario nao deve olhar durante a preparacao.', 185, 228, CYAN, SMALL)
    button('ENTER OU ESPACO PARA CONTINUAR', pygame.Rect(218, 285, 303, 39))


def draw_grid(board, show_ships, now, target=False):
    for row in range(TAMANHO):
        draw_text(chr(65 + row), GX - 22, GY + row * CELL + 7, INK, TINY)
        draw_text(row + 1, GX + row * CELL + 7, GY - 17, INK, TINY)
        for col in range(TAMANHO):
            cell = (row, col)
            r = pygame.Rect(GX + col * CELL, GY + row * CELL, CELL, CELL)
            wav = int(7 * math.sin(now / 450 + row * .8 + col * .4))
            pygame.draw.rect(TELA, (34, 119 + wav, 188 + wav), r)
            pygame.draw.rect(TELA, (154, 215, 241), r, 1)
            ship = board.navio_em(cell)
            if show_ships and ship:
                pygame.draw.rect(TELA, (78, 95, 108), r.inflate(-5, -11), border_radius=5)
                art = ship_images.get(ship.nome) or ship_fallback
                if art:
                    TELA.blit(art, (r.x + 2, r.y + 4))
            if cell in board.tiros:
                if ship:
                    pygame.draw.circle(TELA, RED, r.center, 10)
                    pygame.draw.line(TELA, WHITE, (r.centerx - 4, r.centery - 4),
                                     (r.centerx + 4, r.centery + 4), 2)
                else:
                    pygame.draw.circle(TELA, WHITE, r.center, 6, 2)
    if target:
        mouse = logical_mouse()
        cell = grid_cell(mouse) if mouse is not None else None
        if cell:
            row, col = cell
            pygame.draw.rect(TELA, YELLOW, (GX + col * CELL, GY + row * CELL, CELL, CELL), 3)


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
        screen_heading('POSICIONAR FROTA', f'JOGADOR {active + 1}')
        draw_grid(boards[active], True, now)
        if ship_index < len(FROTA):
            name, size = FROTA[ship_index]
            mouse = logical_mouse()
            cell = grid_cell(mouse) if mouse is not None else None
            if cell:
                valid = boards[active].pode_posicionar(*cell, size, vertical)
                for r, c in boards[active].casas_para(*cell, size, vertical):
                    if 0 <= r < 10 and 0 <= c < 10:
                        pygame.draw.rect(TELA, GREEN if valid else RED,
                            (GX+c*CELL+3, GY+r*CELL+3, CELL-6, CELL-6), 3)
            lines = [('SEU PROXIMO NAVIO', YELLOW), (name, WHITE),
                     (f'Tamanho: {size} casas', CYAN),
                     (f'Orientacao: {"VERTICAL" if vertical else "HORIZONTAL"}', WHITE),
                     (f'Posicionados: {ship_index}/{len(FROTA)}', GREEN),
                     ('Clique na grade para colocar', WHITE)]
        else:
            lines = [('FROTA COMPLETA!', GREEN), ('Pressione ENTER', WHITE),
                     ('para confirmar as posicoes.', CYAN)]
        draw_sidebar(lines, 'R: girar    A: automatico', 'ENTER: confirmar')
    elif phase in ('jogar', 'resultado', 'fim'):
        screen_heading('BATALHA NAVAL', f'VEZ DO JOGADOR {active + 1}')
        draw_grid(boards[1 - active], False, now, phase == 'jogar')
        lines = [('MAR DO ADVERSARIO', YELLOW),
                 (f'Jogador atual: {active + 1}', WHITE),
                 (f'Seus disparos: {len(boards[1-active].tiros)}', CYAN),
                 ('Vermelho: acerto', RED), ('Circulo branco: agua', WHITE)]
        if phase == 'jogar':
            lines.extend([('Escolha uma coordenada', GREEN), ('para disparar!', WHITE)])
        elif phase == 'resultado':
            lines.extend([(notice, YELLOW), ('ENTER: proximo jogador', GREEN)])
        draw_sidebar(lines, 'A-J / 1-10: coordenadas', 'ESC: sair')
        if last_shot:
            x, y, start, result, target = last_shot
            elapsed = now - start
            if elapsed < 1300 and phase != 'transicao':
                frame = quadro_animacao(effect_frames[result], elapsed, 95, repetir=False)
                if frame:
                    TELA.blit(frame, (x - 35, y - 35))
                elif result != 'agua':
                    pygame.draw.circle(TELA, (253, 213, 96), (x, y), 12 + min(elapsed // 65, 13), 3)
        if phase == 'fim':
            panel(pygame.Rect(129, 171, 491, 155), (7, 35, 57), 249, 11)
            draw_text(f'JOGADOR {winner + 1} VENCEU!', 199, 198, YELLOW, BIG)
            draw_text('Todos os navios adversarios foram afundados.', 196, 256, WHITE, SMALL)
            button('N: NOVA PARTIDA', pygame.Rect(279, 287, 194, 28))


def random_place():
    global ship_index, notice
    board = boards[active]
    for name, size in FROTA[len(board.navios):]:
        options = [(r, c, v) for r in range(10) for c in range(10)
                   for v in (False, True) if board.pode_posicionar(r, c, size, v)]
        if not options:
            notice = 'Sem espaco para a frota completa.'
            return
        r, c, v = random.choice(options)
        board.posicionar(name, size, r, c, v)
    ship_index = len(FROTA)
    notice = 'Frota posicionada. Pressione ENTER.'


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


def restart():
    global boards, selected, active, phase, next_phase, ship_index, vertical, winner, notice, last_shot
    boards = [Tabuleiro(), Tabuleiro()]
    selected = [None, None]
    active, phase, next_phase, ship_index = 0, 'selecionar', None, 0
    vertical, winner, last_shot = False, None, None
    notice = 'Jogador 1: escolha seu comandante.'


def click(pos):
    global active, phase, next_phase, ship_index, notice, last_shot, winner
    if phase == 'selecionar':
        for i in range(4):
            if pygame.Rect(94 + 143 * i, 124, 128, 182).collidepoint(pos):
                if i + 1 in selected:
                    notice = 'Personagem ja escolhido.'
                    return
                selected[active] = i + 1
                if active == 0:
                    active, phase, next_phase = 1, 'transicao', 'selecionar'
                else:
                    active, phase, next_phase = 0, 'transicao', 'posicionar'
                return
    if phase == 'posicionar' and ship_index < len(FROTA):
        cell = grid_cell(pos)
        if cell:
            name, size = FROTA[ship_index]
            if boards[active].posicionar(name, size, *cell, vertical):
                ship_index += 1
                notice = 'Navio posicionado.'
            else:
                notice = 'Posicao invalida: sobreposicao ou fora da grade.'
    elif phase == 'jogar':
        cell = grid_cell(pos)
        if cell:
            result = boards[1-active].atirar(*cell)
            if result is None:
                notice = 'Casa ja atacada. Escolha outra.'
                return
            now = pygame.time.get_ticks()
            last_shot = (GX + cell[1]*CELL + CELL//2,
                         GY + cell[0]*CELL + CELL//2, now, result, 1-active)
            if boards[1-active].perdeu:
                winner, phase = active, 'fim'
                notice = f'Jogador {active+1} venceu!'
            else:
                notice = {'agua':'TIRO NA AGUA!', 'acertou':'ACERTOU!',
                          'afundou':'NAVIO AFUNDADO!'}[result]
                phase = 'resultado'


def on_event(event):
    global phase, next_phase, active, vertical, notice
    if event.type == pygame.VIDEORESIZE:
        global JANELA
        JANELA = pygame.display.set_mode((max(320, event.w), max(240, event.h)), pygame.RESIZABLE)
        return
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)
        if phase == 'transicao' and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            phase = next_phase
            notice = 'Pronto para continuar.'
        elif phase == 'posicionar':
            if event.key == pygame.K_r:
                vertical = not vertical
            elif event.key == pygame.K_a:
                random_place()
            elif event.key == pygame.K_RETURN:
                confirm_positions()
        elif phase == 'resultado' and event.key == pygame.K_RETURN:
            active, phase, next_phase = 1-active, 'transicao', 'jogar'
        elif phase == 'fim' and event.key == pygame.K_n:
            restart()
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        # Respeita o tamanho atual da janela, que representa uma arte 800x600.
        pos = to_logical(event.pos)
        if pos is not None:
            click(pos)


def draw(now):
    draw_background(now)
    if phase == 'selecionar':
        draw_selection()
    elif phase == 'transicao':
        draw_privacy()
    else:
        draw_game(now)
    # Avisos discretos dentro da moldura inferior do monitor.
    panel(pygame.Rect(208, 408, 455, 27), (16, 31, 49), 252, 2)
    draw_text(notice[:64], 219, 414, YELLOW, TINY)
    JANELA.fill((8, 15, 27))
    dest = viewport()
    JANELA.blit(pygame.transform.smoothscale(TELA, dest.size), dest.topleft)
    pygame.display.flip()


def main():
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
