"""Carregamento opcional de artes e sequências PNG (sem dependências extras)."""
from pathlib import Path
import pygame

RAIZ = Path(__file__).resolve().parent / 'assets'


def imagem(caminho, tamanho):
    arquivo = RAIZ / caminho
    if not arquivo.is_file():
        return None
    try:
        return pygame.transform.smoothscale(pygame.image.load(str(arquivo)).convert_alpha(), tamanho)
    except (pygame.error, OSError, ValueError):
        return None


def animacao(pasta, tamanho):
    """Lê 001.png, 002.png etc. em ordem alfabética. Devolve lista vazia se ausentes."""
    diretorio = RAIZ / pasta
    if not diretorio.is_dir():
        return []
    quadros = []
    for arquivo in sorted(diretorio.glob('*.png')):
        quadro = imagem(str(arquivo.relative_to(RAIZ)), tamanho)
        if quadro is not None:
            quadros.append(quadro)
    return quadros


def quadro_animacao(quadros, tempo_ms, intervalo_ms=120, repetir=True):
    if not quadros:
        return None
    indice = max(0, tempo_ms // intervalo_ms)
    if repetir:
        indice %= len(quadros)
    else:
        indice = min(indice, len(quadros) - 1)
    return quadros[indice]


def imagem_preencher(caminho, tamanho):
    """Escala no modo 'cover', preserva proporção e recorta o excedente ao centro."""
    arquivo = RAIZ / caminho
    if not arquivo.is_file():
        return None
    try:
        origem = pygame.image.load(str(arquivo)).convert_alpha()
        largura, altura = origem.get_size()
        destino_w, destino_h = tamanho
        escala = max(destino_w / largura, destino_h / altura)
        nova = pygame.transform.smoothscale(origem, (round(largura * escala), round(altura * escala)))
        quadro = pygame.Surface(tamanho, pygame.SRCALPHA)
        quadro.blit(nova, ((destino_w - nova.get_width()) // 2,
                           (destino_h - nova.get_height()) // 2))
        return quadro
    except (pygame.error, OSError, ValueError, ZeroDivisionError):
        return None


def animacao_preencher(pasta, tamanho):
    diretorio = RAIZ / pasta
    if not diretorio.is_dir():
        return []
    quadros = []
    for arquivo in sorted(diretorio.glob('*.png')):
        quadro = imagem_preencher(str(arquivo.relative_to(RAIZ)), tamanho)
        if quadro is not None:
            quadros.append(quadro)
    return quadros
