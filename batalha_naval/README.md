# Batalha Naval A3 — Versão 3 (artes e animações)

Jogo clássico 10×10 para **2 jogadores no mesmo computador**, em Python + Pygame.

## Executar no Windows

No PowerShell, dentro da pasta extraída:

```powershell
py -m pip install -r requirements.txt
py main.py
```

## Controles

- Clique na grade esquerda para colocar um navio.
- `R`: mudar orientação; `A`: distribuição automática; `Enter`: confirmar/trocar turno.
- Clique na grade direita para atacar.
- `N`: nova partida ao fim; `Esc`: sair.

## Onde a turma coloca os arquivos

### Barcos (PNG com transparência)

- `assets/navios/porta_avioes.png`
- `assets/navios/encouracado.png`
- `assets/navios/cruzador.png`
- `assets/navios/submarino.png`
- `assets/navios/patrulha.png`

Tamanho sugerido: **128×96 px ou maior**. As imagens são ajustadas automaticamente para 38×28 px por casa. **Importante:** nesta versão a imagem do navio aparece em *cada célula ocupada*, e não uma imagem única atravessando várias células. Para barcos grandes desenhados por inteiro, será preciso mudar a renderização depois.

Fallback opcional: `assets/navios/navio.png` (usado para qualquer tipo que ainda não tenha sua arte específica).

### Avatares (PNG com transparência)

- `assets/avatares/jogador1.png`
- `assets/avatares/jogador2.png`

Tamanho sugerido: 256×256 px, com o rosto bem centralizado.

### Animações por quadros (PNG com transparência)

Coloque arquivos **001.png, 002.png, 003.png...** dentro da pasta específica:

- `assets/efeitos/agua/` — tiro na água.
- `assets/efeitos/acertou/` — tiro que acertou navio.
- `assets/efeitos/afundou/` — navio afundado.
- `assets/avatares/jogador1_atingido/` — reação quando J1 leva tiro.
- `assets/avatares/jogador2_atingido/` — reação quando J2 leva tiro.
- `assets/avatares/jogador1_derrota/` — reação de derrota do J1.
- `assets/avatares/jogador2_derrota/` — reação de derrota do J2.

Exemplo:

```text
assets/
  navios/
    porta_avioes.png
    encouracado.png
    cruzador.png
    submarino.png
    patrulha.png
  avatares/
    jogador1.png
    jogador2.png
    jogador1_atingido/
      001.png
      002.png
      003.png
    jogador2_atingido/
      001.png
      002.png
      003.png
    jogador1_derrota/
      001.png
      002.png
      003.png
    jogador2_derrota/
      001.png
      002.png
      003.png
  efeitos/
    agua/
      001.png
      002.png
    acertou/
      001.png
      002.png
    afundou/
      001.png
      002.png
```

Quadros do tiro são exibidos a 90 ms por quadro, sem repetir, por até 1,3 segundo. A reação do personagem atingido usa 140 ms por quadro por até 2,2 segundos; a derrota mostra o último quadro ao terminar. Para animações longas, ajustar esses valores em `main.py`.

As imagens são carregadas **ao iniciar o jogo**: feche e abra novamente após substituir as artes. Se não encontrar uma imagem, a partida continua com desenho simples, e a animação ausente não será exibida. Formatos GIF animado, MP4 e spritesheets ainda não são suportados diretamente: exporte como PNGs numerados.

## Arquitetura

- `game.py`: regras, posições, acertos e vitória.
- `main.py`: interface, eventos e animações.
- `assets.py`: leitura de imagens e frames.

## Limitações

- Tabuleiro 2D, não 3D em perspectiva como a imagem de referência.
- Barcos estáticos, conforme regras clássicas; efeitos animados.
- Uma cópia de cada arte por célula de navio, não a silhueta completa de cada barco.
- Jogadores precisam passar o computador no fim do turno; a tela de transição evita mostrar as posições antes da troca.
