# Handoff — conversa de planejamento do Papeto (até 25/11/2026)

Resumo da conversa com o Claude (claude.ai) em que o produto foi planejado. Serve para um agente que começa agora
(Claude Code, Codex, etc. no Orca) entender o que já foi decidido, o que existe e o que falta.
Regras de código e de produto continuam em `AGENTS.md` e `docs/`; este arquivo é o histórico e o estado.

## 1. O produto

- **Papeto:** app mobile (iOS e Android) em que a pessoa cuida do pet virtual **Bolinha**, que vive da constância dela em **registrar refeições por foto**. Uma IA descreve o prato.
- **MVP = só alimentação.** Treino, arena, social e evolução por força ficam para as Fases 2 e 3 (o `docs/scope.md` ainda tem essa história: não implementar).
- **Público:** adultos 18+, Brasil, interface em pt-BR.
- **Nome:** Papeto (Grampy foi descartado por marca registrada). Busca formal no INPI, WIPO e USPTO ainda não feita.

## 2. Decisões tomadas (em ordem)

| Tema | Decisão |
| --- | --- |
| Backend | FastAPI em Python; ARQ em vez de Celery; estado do pet calculado na leitura |
| Deploy | Fly.io região `gru` (API, worker ARQ, Postgres gerenciado), Upstash Redis, Expo EAS; Cloudflare opcional na borda |
| Idioma do código | Tudo em inglês (código, banco, API, commits). UI em pt-BR via i18n |
| Pagamentos | Stripe, trocável: padrão Ports and Adapters para **todos** os provedores |
| Front-end | React Native + Expo, Gluestack UI sobre NativeWind (bibliotecas em `frontend/AGENTS.md`) |
| Plano grátis | 2 fotos com IA por dia |
| Pausa | Recurso Premium (o risco para usuários grátis foi registrado no escopo) |
| Vidas | 2 ao começar, até 4; +1 a cada 7 dias seguidos com registro; −1 por dia sem registro, exceto em pausa; com 0 o pet desmaia e um registro acorda com 1 vida |
| Mascote e logo | Gerados no Gemini; logo principal e ícone escolhidos. Versão final precisa ser redesenhada em vetor |
| Métricas da refeição | Accordion "Sobre este prato" aberto por padrão: parte grátis (grupos, itens, cores, confiança) e "Seus hábitos" Premium, todo bloqueado com blur |
| Onboarding | O nome do pet é pedido **antes** de mostrar o pet (tela 43); depois vem a revelação (24) |
| Reembolso | Compras no site: só os 7 dias do CDC (art. 49) |
| Advogado | Lançar sem revisão jurídica por enquanto; revisar antes de cobrar o Premium/crescer |
| Ambiente | Projeto em `Área de Trabalho\Projetos\papeto` (dentro do OneDrive, decisão do usuário), pastas `frontend` e `be` |

Decisões que o Claude tomou e que **o usuário ainda precisa confirmar**:

1. Humor "sonolento" = pet com 1 vida (o escopo dizia "2 dias sem registro", o que colide com o desmaio).
2. Vidas aplicadas por `settle()` na leitura, sem depender de cron.
3. Máximo de 3 refeições pontuadas por dia (+10 cada) e +5 ao acordar o pet.
4. Pix não renova sozinho; aumento de preço com 30 dias de aviso; pagamento falho volta ao grátis sem perder nada; encerramento do app devolve valor proporcional de assinaturas pelo site.
5. Fila (Upstash) na região de São Paulo.

## 3. O que existe

| Entregável | Onde | Estado |
| --- | --- | --- |
| Doc de escopo e requisitos | https://claude.ai/artifact/LTBCF9VPoJm4S6jauwhivS (cópia em `docs/scope.md`) | Completo; tem mapa do app, tabela de 42 telas, modelo de dados, stack, deploy, página das lojas |
| Canvas de design | https://claude.ai/artifact/1kwmN9FBtScfqXR6yRmJ2N | Página **Layout** com as telas 1–43 em alta fidelidade e protótipo no Play; página **Fluxo** com o diagrama de setas; página **Wireframe** antiga |
| Validação de fluxo e acessibilidade | https://claude.ai/artifact/K2nUQe9TGzhKcqq7yDdezy (resumo em `docs/screens.md`) | 14 problemas de fluxo: 12 corrigidos no canvas, 2 viraram regras do app; acessibilidade corrigida; tabela de estados por tela; roteiro de teste com 5 pessoas |
| Termos de Uso e Política de Privacidade | https://claude.ai/artifact/Dk8YdzqynRskhEP5iU4Az1 (regras em `docs/product-rules.md`) | Versão 1.0 completa, sem revisão jurídica; faltam dados da empresa, e-mails e o provedor de IA |
| Regras para agentes | `AGENTS.md`, `CLAUDE.md`, `be/`, `frontend/`, `.cursor/rules/` | Prontos. Faltam `.claude/settings.json` e `.github/copilot-instructions.md` (criar à mão) |
| Prompt para começar o código | `docs/prompts/bootstrap.md` | Pronto, em 3 etapas: backend, app, CI |
| Prompt de animação | `docs/prompts/rive.md` | Pronto; depende do Bolinha em SVG com partes nomeadas |
| Vídeos de demonstração | Só na conversa | Mostram a versão antiga das telas |

## 4. O que falta (por prioridade)

1. **Validar a IA de visão:** prompt, schema Pydantic e ~30 pratos de teste para medir acerto. Também escolhe o provedor (ainda indefinido).
2. **Números do Premium:** preço (depende do teto de custo de infra; o escopo ainda diz US$ 50/mês) e quantas fotos por dia o Premium dá.
3. **Código:** rodar `docs/prompts/bootstrap.md` (backend → app → CI), uma worktree por etapa no Orca.
4. **Teste com 5 pessoas** usando o roteiro do doc de validação.
5. **Marca:** INPI, WIPO, USPTO, domínios e perfis.
6. **Termos:** preencher dados da empresa; no app, adicionar a segunda caixa de consentimento (dados de refeição) na tela 2 e a área Perfil > Privacidade (revogar consentimento, desligar analytics).
7. **Arte:** Bolinha em vetor com partes nomeadas, poses "acordando" e "perdendo vida", variações de cor, logo em vetor, animações no Rive.

## 5. Como continuar

- Primeira mensagem para o agente: "Leia `AGENTS.md` e `docs/handoff.md`. Depois siga `docs/prompts/bootstrap.md`, começando pela etapa 1."
- Se um doc vivo (links acima) mudar, a cópia em `docs/` precisa ser atualizada; o agente não consegue abrir os links do claude.ai.
- A conversa original continua no claude.ai, na lista de chats do usuário.
