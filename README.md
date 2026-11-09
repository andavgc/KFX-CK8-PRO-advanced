# KFX CK8 PRO Advanced Remote Script para Ableton Live

## Visão Geral

Este repositório é um **Fork** baseado no trabalho original dos criadores do [MIDIMixD / MIDI Mix remote script para Ableton Live](https://github.com/diff-arch/MIDIMixD).

Este script foi desenvolvido especificamente para o controlador MIDI **KFX CK8 PRO** (que compartilha o layout físico do **Akai MIDI Mix**), mas traz adaptações cruciais de comportamento de hardware.

### Por que este Fork foi criado (Adaptações para o KFX CK8 PRO)
No Akai MIDI Mix original, botões como `SOLO` são utilizados em combinações modificadoras (como `SOLO + BANK RIGHT`). No entanto, no controlador **KFX CK8 PRO**, o botão `SOLO` não envia mensagens MIDI CC ou de nota padrão da mesma forma para combinações de modificadores.

Para tornar este controlador totalmente funcional no Ableton Live, este script adapta a arquitetura de controle:
- **Função Shift:** Movida do `SOLO` para o **`REC ARM 1`** (pressionar e segurar o botão `REC ARM` da primeira faixa atua como a tecla `Shift`).
- **Alternância de Modos e Navegação:** Adaptados especificamente para cái layout e fluxo de trabalho do CK8 PRO.

---

## Recursos Detalhados e Fluxo de Trabalho

O script opera em dois modos principais, oferecendo controle tradicional de mixagem e edição avançada de parâmetros de dispositivos.

### 1. Modo 1: Modo Mixer (Mixagem Tradicional)
Projetado para tarefas padrão de mixagem em blocos de 8 faixas:
- **Knobs (Fileiras 1, 2 e 3):** Controlam os **Sends A, B e C** de cada canal.
- **Shift + Knobs (Fileiras 1, 2 e 3):** Segure `REC ARM 1` (`Shift`) enquanto gira os knobs para controlar **Sends D, E e Panorâmica (Pan)**.
- **Faders 1–8:** Controlam o **Volume** da faixa (a posição máxima/topo corresponde a 0 dB).
- **BANK L / R:** Move o banco de 8 faixas para a esquerda ou direita na sua sessão.

### 2. Modo 2: Modo de Dispositivos e Parâmetros (Controle Avançado)
Projetado para ajustar parâmetros de plugins e dispositivos diretamente pelo hardware:
- **Knobs (Fileiras 1, 2 e 3):** Controlam os **primeiros 8 parâmetros** do dispositivo selecionado nas faixas 1, 2 e 3.
- **Faders 1–8:** **Selecionam dispositivos** em cada faixa. Mover um fader de baixo para cima alterna e seleciona os dispositivos carregados naquela faixa.
- **BANK L / R:** Move em blocos de 3 faixas.

### 3. Atalhos para Troca de Modo
- **Mudar para o Modo 2:** Segure `Shift` (`REC ARM 1`) + pressione **`BANK RIGHT`**.
- **Voltar para o Modo 1:** Segure `Shift` (`REC ARM 1`) + pressione **`BANK LEFT`**.

### 4. Multiuso do REC ARM (Toque e Seleção)
Os botões `REC ARM` dos canais 1 a 8 cumprem duas funções (armar gravação e selecionar a faixa):
- **1 Toque curto:** Arma ou desarma a gravação da faixa.
- **2 Toques curtos (Toque duplo):** Seleciona a faixa no Ableton Live.
- **Seleção automática por Knobs (com Cooldown):** Ao girar qualquer knob, a faixa correspondente é selecionada automaticamente no Ableton. Um sistema inteligente de *debounce* (400ms) evita que a seleção fique pulando ao ajustar múltiplos knobs simultaneamente.

### 5. Pickup de Parâmetros (Sem Saltos Bruscos)
Tanto os knobs quanto os faders possuem o recurso de **Pickup** (`PICKUP_KNOBS = True`, `PICKUP_FADERS = True`). Ao trocar de modo ou página, um controle físico só afetará o parâmetro do software quando a posição física cruzar ou coincidir com o valor atual no Ableton, evitando saltos repentinos no áudio.

### 6. Botão Send All
Pressionar o botão **`SEND ALL`** (ou quando há rajadas de controle) força instantaneamente o envio das posições físicas de todos os knobs para seus respectivos alvos, ignorando temporariamente o *pickup* para sincronizar os parâmetros na hora.

### 7. Caixa Vermelha (Session Box) e LEDs
- **Caixa Vermelha:** Desenha e mantém sincronizada a caixa de destaque da sessão diretamente no Ableton Live.
- **Feedback por LEDs:** Acende em tempo real os LEDs físicos dos botões de Mute e Arm de acordo com o estado do projeto.

---

## Guia de Instalação (Para Iniciantes)

Se você não tem familiaridade com Git ou linha de comando, é muito simples instalar este script baixando um arquivo ZIP:

### Passo 1: Baixar o arquivo ZIP
1. Role até o topo desta página do repositório no GitHub.
2. Clique no botão verde **`<> Code`**.
3. Clique em **`Download ZIP`**.
4. Salve o arquivo no seu computador e descompacte-o. Você receberá uma pasta contendo os arquivos do script.

### Passo 2: Localizar a pasta "Remote Scripts" no Ableton Live
1. Abra o **Ableton Live**.
2. Vá em **Preferências** (ou **Configurações** nas versões mais recentes) -> **Arquivo / Pasta** (File / Folder).
3. Localize o caminho da sua **User Library** (Biblioteca do Usuário).
4. Abra a pasta `User Library` no explorador de arquivos do seu computador (Finder no macOS, Explorador de Arquivos no Windows).
5. Dentro da `User Library`, verifique se existe uma pasta chamada **`Remote Scripts`**. Caso não exista, crie uma nova pasta com exatamente esse nome.

### Passo 3: Instalar o Script
1. Mova ou copie a pasta descompactada para dentro da pasta `Remote Scripts` e renomeie-a obrigatoriamente para **`kfx_ck8_pro`**:
   `User Library/Remote Scripts/kfx_ck8_pro/`
   > ⚠️ **Nota Importante sobre o Python:** Certifique-se de que o nome da pasta **não contenha espaços ou hífens** (ex: use `kfx_ck8_pro` em vez de `KFX-CK8-PRO` ou `KFX CK8 PRO`). As regras de módulos do Python exigem identificadores válidos; caso contrário, o interpretador do Ableton Live falhará ao carregar o script.

### Passo 4: Ativar no Ableton Live
1. Reinicie o Ableton Live.
2. Abra **Preferências** -> **Link / Tempo / MIDI**.
3. No campo **Control Surface**, selecione **MIDI Mix** (or the script name).
4. Defina as portas **Input** e **Output** para o seu controlador KFX CK8 PRO.

---

## Contribuições e Discussão

Contribuições, reporte de bugs e discussões são muito bem-vindos! Para ajudar a melhorar este projeto:

1. **Abrir uma Issue:** Se encontrar algum bug, tiver dúvidas ou quiser sugerir uma melhoria, abra uma *Issue* detalhando sua versão do Ableton Live e os passos para reproduzir o problema.
2. **Enviar uma Pull Request (PR):**
   - Faça um Fork do repositório.
   - Crie uma branch de recurso (`git checkout -b feature/SuaMelhoria`).
   - Faça o commit das suas alterações (`git commit -m 'Adiciona tal recurso'`).
   - Envie para a sua branch (`git push origin feature/SuaMelhoria`).
   - Abra uma Pull Request para a branch `main`.
3. **Boas Práticas:**
   - Mantenha o código limpo, legível e estruturado.
   - Documente claramente novos mapeamentos de controle.
   - Discuta mudanças arquiteturais importantes abrindo uma *Issue* antes de começar a codificar.

---

## Créditos e Licença

- **Projeto Original:** Forked a partir de [MIDIMixD por diff-arch](https://github.com/diff-arch/MIDIMixD).
- **Licença:** Distribuído sob a Licença MIT. Veja o arquivo `LICENSE.txt` para mais informações.
