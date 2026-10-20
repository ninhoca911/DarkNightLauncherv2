# MeuLauncher – launcher de Minecraft personalizado

Visual roxo arredondado com estrelas cadentes, menu principal com a skin da tua conta
e botão **LAUNCH <versão>**. Secções: **Início**, **Mods**, **Cosméticos**, **Definições**.

## Login Microsoft (pelo browser, com MSAL)

Ao carregar em "Entrar com Microsoft" (ou no LAUNCH sem sessão) abre-se o teu browser
normal, fazes login lá e voltas ao launcher. A sessão fica guardada.

Precisas de registar uma app tua no Azure (grátis, uma vez):

1. https://entra.microsoft.com → **Identidade → Aplicações → Registos de aplicações → Novo registo**
   (se o portal Azure der erro de "tenant", cria primeiro uma conta Azure gratuita em
   https://azure.microsoft.com/free com a tua conta Microsoft).
2. **Tipos de conta suportados:** *Apenas contas Microsoft pessoais*.
3. Depois de criar: **Autenticação → Adicionar uma plataforma → Aplicações móveis e de ambiente de trabalho**
   e adiciona o URI `http://localhost`.
4. Ainda em Autenticação, **Permitir fluxos de cliente público = Sim**. Guarda.
5. Copia o **ID da aplicação (cliente)** para `config.py`, em `CLIENT_ID`.
6. A Mojang tem de aprovar a app para usar a API do Minecraft:
   https://aka.ms/mce-reviewappid (pode demorar alguns dias). Até lá o login falha
   com um erro 403/401 no passo "Minecraft".

## Usar com Python (opcional)

```
pip install -r requirements.txt
python launcher.py
python criar_atalho.py     # atalho no ambiente de trabalho
```

Para teres só um `.exe` sem instalar nada, vê o `COMO_GERAR_EXE.md`.

## Personalizar

- Nome do launcher: `APP_NAME` em `config.py`.
- Logo: `assets/logo.png` (barra lateral) e `assets/icon.png` (ícone da janela/.exe).
- Cores e estrelas: `STYLE` e a classe `Shell` em `launcher.py`.

## Mods

- Escolhe **Fabric** ou **Forge** no menu principal (instala-se sozinho).
- No separador **Mods**, arrasta os `.jar` ou usa "Abrir pasta dos mods".
- Ficam em `~/.meulauncher/minecraft/mods`. O mod tem de ser da mesma versão e loader.
- O Java é descarregado automaticamente com o jogo.

## Capas

- Capas oficiais da conta: podes equipar/esconder.
- Capa personalizada (PNG): guardada com pré-visualização. A Mojang não mostra capas
  personalizadas a outros jogadores; para a ver no jogo é preciso um mod do lado do cliente.
