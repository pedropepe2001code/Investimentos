# Investimentos

Sistema pessoal de apoio à decisão de investimento.

- **Toda segunda às 7h** o GitHub Actions (`.github/workflows/relatorio-semanal.yml`) roda o Claude com o prompt de `prompts/relatorio_semanal.md` e grava um relatório em `relatorios/`.
- **Quando for decidir**, abra a pasta no VS Code, rode `git pull` e peça ao Claude Code (que segue o `CLAUDE.md`), por exemplo:
  - "Leia o relatório novo e me diga o que mudou para a minha carteira."
  - "Tenho R$ 5.000 para aportar. Onde coloco?"
- Depois de decidir, o agente registra em `decisoes.md` e faz push.

Regra de ouro com dois computadores: **pull ao abrir, push ao terminar.**
