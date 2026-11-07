"""Regras da Batalha Naval, independentes do Pygame."""
from dataclasses import dataclass, field

TAMANHO = 10
FROTA = [("Porta-avioes", 5), ("Encouracado", 4), ("Cruzador", 3), ("Submarino", 3), ("Patrulha", 2)]

@dataclass
class Navio:
    nome: str
    casas: set[tuple[int, int]]
    acertos: set[tuple[int, int]] = field(default_factory=set)

    @property
    def afundado(self):
        return self.casas == self.acertos

class Tabuleiro:
    def __init__(self):
        self.navios: list[Navio] = []
        self.tiros: set[tuple[int, int]] = set()

    def casas_para(self, linha, coluna, tamanho, vertical):
        return {(linha + (i if vertical else 0), coluna + (0 if vertical else i))
                for i in range(tamanho)}

    def pode_posicionar(self, linha, coluna, tamanho, vertical):
        casas = self.casas_para(linha, coluna, tamanho, vertical)
        return all(0 <= l < TAMANHO and 0 <= c < TAMANHO for l,c in casas) and not any(
            casas & navio.casas for navio in self.navios)

    def posicionar(self, nome, tamanho, linha, coluna, vertical):
        if not self.pode_posicionar(linha, coluna, tamanho, vertical):
            return False
        self.navios.append(Navio(nome, self.casas_para(linha, coluna, tamanho, vertical)))
        return True

    def atirar(self, linha, coluna):
        casa = (linha, coluna)
        if not (0 <= linha < TAMANHO and 0 <= coluna < TAMANHO) or casa in self.tiros:
            return None
        self.tiros.add(casa)
        for navio in self.navios:
            if casa in navio.casas:
                navio.acertos.add(casa)
                return 'afundou' if navio.afundado else 'acertou'
        return 'agua'

    @property
    def perdeu(self):
        return len(self.navios) == len(FROTA) and all(n.afundado for n in self.navios)

    def navio_em(self, casa):
        return next((n for n in self.navios if casa in n.casas), None)
