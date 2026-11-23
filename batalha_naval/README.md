# Batalha Naval A3 — V6 (Python + Pygame)

Projeto acadêmico de Batalha Naval, **2 jogadores no mesmo computador**. Interface criada a partir da arte do monitor e dos quatro personagens fornecidos pela turma. O motor (`game.py`) continua independente da interface (`main.py`).

## Executar no Windows

```powershell
py -m pip install -r requirements.txt
py main.py
```

Ou abra `iniciar.bat` após instalar o Pygame. Para sair, ESC.

## Fluxo da partida

1. **Menu principal:** JOGAR (Enter) ou SAIR (Esc).
2. **Nomes:** cada jogador digita seu nome (Tab ou clique troca de campo; vazio = "Jogador 1/2").
3. Cada jogador escolhe um dos quatro personagens (não é permitido repetir); a tela de troca protege a escolha.
4. Cada jogador posiciona **cinco navios** no tabuleiro 10×10. Clique para posicionar; **R** gira; **A** distribui automaticamente; **Backspace** desfaz o último navio; **Enter** confirma. Deve existir pelo menos **uma célula vazia entre embarcações em todas as direções, inclusive na diagonal** (a prévia fica vermelha se o navio encostar em outro).
5. Na batalha, clique no mar do adversário para disparar. **Ao acertar uma embarcação, o jogador tem direito a uma nova jogada** (Enter continua). Ao errar (água), Enter passa a vez com tela de privacidade.
6. Efeitos: respingo na água, explosão no acerto e explosão maior no afundamento, com aviso grande na grade. Navio afundado fica marcado com **X**. Quando uma embarcação é atingida, o retrato mostra a **reação (rosto bravo)** do jogador que levou o tiro, usando `assets/personagens/personagemN_atingido/001.png`; na derrota, o perdedor também aparece com essa reação.
7. Vence quem afundar todos os navios adversários. No fim: **R** revanche (mesmos nomes e personagens) ou **M** volta ao menu principal.

## Estrutura dos arquivos de arte

```text
assets/
  interface/
    fundo_principal.jpg           # fundo do monitor, 800x600
  personagens/
    personagem1.jpg               # avatars enviados pela turma
    personagem2.jpg
    personagem3.jpg
    personagem4.jpg
    personagem1_atingido/         # quadros opcionais 001.png, 002.png...
    personagem1_derrota/          # quadros opcionais 001.png, 002.png...
    personagem2_atingido/
    personagem2_derrota/
    personagem3_atingido/
    personagem3_derrota/
    personagem4_atingido/
    personagem4_derrota/
  navios/
    porta_avioes.png
    encouracado.png
    cruzador.png
    submarino.png
    patrulha.png
  efeitos/
    agua/                         # 001.png, 002.png...
    acertou/
    afundou/
```

### Orientações para a turma de design

- **Retratos:** JPG ou PNG funcionam; por padrão foram incorporados os quatro JPG já enviados.
- **Navios:** PNG transparente em `assets/navios/`. Desde a V6 cada navio é desenhado **inteiro, atravessando suas 2–5 casas** (girado 90° na vertical). Artes da turma: Muito Grande = porta-aviões (5), Grande = encouraçado (4), Médio = cruzador e submarino (3), Pequeno = patrulha (2). No posicionamento aparece uma prévia transparente; no mar do adversário o navio só é revelado depois de afundado.
- **Animações:** coloquem quadros PNG em ordem crescente (`001.png`, `002.png`, ...). A duração padrão de cada quadro é 95 ms nos tiros e 160 ms nas reações; é ajustável no código.
- Se uma arte estiver ausente, o jogo continua usando efeitos de fallback.
- O retrato de reação do atingido aparece **no quadrado preto** durante o resultado do ataque. Sem quadros de reação específicos, aparece o retrato normal.
- A tela do computador no fundo é usada para um único tabuleiro por vez. O branco foi mantido sob o painel do jogo.

## Arquivos importantes

- `game.py`: regras, navios, colisões e estado dos tiros.
- `main.py`: renderização, seleção de personagem, turnos, animações e entrada.
- `assets.py`: carregamento dos arquivos PNG/JPG e sequências de quadros.

## GitHub

Na pasta do projeto:

```powershell
git add .
git commit -m "V4: fundo da turma e selecao de personagens"
git push
```

O código foi criado como **atualização**, mas este pacote não realiza o envio ao seu GitHub automaticamente. Não sobrescreva modificações feitas por outros colegas sem comparar.

## V5 — janela responsiva e avatar preenchendo quadrado

- A V4 abria obrigatoriamente em 1200×900. A V5 mede a resolução do monitor principal e inicia em tamanho compatível com a tela disponível, com margem para barra de tarefas e bordas.
- Janela redimensionável pelo mouse. A arte do jogo continua em 800×600 lógicos, com proporção 4:3 preservada e margens escuras quando necessário. O clique é convertido corretamente mesmo após redimensionamento.
- Imagens dos personagens e sequências animadas agora preenchem a área do retrato (163×163 na arte base), usando recorte central para não deformar as pessoas. Os lados da imagem podem ser cortados para encaixar no quadrado.
- Para trocar o personagem, mantenha os arquivos `assets/personagens/personagem1.jpg` até `personagem4.jpg`.
- Para obter mais espaço na tela, diminua a janela pelo canto. Não precisa editar o código.
