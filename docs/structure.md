# Estrutura do projeto

O código do aplicativo está organizado no pacote `curvsat`:

- `core`: versão, caminhos e configurações compartilhadas;
- `services`: licença, sincronização, Supabase e atualização;
- `content`: traduções e dados técnicos;
- `ui`: telas e componentes gráficos;
- `reporting`: banco local e relatórios;
- `tools`: gerador de chaves, ícones e publicação de versões.

Os pontos de entrada públicos continuam na raiz (`main.py`,
`license_generator.py` e `release_update.py`) para preservar os comandos,
atalhos e configurações de empacotamento existentes. Os arquivos de PyInstaller
ficam em `packaging/`, e os procedimentos operacionais em `docs/`.

A pasta `server/` é somente de implantação local e continua ignorada pelo Git.
