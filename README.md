# Investimentos

## O que é
- **Relatório semanal:** toda segunda às 7h (Brasília) o GitHub Actions gera um relatório de macro e mercados em `relatorios/`, a partir do prompt em `prompts/relatorio_semanal.md`.
- **Agente de alocação:** o `CLAUDE.md` transforma o Claude Code num analista que cruza esse relatório com o **seu** perfil e a **sua** carteira para sugerir onde aportar.

É apoio à decisão, **não é recomendação de investimento**. A decisão e a execução são suas.

## Como começar
1. Clone o repositório:
   ```
   git clone https://github.com/pedropepe2001code/Investimentos.git
   ```
2. Abra a pasta no VS Code e inicie o Claude Code nela.
3. O agente copia os modelos de `modelos/` para a raiz e faz uma entrevista curta para preencher o seu `perfil.md`.

`perfil.md`, `carteira.md` e `decisoes.md` ficam **só no seu PC**. Eles estão no `.gitignore`.

## Uso semanal
1. `git pull` para receber o relatório novo.
2. Pergunte ao Claude Code, por exemplo:
   - "Leia o relatório novo e me diga o que mudou para a minha carteira."
   - "Tenho R$ 5.000 para aportar. Onde coloco?"

## Regras
- **Nunca** faça push de `perfil.md`, `carteira.md` ou `decisoes.md`.
- Com este repo, use só `git pull`.

## Requisitos
- [Claude Code](https://claude.com/claude-code) instalado.
- Plano pago do Claude.
