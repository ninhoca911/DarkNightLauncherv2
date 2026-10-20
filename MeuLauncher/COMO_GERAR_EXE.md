# Como obter o .exe (sem instalares Python)

O .exe é compilado gratuitamente na nuvem do GitHub.

1. No teu repositório, **apaga os ficheiros antigos** (ou carrega os novos por cima).
2. Descompacta o zip e carrega o **conteúdo** da pasta (não a pasta `MeuLauncher` em si)
   com **Add file → Upload files**. Os ficheiros `requirements.txt`, `build_exe.py`,
   `launcher.py`, etc. têm de ficar na raiz do repositório.
3. A pasta oculta `.github` costuma não ser carregada. Cria-a à mão:
   **Add file → Create new file**, nome `.github/workflows/build.yml`, e cola o conteúdo
   do `build.yml` que vem no zip. Faz **Commit changes**.
4. Separador **Actions → Compilar .exe → Run workflow**. Demora 5 a 10 minutos.
5. Quando ficar verde, abre a execução e em **Artifacts** descarrega `MeuLauncher-exe`.
6. Dentro do zip está o `MeuLauncher.exe`. Cria um atalho no ambiente de trabalho
   (botão direito → Enviar para → Ambiente de trabalho).

Notas:
- Põe o teu logo em `assets/logo.png` (e `assets/icon.png`) antes de carregar, para o .exe
  sair com o teu ícone.
- O Windows SmartScreen pode avisar "editor desconhecido" na primeira vez: **Mais informações →
  Executar mesmo assim**.
- Edita o `CLIENT_ID` em `config.py` antes de carregar (ver LEIAME.md).
