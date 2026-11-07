"""Batalha Naval A3 — jogo local para dois jogadores (Pygame)."""
import math
import random
import sys
import pygame
from game import Tabuleiro, FROTA, TAMANHO
from assets import imagem, animacao, quadro_animacao

pygame.init()
LARG, ALT = 1220, 780
TELA = pygame.display.set_mode((LARG, ALT))
pygame.display.set_caption('Batalha Naval - A3 | 2 jogadores')
RELOGIO = pygame.time.Clock()
FONTE = pygame.font.SysFont('arial', 22)
PEQUENA = pygame.font.SysFont('arial', 17)
GRANDE = pygame.font.SysFont('arial', 39, bold=True)
TITULO = pygame.font.SysFont('arial', 28, bold=True)
BRANCO = (243, 250, 255)
AZUL = (20, 119, 175)
MAR = (14, 80, 130)
FUNDO = (7, 26, 50)
AMARELO = (255, 210, 91)
VERMELHO = (245, 88, 79)
VERDE = (104, 225, 153)
CEL = 42
X_ESQ, X_DIR, Y_TAB = 96, 702, 195

jogadores = [Tabuleiro(), Tabuleiro()]
fase = 'posicionar'
ativo = 0
indice_navio = 0
vertical = False
aviso = 'Clique na grade esquerda para posicionar o primeiro navio.'
proxima_fase = None
vencedor = None
efeitos = []
avatares = [imagem(f'avatares/jogador{i}.png', (66, 66)) for i in (1, 2)]
navio_arte = imagem('navios/navio.png', (38, 28))
explosao = imagem('efeitos/explosao.png', (40, 40))
# Cada tipo tem uma arte opcional; navio.png permanece como fallback.
ARTES_NAVIOS = {
    'Porta-avioes': 'porta_avioes.png',
    'Encouracado': 'encouracado.png',
    'Cruzador': 'cruzador.png',
    'Submarino': 'submarino.png',
    'Patrulha': 'patrulha.png',
}
navios_por_tipo = {
    nome: imagem('navios/' + arquivo, (38, 28))
    for nome, arquivo in ARTES_NAVIOS.items()
}
# Se não houver quadros, o jogo continua com gráficos desenhados por código.
anim_tiro = {tipo: animacao(f'efeitos/{tipo}', (112, 112))
             for tipo in ('agua', 'acertou', 'afundou')}
anim_reacao = {j: animacao(f'avatares/jogador{j}_atingido', (190, 190)) for j in (1, 2)}
anim_derrota = {j: animacao(f'avatares/jogador{j}_derrota', (260, 260)) for j in (1, 2)}
ultimo_impacto = None  # (x, y, instante, tipo, jogador_atingido)
instante_derrota = 0


def texto(s, x, y, cor=BRANCO, fonte=FONTE):
    TELA.blit(fonte.render(str(s), True, cor), (x, y))


def tab_cell(pos, x):
    px, py = pos
    if x <= px < x + CEL * TAMANHO and Y_TAB <= py < Y_TAB + CEL * TAMANHO:
        return ((py - Y_TAB)//CEL, (px - x)//CEL)
    return None


def desenhar_grade(x, tabuleiro, mostrar_navios, alvo=False, tempo=0):
    for l in range(TAMANHO):
        texto(chr(65+l), x-30, Y_TAB+l*CEL+10, AMARELO, PEQUENA)
        texto(l+1, x+l*CEL+13, Y_TAB-28, AMARELO, PEQUENA)
        for c in range(TAMANHO):
            casa = (l, c)
            r = pygame.Rect(x+c*CEL, Y_TAB+l*CEL, CEL, CEL)
            tom = 84 + int(10*math.sin(tempo/650 + l + c))
            pygame.draw.rect(TELA, (19, tom, 158), r)
            pygame.draw.rect(TELA, (45, 163, 224), r, 1)
            navio = tabuleiro.navio_em(casa)
            if mostrar_navios and navio:
                pygame.draw.rect(TELA, (96, 126, 145), r.inflate(-5, -10), border_radius=9)
                arte = navios_por_tipo.get(navio.nome) or navio_arte
                if arte:
                    TELA.blit(arte, (r.x+2, r.y+7))
            if casa in tabuleiro.tiros:
                if navio:
                    pygame.draw.circle(TELA, VERMELHO, r.center, 12)
                    pygame.draw.line(TELA, BRANCO, (r.centerx-5, r.centery-5), (r.centerx+5,r.centery+5), 2)
                    pygame.draw.line(TELA, BRANCO, (r.centerx+5,r.centery-5), (r.centerx-5,r.centery+5), 2)
                else:
                    pygame.draw.circle(TELA, (229, 250, 255), r.center, 6, 2)
    if alvo:
        casa = tab_cell(pygame.mouse.get_pos(), x)
        if casa:
            l,c = casa
            r = pygame.Rect(x+c*CEL, Y_TAB+l*CEL, CEL, CEL)
            pygame.draw.rect(TELA, AMARELO, r, 3)


def avancar_posicionamento():
    global fase, ativo, indice_navio, aviso, proxima_fase
    if len(jogadores[ativo].navios) != len(FROTA):
        aviso = 'Posicione todos os navios antes de confirmar.'
        return
    if ativo == 0:
        fase, proxima_fase = 'transicao', 'posicionar'
        ativo, indice_navio = 1, 0
    else:
        fase, proxima_fase = 'transicao', 'jogar'
        ativo = 0
    aviso = 'Passe o computador ao proximo jogador.'


def distribuir_automaticamente():
    global indice_navio, aviso
    tab = jogadores[ativo]
    # Preenche apenas navios ainda não posicionados; evita travamento por tentativas limitadas.
    for nome, tamanho in FROTA[len(tab.navios):]:
        opcoes = [(l,c,v) for l in range(TAMANHO) for c in range(TAMANHO)
                  for v in (False, True) if tab.pode_posicionar(l,c,tamanho,v)]
        if not opcoes:
            aviso = 'Sem espaco para posicionamento automatico.'
            return
        l,c,v = random.choice(opcoes)
        tab.posicionar(nome,tamanho,l,c,v)
    indice_navio = len(tab.navios)
    aviso = 'Frota pronta! Pressione ENTER para confirmar.'


def atualizar_evento(ev):
    global fase, ativo, indice_navio, vertical, aviso, vencedor, proxima_fase, ultimo_impacto, instante_derrota
    if ev.type == pygame.KEYDOWN:
        if ev.key == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()
        if fase == 'transicao' and ev.key in (pygame.K_SPACE, pygame.K_RETURN):
            fase = proxima_fase
            aviso = ('Posicione sua frota na grade esquerda.' if fase == 'posicionar'
                     else 'Clique na grade direita para disparar contra o adversario.')
        elif fase == 'posicionar':
            if ev.key == pygame.K_r:
                vertical = not vertical
            elif ev.key == pygame.K_a:
                distribuir_automaticamente()
            elif ev.key == pygame.K_RETURN:
                avancar_posicionamento()
        elif fase == 'fim' and ev.key == pygame.K_n:
            reiniciar()
    if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
        if fase == 'posicionar' and indice_navio < len(FROTA):
            casa = tab_cell(ev.pos, X_ESQ)
            if casa:
                nome, tamanho = FROTA[indice_navio]
                if jogadores[ativo].posicionar(nome, tamanho, *casa, vertical):
                    indice_navio += 1
                    aviso = ('Todos posicionados! Pressione ENTER.' if indice_navio == len(FROTA)
                             else 'Navio posicionado. Continue escolhendo as casas.')
                else:
                    aviso = 'Posicao invalida: navio sobreposto ou fora da grade.'
        elif fase == 'jogar':
            casa = tab_cell(ev.pos, X_DIR)
            if casa:
                resultado = jogadores[1-ativo].atirar(*casa)
                if resultado is None:
                    aviso = 'Esta casa ja recebeu um disparo. Escolha outra.'
                    return
                agora = pygame.time.get_ticks()
                centro_x = X_DIR + casa[1]*CEL + CEL//2
                centro_y = Y_TAB + casa[0]*CEL + CEL//2
                efeitos.append((centro_x, centro_y, agora, resultado))
                ultimo_impacto = (centro_x, centro_y, agora, resultado, 2-ativo)
                if jogadores[1-ativo].perdeu:
                    vencedor, fase = ativo, 'fim'
                    instante_derrota = agora
                    aviso = f'Jogador {ativo+1} venceu! Pressione N para reiniciar.'
                else:
                    aviso = {'agua':'Tiro na agua!', 'acertou':'Acertou um navio!',
                             'afundou':'Navio afundado!'}[resultado]
                    # Resultado fica visível até o jogador apertar ENTER.
                    fase, proxima_fase = 'resultado', 'jogar'
        elif fase == 'resultado':
            # Alternância é feita por ENTER, para garantir que ambos vejam o tiro.
            pass
    if ev.type == pygame.KEYDOWN and fase == 'resultado' and ev.key == pygame.K_RETURN:
        ativo = 1-ativo
        fase, proxima_fase = 'transicao', 'jogar'
        aviso = 'Passe o computador ao proximo jogador.'


def reiniciar():
    global jogadores, fase, ativo, indice_navio, vertical, aviso, vencedor, proxima_fase, ultimo_impacto, instante_derrota
    jogadores = [Tabuleiro(), Tabuleiro()]
    fase, ativo, indice_navio, vertical = 'posicionar', 0, 0, False
    vencedor, proxima_fase = None, None
    aviso = 'Clique na grade esquerda para posicionar o primeiro navio.'
    efeitos.clear()
    ultimo_impacto = None
    instante_derrota = 0


def desenhar():
    tempo = pygame.time.get_ticks()
    TELA.fill(FUNDO)
    pygame.draw.rect(TELA, (15, 49, 82), (0, 0, LARG, 115))
    texto('BATALHA NAVAL', 40, 28, BRANCO, GRANDE)
    texto('A3 - 2 jogadores no mesmo computador', 42, 79, (170, 217, 240), PEQUENA)
    texto(f'JOGADOR {ativo+1}', 987, 32, AMARELO, TITULO)
    if avatares[ativo]:
        TELA.blit(avatares[ativo], (904, 22))
    else:
        pygame.draw.circle(TELA, (52, 126, 183), (938, 55), 33)
        texto(str(ativo+1), 931, 42, BRANCO, TITULO)

    if fase == 'transicao':
        texto('TROCA DE JOGADOR', 420, 235, AMARELO, GRANDE)
        texto(f'Agora e a vez do Jogador {ativo+1}.', 425, 315)
        texto('Sem mostrar a tela ao adversario.', 425, 353)
        texto('Pressione ESPACO ou ENTER quando estiver pronto.', 320, 435, VERDE)
        return

    texto('SUA FROTA', X_ESQ, 136, AMARELO, TITULO)
    texto('MAR DO ADVERSARIO', X_DIR, 136, AMARELO, TITULO)
    desenhar_grade(X_ESQ, jogadores[ativo], True, tempo=tempo)
    desenhar_grade(X_DIR, jogadores[1-ativo], False, alvo=(fase == 'jogar'), tempo=tempo)

    if fase == 'posicionar':
        if indice_navio < len(FROTA):
            nome,tamanho = FROTA[indice_navio]
            casa = tab_cell(pygame.mouse.get_pos(), X_ESQ)
            if casa:
                valido = jogadores[ativo].pode_posicionar(*casa, tamanho, vertical)
                for l,c in jogadores[ativo].casas_para(*casa,tamanho,vertical):
                    if 0 <= l < TAMANHO and 0 <= c < TAMANHO:
                        cor = VERDE if valido else VERMELHO
                        pygame.draw.rect(TELA, cor,
                            (X_ESQ+c*CEL+3,Y_TAB+l*CEL+3,CEL-6,CEL-6),3)
            texto(f'Posicionar: {nome} ({tamanho} casas)', 97, 634, BRANCO)
        else:
            texto('Frota completa!', 97, 634, VERDE)
        texto('R: girar | A: posicionamento automatico | ENTER: confirmar', 97, 673, (180, 220, 249), PEQUENA)
    elif fase in ('jogar', 'resultado'):
        tiros = len(jogadores[1-ativo].tiros)
        texto(f'Seus disparos: {tiros}', X_DIR, 634)
        texto('Vermelho = acerto     Circulo branco = agua', X_DIR, 667, BRANCO, PEQUENA)
        if fase == 'resultado':
            texto('Pressione ENTER para passar o turno.', 97, 673, VERDE)
    elif fase == 'fim':
        perdedor = 2-vencedor
        quadros = anim_derrota[perdedor]
        if quadros:
            arte = quadro_animacao(quadros, tempo-instante_derrota, 140, repetir=False)
            TELA.blit(arte, (440, 10))
        pygame.draw.rect(TELA, (8, 37, 62), (330, 290, 550, 170), border_radius=20)
        texto(f'JOGADOR {vencedor+1} VENCEU!', 393, 327, AMARELO, TITULO)
        texto('Pressione N para uma nova partida.', 403, 395, VERDE)
    texto(aviso, 38, 725, AMARELO, PEQUENA)
    texto('ESC: sair', 1091, 750, (150, 188, 208), PEQUENA)
    # Animação curta no ponto do tiro, independentemente de imagem estática.
    for x,y,t0,tipo in efeitos[:]:
        idade = tempo-t0
        if idade > 1300:
            efeitos.remove((x,y,t0,tipo))
        else:
            frames = anim_tiro[tipo]
            quadro = quadro_animacao(frames, idade, 90, repetir=False)
            if quadro:
                TELA.blit(quadro, (x-56, y-56))
            elif tipo != 'agua':
                if explosao:
                    TELA.blit(explosao, (x-20, y-20))
                else:
                    pygame.draw.circle(TELA, (255, 193, 76), (x,y), 9+int(min(idade,700)/55), 3)
    # Reação do avatar do jogador atingido, enquanto o tiro é mostrado.
    if ultimo_impacto is not None and fase in ('resultado', 'fim'):
        _, _, inicio, tipo, atingido = ultimo_impacto
        decorrido = tempo-inicio
        if tipo != 'agua' and decorrido < 2200 and fase == 'resultado':
            quadros = anim_reacao[atingido]
            quadro = quadro_animacao(quadros, decorrido, 140, repetir=False)
            if quadro:
                pygame.draw.rect(TELA, (10, 44, 74), (440, 380, 204, 234), border_radius=12)
                TELA.blit(quadro, (447, 388))
                texto(f'Jogador {atingido} atingido!', 442, 587, AMARELO, PEQUENA)


def main():
    while True:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); return
            atualizar_evento(ev)
        desenhar()
        pygame.display.flip()
        RELOGIO.tick(60)

if __name__ == '__main__':
    main()
