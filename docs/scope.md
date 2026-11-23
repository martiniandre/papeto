> **Snapshot** of the scope doc exported on 2026-11-25 (live version: https://claude.ai/artifact/LTBCF9VPoJm4S6jauwhivS).
> It keeps the history of the product: sections about workouts (Treino), arena, social and calories are later phases or superseded.
> For rules, `docs/domain/pet-rules.md` and `docs/product-rules.md` take precedence. Diagrams and images are not included in this export.

# Papeto: requisitos e escopo

Nov 25, 2026 · @André

## Visão e decisões

- **Nome do app: Papeto** (decisão de 25/11/2026). Vem de “papar” e “papa”, funciona em português e espanhol e é neutro em inglês. Na triagem prévia não apareceu app nem marca com esse nome; o mais próximo é a PapaPets (alimentação natural para pets). Antes de registrar: busca no INPI (classes 9, 41 e 42, incluindo “Papapet”), WIPO e USPTO, domínios (.app, .com e .com.br) e @ nas redes. O pet de exemplo continua se chamando Bolinha.

App mobile em que o usuário cuida de um pet que vive da constância de exercício dele, sem punição pesada: se o usuário some, o pet desmaia e volta quando ele treina de novo.

**Decisões já tomadas na conversa**

- **Começa por exercício.** Alimentação por foto entra depois, como módulo opcional, porque o risco de pressão e de relação ruim com a comida é maior.
- **O pet não morre.** Ele passa por cansado, sonolento e desmaiado. Voltar é sempre recompensado.
- **Recompensa por regularidade, não por volume.** Sem ranking de peso, calorias queimadas ou medidas corporais, e o crescimento do pet nunca depende de peso, altura ou calorias do usuário.
- **Descanso e pausa contam.** No premium, a pausa protege o pet em doença, lesão e viagem; no grátis, o pet tem de 2 a 4 vidas de margem.
- **Arte e nome originais.** Não copiar mascote, texto ou identidade de nenhum concorrente.

**Referências de mercado já vistas**

- Finch: pet de autocuidado de baixa pressão.
- BitePal: contador de calorias com mascote, mais de 5 milhões de downloads.
- FitFolio: registro de treino e dieta com ranking, focado no usuário final.

**Público inicial:** adultos de 18 anos ou mais que querem manter constância de treino, no Brasil, em português.

## Escopo

O MVP entrega o laço completo do pet de exercício (criar, treinar, evoluir, desmaiar, voltar) em Android e iOS, sem IA de comida e sem integração com relógio.

| Módulo | MVP (Fase 1) | Depois (Fases 2 e 3) | Fora do escopo |
| --- | --- | --- | --- |
| Conta e perfil | Cadastro com Apple, Google ou e-mail e senha, idade mínima 18, consentimento LGPD, exclusão de conta | Vincular métodos de login, múltiplos dispositivos | Perfis para menores de 18 |
| Pet | Criar e nomear, 4 estados, evolução por níveis, desmaio e retorno | Mais espécies, itens e cenários, eventos sazonais | Pet que morre ou perde progresso permanente |
| Treino | Registro manual ou envio de qualquer prova do treino validado por IA (tipo, duração, esforço), histórico, meta semanal própria | Apple Saúde, Health Connect, Strava, foto do treino | Planos de treino prescritos e análise biométrica |
| Pausa e descanso | Modo pausa e dia de descanso que preservam a sequência | Pausa automática por inatividade longa | Diagnóstico ou orientação médica |
| Notificações | Lembretes gentis com limite e horário silencioso | Notificações personalizadas por horário de treino | Notificações de culpa ou cobrança |
| Social | Compartilhar cartão do pet | Amigos, pet de grupo, desafios fechados, rankings de constância e arena de pets (premium) | Rankings de peso, calorias ou medidas |
| Alimentação | Não incluído | Módulo opcional e premium: hábitos escolhidos, pontos só positivos e foto da refeição com estimativa por IA, sem número por padrão | Metas de calorias, jejum, dietas por doença |
| Monetização | Gratuito | Assinatura com itens, cenários, extras de pet, evolução por força e resistência, arena e módulo de alimentação | Anúncios de produtos de dieta, venda de dados |
| Administração | Painel simples de métricas e feature flags | Painel para treinadores e grupos | App web completo |

## MVP pela alimentação (decisão de escopo)

O MVP passa a ser o pet que come: o usuário fotografa a refeição, a IA identifica o que há no prato e o pet reage. O treino, a validação de treino por IA e as importações de saúde passam para a Fase 2. Como “avaliar” a refeição é a parte mais sensível do produto, a avaliação descreve o prato e não dá nota.

**O que a avaliação devolve**

| Item | O que o usuário vê | Observação |
| --- | --- | --- |
| Alimentos e tipo de refeição | Lista do que a IA reconheceu (por exemplo arroz, feijão, ovo) e se é café, almoço, jantar ou lanche | O usuário confirma, corrige ou acrescenta itens |
| Porções | Estimativa aproximada | Sempre rotulada como estimativa e ajustável |
| Variedade | Quais grupos de alimentos aparecem no dia | Descrição, sem nota nem rótulo de saudável ou não saudável |
| Informação nutricional | Calorias e macros aproximados | Desligada por padrão, o usuário liga nos ajustes, e nunca aparece no pet nem na arena |
| Reação do pet | O pet come, comemora e ganha pontos só positivos | Por variedade e regularidade, nunca perde pontos |

**Requisitos do MVP de alimentação**

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-90 | O usuário tira uma foto ou envia da galeria uma foto da refeição | M |
| RF-91 | A IA identifica os alimentos e o tipo de refeição, e o usuário confirma, corrige ou acrescenta itens antes de salvar | M |
| RF-92 | A IA estima porcões aproximadas, rotuladas como estimativa, e o usuário pode ajustá-las | M |
| RF-93 | O resultado descreve a refeição (alimentos e variedade) sem nota, sem rótulo de saudável ou não saudável e sem tirar pontos | M |
| RF-94 | Calorias e macros aproximados só aparecem se o usuário ligar a opção nos ajustes | S |
| RF-95 | Se a foto não parecer comida ou a IA não conseguir identificar, o app avisa e deixa o usuário descrever por texto ou escolher os alimentos à mão | M |
| RF-96 | O pet reage à refeição registrada, com pontos só positivos por variedade e regularidade | M |
| RF-97 | O usuário vê o histórico de refeições, sem total diário de calorias por padrão | M |
| RF-98 | Se o uso indicar um padrão de risco (por exemplo muitos dias seguidos de refeições puladas), o app mostra uma mensagem acolhedora e um caminho discreto de apoio, sem punir | M |

**Salvaguardas obrigatórias já no MVP**

1. Idade mínima 18 anos, com o sinal de idade da loja.
2. Nenhuma nota, rótulo de saudável ou não saudável, nem perda de pontos por comida.
3. Números de calorias desligados por padrão e fora do pet, da arena e de qualquer ranking.
4. A foto é descartada após a análise e não fica guardada.
5. O usuário pausa ou desliga o módulo a qualquer momento, sem perder o pet.
6. Aviso de que o app não substitui médico nem nutricionista e caminho de apoio visível nos ajustes.
7. Revisão jurídica e das regras das lojas para apps de nutrição antes do lançamento.

**Free e premium na alimentação**

| Recurso | Plano |
| --- | --- |
| Foto, avaliação por IA, pet e histórico recente (RF-90 a RF-98) | Free com 2 fotos com IA por dia |
| Histórico completo, hábitos escolhidos e pontos positivos extras (RF-64, RF-65) | Premium |
| Apoio, desligar o módulo, exportar e excluir dados | Free sempre |

## Free e premium

O app é gratuito para manter o pet vivo e criar o hábito. O premium paga personalização, competição e os recursos que têm custo por uso.

**Regras da divisão**

1. **Quem paga não ganha força.** O premium muda o visual, a personalização e o acesso à arena, nunca o poder do pet na disputa.
2. **Segurança e direitos nunca ficam atrás de paywall:** descanso, modo sem números, exportar e excluir dados e o caminho de apoio.
3. **O que tem custo por uso tem limite no gratuito,** e o registro manual de treino é sempre ilimitado e gratuito.
4. **Manter o pet vivo nunca exige assinatura.**

| Recurso | Requisitos | Plano | Por quê |
| --- | --- | --- | --- |
| Conta, login e exportar ou excluir dados | RF-01 a RF-05 | Free | Direito do usuário e obrigação legal |
| Pet básico, 4 estados e evolução por nível | RF-10 a RF-13 | Free | É o produto central |
| Registro manual de treino, histórico e meta | RF-20 a RF-23 | Free | Não tem custo e é a base do hábito |
| Envio de prova do treino validado por IA | RF-26 a RF-28 | Free com 2 fotos com IA por dia | Tem custo por uso, e o registro manual segue ilimitado |
| Importação de Apple Saúde, Health Connect e Strava | RF-24, RF-25 | Free | É barata e reduz o uso de IA |
| Descanso, pausa e retorno | RF-30 a RF-32 | Free | Segurança do usuário |
| Notificações e horário silencioso | RF-40 a RF-42 | Free | Controle do usuário |
| Moedas e itens básicos | RF-14 | Free | Recompensa pela constância |
| Cartão compartilhável e amigos | RF-50, RF-51 | Free | Crescimento orgânico |
| Itens, cenários e espécies extras | RF-14, RF-15 | Premium | Personalização visual |
| Evolução por força e resistência | RF-16 | Premium | Visual, sem vantagem na disputa |
| Arena, ligas e torneios de pets | RF-53 | Premium | Competição sem pagar por força |
| Grupos fechados com pet coletivo | RF-52 | Premium (para quem cria o grupo) | Abre caminho para assessorias e academias |
| Alimentação: foto, avaliação por IA e pet (núcleo do MVP) | RF-60 a RF-65 | Free com limite diário; hábitos e histórico completo no premium | Tem custo de IA e exige cuidado |
| Painel de métricas e feature flags | RF-70, RF-71 | Interno | Não é recurso do usuário |
| Painel de métricas de constância do usuário | RF-72 a RF-74 | Premium (o básico do RF-23 é free) | Visão profunda da própria constância |
| Assinatura, restaurar compras e cancelamento | RF-80 a RF-83 | Todos os planos | Quem cancela mantém o pet e o histórico |

### Requisitos por plano

Cada requisito pertence a um plano. Nenhum requisito de segurança ou de direito do usuário é premium. Os requisitos não funcionais valem para todos os planos; dependem do plano apenas RNF-16 e RNF-22 (limite de IA no free) e RNF-24 (assinatura).

**Plano free**

| Requisitos | Resumo | Fase |
| --- | --- | --- |
| RF-01 a RF-04 | Conta, consentimentos, idade mínima 18, exportar e excluir dados | 1 |
| RF-05 | Vincular outro método de login | 2 |
| RF-10 a RF-13 | Pet, 4 estados, energia, níveis, animação de suor e retorno do desmaio | 1 |
| RF-14 (parte básica) | Moedas e itens básicos por constância | 2 |
| RF-20 a RF-23 | Registro manual, edição, meta própria e histórico básico | 1 |
| RF-24 | Importação do Apple Saúde e do Health Connect | 2 |
| RF-25 | Importação do Strava | 3 |
| RF-26 a RF-28 | Envio de prova do treino validado por IA, com limite diário | 1 |
| RF-30, RF-31 | Dia de descanso e modo pausa | 1 |
| RF-32 | Boas-vindas ao fim da pausa | 2 |
| RF-40 a RF-42 | Avisos gentis, horário silencioso e texto sem culpa | 1 |
| RF-50, RF-51 | Cartão compartilhável e amigos | 2 |

**Plano premium**

| Requisitos | Resumo | Fase |
| --- | --- | --- |
| RF-14 (itens e cenários extras) | Catálogo ampliado de itens e cenários | 2 |
| RF-15 | Outras espécies, personalização e vários pets com troca de pet ativo (RF-17) | Depois |
| RF-16 | Evolução por força e resistência | 2 |
| RF-72 | Painel: constância de 12 semanas, histórico por semana e mês, maior sequência e mix de treinos | 2 |
| RF-73 | Painel: melhor dia e horário, esforço médio com semanas de carga alta e tempo de retorno | 2 |
| RF-74 | Painel: comparação com o próprio mês anterior e resumo semanal ou mensal compartilhável, sem números do corpo | 2 |
| RF-52 | Grupos fechados com pet coletivo e ranking de constância | 3 |
| RF-53 | Arena de pets, ligas e torneios | 3 |
| RF-60 a RF-65 | Módulo de alimentação opcional, com hábitos escolhidos e pontos só positivos | 3 |

**Gestão do plano (todos os usuários) e itens internos**

| Requisitos | Resumo | Fase |
| --- | --- | --- |
| RF-80 | O usuário assina pelo sistema de compras da loja, e o plano é validado no servidor | 2 |
| RF-81 | O usuário restaura compras ao trocar de aparelho | 2 |
| RF-82 | Ao cancelar ou expirar, o usuário mantém pet, nível e histórico e só perde os recursos premium | 2 |
| RF-83 | A tela de assinatura mostra o que é free e premium, o preço e como cancelar, sem pressão nem contagem regressiva falsa | 2 |
| RF-70 | Métricas de retenção e uso para o time (interno) | 1 |
| RF-71 | Feature flags (interno) | 2 |

## Requisitos funcionais

Prioridade: **M** = precisa estar no MVP, **S** = entra logo depois, **C** = desejável.

### Conta e privacidade

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-01 | O usuário cria conta com Apple, Google ou e-mail e senha (com e-mail confirmado) | M |
| RF-02 | O cadastro exige data de nascimento, usa o sinal de idade da loja quando disponível e bloqueia menores de 18 anos | M |
| RF-03 | O usuário aceita termos e política de privacidade e consente separadamente com o uso de dados de saúde | M |
| RF-04 | O usuário exporta e exclui seus dados e sua conta dentro do app | M |
| RF-05 | Vincular outro método de login à mesma conta e recuperar o acesso se perder um deles | S |

### Pet

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-10 | O usuário escolhe uma espécie inicial, dá um nome ao pet, escolhe uma cor básica e vê o pet na tela principal | M |
| RF-11 | O pet tem os estados animado, cansado, sonolento e desmaiado, cada um com animação própria | M |
| RF-12 | O pet ganha energia e níveis a cada treino registrado, faz uma animação de suor ao registrar (mais forte conforme o esforço informado) e evolui de forma visual em marcos de nível | M |
| RF-13 | Um treino registrado acorda o pet desmaiado e mostra uma mensagem acolhedora de retorno | M |
| RF-14 | O usuário ganha moedas e itens (cenários, acessórios) por regularidade | S |
| RF-15 | O usuário escolhe outras espécies e personaliza o pet (cores, acessórios e cenário), sem opções que representem peso ou corpo | C |
| RF-16 | Assinantes desbloqueiam a evolução visual por força e resistência, calculada pelo tipo e pela constância dos treinos, sem usar peso, altura ou calorias | S |
| RF-17 | Assinantes têm vários pets e trocam o pet ativo; cada pet mantém nível, evolução e histórico, e o pet que não está ativo descansa sem desmaiar | C |

### Treino

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-20 | O usuário registra um treino com tipo, duração, esforço percebido e data, em até 3 toques após abrir o formulário | M |
| RF-21 | O usuário edita e apaga treinos já registrados, e o estado do pet é recalculado | M |
| RF-22 | O usuário define a própria meta semanal (número de treinos) e a altera quando quiser | M |
| RF-23 | O app mostra o histórico semanal e mensal de constância, sem metas corporais | M |
| RF-24 | Importa treinos do Apple Saúde e do Health Connect | S |
| RF-25 | Importa treinos do Strava | C |
| RF-26 | O usuário envia qualquer arquivo que simbolize o treino (captura de relógio ou app, foto, comprovante, mapa de rota, vídeo curto) e a IA valida e preenche tipo, duração e esforço quando visíveis; o usuário confirma ou corrige antes de salvar | M |
| RF-27 | Se a IA não conseguir confirmar o treino, o app avisa e deixa o usuário registrar mesmo assim; nunca há rejeição sem alternativa | M |
| RF-28 | O envio de prova por IA tem limite diário no plano free; o app mostra quantos envios restam e, quando acabam, oferece o registro manual, que continua ilimitado | M |

### Pausa e descanso

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-30 | O usuário marca um dia de descanso, que mantém a sequência e o pet animado | M |
| RF-31 | O usuário ativa o modo pausa por período definido (doença, lesão, viagem), e o pet não desmaia durante ele | M |
| RF-32 | Ao fim da pausa o app dá boas-vindas e sugere uma meta leve de retorno | S |

### Notificações

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-40 | O app envia no máximo um aviso ao entrar em cansado e outro ao entrar em sonolento, e nenhum depois de desmaiar | M |
| RF-41 | O usuário escolhe horário silencioso e desliga qualquer notificação | M |
| RF-42 | O texto das notificações nunca culpa o usuário nem cita corpo, peso ou calorias | M |

### Compartilhamento e social

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-50 | O usuário gera e compartilha um cartão visual do pet e da sequência | S |
| RF-51 | O usuário adiciona amigos por código ou link e vê o pet deles | S |
| RF-52 | Grupos fechados têm pet coletivo e ranking de constância (não de volume ou corpo) | C |
| RF-53 | Arena premium: os pets disputam ligas e torneios em que a força vem da constância do próprio usuário em relação à meta dele, com ligas por nível, sem comparar peso, calorias ou volume de treino e sem apostas | C |

### Alimentação (módulo opcional, fase posterior)

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-60 | O usuário ativa o módulo por escolha própria, e ele fica desligado por padrão | C |
| RF-61 | O usuário envia uma foto da refeição e recebe uma estimativa rotulada como aproximada, que pode confirmar ou corrigir | C |
| RF-62 | Números de calorias ficam ocultos por padrão, e o pet reage ao registro, não ao resultado | C |
| RF-63 | O app detecta padrões de risco no uso (por exemplo restrição repetida) e mostra um caminho discreto de apoio | C |
| RF-64 | O módulo dá pontos só positivos por variedade e regularidade (por exemplo refeições em horários regulares ou verdura, legume ou fruta registrados) e nunca tira pontos nem classifica comida como boa ou ruim | C |
| RF-65 | O usuário escolhe os próprios hábitos de alimentação (beber água, verdura no almoço, café da manhã) e o pet comemora quando ele cumpre, sem número de calorias | C |

### Administração e dados

| ID | Requisito | Prioridade |
| --- | --- | --- |
| RF-70 | O time vê métricas de retenção, ativação e retorno depois do desmaio | M |
| RF-71 | O time liga e desliga funcionalidades por feature flag, sem nova versão do app | S |

### Métricas do plano pago (RF-72 a RF-74)

O plano pago mostra ao usuário uma visão mais profunda da própria constância. O plano gratuito mantém o básico (treinos da semana contra a meta e sequência atual, RF-23).

| Métrica | O que mostra | Como é calculada |
| --- | --- | --- |
| Constância das últimas 12 semanas | Em quantas semanas a meta foi cumprida | Treinos validados contra a meta da semana |
| Histórico de treinos por semana e mês | A evolução além dos últimos 3 meses | Contagem de treinos por período |
| Maior sequência | O recorde pessoal e a sequência atual | Dias de treino, descanso e pausa seguidos |
| Mix de treinos | A divisão entre força, cardio, mobilidade e outros | Tipo informado em cada treino |
| Força e resistência do pet | Os índices que fazem o pet evoluir (RF-16) | Tipo e regularidade dos treinos, sem peso, altura ou calorias |
| Melhor dia e horário | Quando o usuário mais treina | Mapa de calor por dia da semana e horário |
| Esforço médio e semanas de carga alta | Como o esforço percebido variou | Média do esforço informado, com aviso de descanso |
| Tempo de retorno | Quantos dias o usuário leva para voltar depois de uma pausa ou desmaio | Dias entre o estado desmaiado e o treino seguinte |
| Comparação com o próprio mês anterior | Se a constância subiu ou caiu | Constância do mês contra a do mês anterior |
| Resumo semanal e mensal compartilhável | Um cartão com os destaques do período | Dados acima, sem números do corpo |

**Nunca aparece, em nenhum plano:** peso, altura, calorias, comparação de corpo e ranking de volume de treino. O aviso básico de descanso depois de muitos dias de esforço alto fica no plano gratuito, porque é segurança.

## Requisitos não funcionais

Os números abaixo são metas iniciais de projeto, para ajustar depois de medir o app real.

| ID | Categoria | Requisito | Meta |
| --- | --- | --- | --- |
| RNF-01 | Desempenho | Abertura do app até a tela do pet | até 2 s em aparelho intermediário |
| RNF-02 | Desempenho | Resposta da API para registrar um treino | até 500 ms no percentil 95 |
| RNF-03 | Desempenho | Animações do pet | 60 quadros por segundo, sem travar a interface |
| RNF-04 | Disponibilidade | API em produção | 99,5% ao mês, com backups diários |
| RNF-05 | Offline | Registrar treino sem internet | grava no aparelho e sincroniza depois, sem perder dados |
| RNF-06 | Segurança | Autenticação e sessão | tokens com expiração, senhas com hash forte, limite de tentativas |
| RNF-07 | Segurança | Tráfego e armazenamento | HTTPS em tudo e dados sensíveis criptografados em repouso |
| RNF-08 | Privacidade (LGPD) | Dados de saúde e treino | consentimento específico, coleta mínima, finalidade declarada, nenhuma venda ou repasse a terceiros |
| RNF-09 | Privacidade (LGPD) | Direitos do titular | exportar e excluir dados em até 15 dias, com exclusão imediata no app |
| RNF-10 | Privacidade | Fotos de refeição (fase posterior) | não guardar a imagem após a análise, ou guardar só com consentimento claro |
| RNF-11 | Bem-estar | Texto e regras de jogo | sem culpa, sem mencionar peso ou corpo, sem punição permanente |
| RNF-12 | Acessibilidade | Interface | contraste adequado, leitor de tela, textos escaláveis e alternativa sem animação |
| RNF-13 | Compatibilidade | Plataformas | Android 8 ou superior e iOS 15 ou superior |
| RNF-14 | Localização | Idioma e fuso | português do Brasil, horário de Brasília, virada do dia no fuso do usuário |
| RNF-15 | Custo | Infraestrutura no início | até cerca de US$ 50 por mês até as primeiras centenas de usuários |
| RNF-16 | Custo (IA) | Análise de foto | limite diário por usuário, imagem reduzida e cache de resultados |
| RNF-17 | Observabilidade | Erros e uso | rastreio de erros, logs sem dados pessoais e painel de métricas |
| RNF-18 | Manutenibilidade | Código | Python com tipagem (mypy ou pyright), testes automatizados da lógica do pet, CI em cada mudança |
| RNF-19 | Lojas | Conformidade | política de privacidade pública, declaração de dados de saúde e aviso de que o app não substitui profissional |
| RNF-20 | Confiabilidade | Regras do pet | calculadas no servidor, com a mesma regra para todos os aparelhos e testes cobrindo fuso e horário de verão |
| RNF-21 | Privacidade | Arquivos enviados para validar treino | processar e descartar após a análise, sem guardar imagens nem localização, com aviso claro antes do envio |
| RNF-22 | Custo e desempenho | Validação por IA | resposta em até 10 s, limite diário por usuário, imagem reduzida antes do envio e checagem de tipo e tamanho antes de chamar a IA |
| RNF-23 | Confiabilidade da IA | Erros da validação | tolerância alta a aceitar treino duvidoso (nada valioso em jogo), taxa de recusa errada medida no beta e fallback manual sempre disponível |
| RNF-24 | Pagamentos | Assinatura e estado do plano | pagamento pelas lojas, sem guardar dados de cartão, e plano validado no servidor para não liberar recursos premium por engano |

## Regras do pet

### Vidas do pet (decisão de 25/11/2026)

O pet tem vidas, mostradas como corações no Início. As regras abaixo substituem a contagem de dias sem registro onde houver conflito.

| Regra | Valor |
| --- | --- |
| Vidas ao começar | 2 |
| Máximo de vidas | 4 |
| Como ganhar uma vida | Manter a sequência: +1 vida a cada 7 dias seguidos com registro (valor inicial, a testar) |
| Como perder uma vida | Terminar o dia sem nenhuma refeição registrada, no fuso do usuário |
| Pausa (premium) | Durante a pausa o pet não perde vidas e a sequência fica guardada |
| Sem vidas | O pet desmaia; uma refeição registrada acorda ele com 1 vida |
| Fotos com IA no grátis | 2 por dia |

- **Linguagem:** o app fala sempre em “registrar” e nunca em “comer” ou “alimentar”. A vida cai por falta de registro, não por falta de comida.
- **Desmaio sem perda:** pontos, visuais e histórico continuam intactos depois do desmaio.
- **Risco registrado:** com a pausa no premium, um usuário grátis doente ou viajando perde vidas. Mitigações: as vidas extras como margem, avisos gentis, desmaio reversível e nenhum aviso sobre vidas durante a madrugada. Rever com os dados do beta.

### Estados e animações do Bolinha

Arte conceitual gerada no Gemini em 25/11/2026. Serve de briefing: a versão final precisa ser redesenhada em vetor e animada no Rive (ou Lottie), mantendo o mesmo personagem em todas as poses.

&#91;image: Bolinha nos estados referência, animado, cansado, sonolento, desmaiado, pausado e comemorando\]

| Estado | Quando aparece | Animação sugerida | Tipo |
| --- | --- | --- | --- |
| Animado | Registrou hoje e tem vidas | Pulinho leve e piscar de olhos | Repetição contínua |
| Cansado | 1 dia sem registro | Orelhas caídas, respiração lenta | Repetição contínua |
| Sonolento | 2 dias sem registro | Bocejo a cada poucos segundos | Repetição contínua |
| Desmaiado | Vidas zeradas | Deitado de lado, olhos em x, “zzz” subindo | Repetição contínua |
| Pausado | Pausa ativa (premium) | Dormindo de touca, respiração tranquila | Repetição contínua |
| Comemorando | Ganhou vida, assinou ou bateu sequência | Braços para cima, estrela e confete | Evento, toca uma vez |
| Acordando | Primeiro registro depois do desmaio | Levanta, se espreguiça e sorri | Evento, toca uma vez |
| Perdendo vida | Início do dia após um dia sem registro | Coração sai e o pet fica cansado | Evento, toca uma vez |

- **No app:** o servidor devolve o estado (`happy`, `tired`, `sleepy`, `fainted`, `paused`) e o app só escolhe a animação; os eventos (`wake_up`, `life_lost`, `celebrate`) vêm na resposta do registro.
- **Ajustes para o redesenho:** padronizar as orelhas (nas poses cansado, sonolento e desmaiado elas mudam de formato), decidir se o pet tem rabo (só aparece dormindo) e corrigir o braço da vista lateral.
- **Faltam gerar:** as poses “acordando” e “perdendo vida”, as variações de cor da tela de pets e os estágios da evolução (Fase 2).

O estado do pet depende de quantos dias seguidos o usuário ficou sem treinar, sem contar dias de descanso e de pausa. Os limites abaixo são um ponto de partida para testar com usuários reais.

| Estado | Gatilho | O que o usuário vê | O que acontece |
| --- | --- | --- | --- |
| Animado | Treinou dentro da meta ou está em descanso ou pausa | Pet ativo e alegre | Ganha energia e nível normalmente |
| Cansado | 1 dia sem treinar, fora de descanso ou pausa | Pet bocejando | 1 aviso gentil no máximo |
| Sonolento | 2 dias sem treinar | Pet com olhos pesados | 1 aviso gentil no máximo |
| Desmaiado | 3 dias ou mais sem treinar | Pet dormindo, com estrelinhas e "zzz" | Nenhuma notificação nova; a sequência zera |

**Regras de jogo**

1. **Energia:** cada treino válido dá energia ao pet, com um teto diário para que treinar mais não dê vantagem injusta.
2. **Nível e evolução:** a energia acumulada sobe o nível, e certos níveis mudam a aparência do pet. Não há perda de nível por desmaiar.
3. **Retorno:** um treino registrado acorda o pet na hora, com mensagem acolhedora, e o recoloca em animado.
4. **Sequência:** dias de treino, descanso e pausa mantêm a sequência. Só o desmaio a zera.
5. **Descanso:** o usuário pode marcar até um número de dias de descanso por semana (valor inicial a validar), sem justificar.
6. **Pausa:** recurso premium, por período escolhido (1, 3 ou 7 dias). Durante a pausa o pet não perde vidas e a sequência fica guardada.
7. **Treino válido:** qualquer atividade física registrada com duração mínima baixa. Um treino curto vale.
8. **Anti-abuso:** limite de registros por dia e checagem de datas futuras, sem punir quem esqueceu de registrar (permitir registro retroativo de até alguns dias).
9. **Fuso e virada do dia:** calculados no horário do usuário, e o servidor é a fonte de verdade.

**Tom das mensagens:** acolhedor e curto. Exemplo de retorno: o pet só precisava de um cochilo, que bom que o usuário voltou. Nunca culpar, nunca citar corpo, peso ou calorias.

### Pontos (proposta inicial, valores a testar)

| Evento | Pontos | Regra |
| --- | --- | --- |
| Treino validado | 10 | Vale igual para qualquer tipo e duração acima do mínimo, até 2 treinos pontuados por dia |
| Meta semanal cumprida | +20 | A meta é a do próprio usuário |
| Retorno depois de desmaiar | +5 | Uma vez por retorno |
| Dia de descanso ou pausa | 0 | Não perde pontos nem sequência |
| Hábito de alimentação (Fase 3, opcional e premium) | só bônus positivos no pet | Só ganha, nunca perde: bônus por variedade, regularidade ou hábito escolhido, com teto diário, sem julgar o prato nem usar calorias, e não conta na arena |

Na arena (RF-53), a pontuação da semana é medida em percentual da meta do próprio usuário, para que quem treina menos tenha a mesma chance.

## Dados e integrações

O modelo de dados do MVP tem seis entidades, todas ligadas ao usuário. Dados de saúde ficam separados dos dados de conta.

| Entidade | Campos principais | Observação |
| --- | --- | --- |
| Usuário | id, e-mail, data de nascimento, fuso, consentimentos, criado em | Idade mínima 18 verificada no cadastro |
| Pet | id, usuário, espécie, nome, nível, energia, estado, última atividade | Estado recalculado no servidor |
| Treino | id, usuário, tipo, duração, esforço, data, origem (manual ou integração) | Dado sensível, acesso restrito |
| Descanso e pausa | id, usuário, tipo, início, fim | Preservam a sequência |
| Meta | id, usuário, treinos por semana, vigência | Definida pelo próprio usuário |
| Evento de uso | id, usuário, nome, data | Para métricas, sem texto livre nem dados de saúde detalhados |

**Integrações**

- **Notificações push:** serviço de push do Expo no início, e Firebase Cloud Messaging e Apple Push depois, se necessário.
- **E-mail transacional:** confirmação de conta e recuperação de senha.
- **Apple Saúde e Health Connect (Fase 2):** leitura de treinos com permissão explícita do usuário e só dos tipos necessários.
- **Strava (Fase 3):** OAuth e importação de atividades, sujeito à aprovação da plataforma.
- **Compras no app (Fase 2):** camada de pagamentos com adaptador (Stripe primeiro) para assinatura e itens.
- **Análise de imagem (MVP, para validar treino, e Fase 3, para comida):** modelo de visão via API, com limite de uso e sem guardar a foto por padrão.
- **Analytics e erros:** ferramenta de analytics de produto e rastreio de erros, sem dados pessoais nos eventos.

## Arquitetura e stack

&#91;embedded content: arquitetura do MVP · 5 componentes, 2 na fase 2 e 3\]

O app só mostra o estado do pet que o servidor calcula, então o resultado é o mesmo em qualquer aparelho. Apple Saúde e Health Connect entram no app na Fase 2.

**Stack proposta**

- **App:** React Native com Expo e TypeScript, Rive ou Lottie para as animações do pet, armazenamento local para o modo offline.
- **API:** FastAPI (Python) com PostgreSQL e Redis, jobs com ARQ para enviar avisos e rotinas agendadas; o estado do pet é calculado na leitura a partir da data da última atividade.
- **Infra:** Docker, GitHub Actions para CI/CD, hospedagem gerenciada de baixo custo, Sentry para erros.
- **Testes:** unitários para a lógica do pet (inclusive fuso e horário de verão) e testes ponta a ponta do fluxo principal.

**Stack do backend em Python**

| Camada | Sugestão | Por quê |
| --- | --- | --- |
| API | FastAPI com Pydantic v2, rodando em Uvicorn atrás do Gunicorn | Async, validação por tipos e OpenAPI automático |
| Banco e migrações | PostgreSQL, SQLAlchemy 2.0 assíncrono e Alembic | Padrão maduro, com migrações versionadas |
| Fila e jobs | Redis com ARQ (async, com cron embutido); Celery só se a fila crescer | Avisos de push e resumo semanal; o estado do pet não depende de job |
| Autenticação | Validação de token da Apple e do Google (PyJWT e google-auth), e-mail e senha com argon2, JWT de acesso e de renovação | Cobre os três modos de cadastro |
| IA de imagem | API de um modelo de visão, com saída estruturada validada por Pydantic e Pillow para reduzir a imagem | Resposta tipada e custo menor por foto |
| Notificações | API de push do Expo chamada com httpx | Simples para começar |
| Assinaturas (Fase 2) | Camada de pagamentos com adaptador (Stripe primeiro), com webhooks por provedor | Plano validado no servidor |
| Limites de uso | Limite por usuário no Redis (slowapi ou regra própria) | Controla o custo da IA |
| Configuração | pydantic-settings | Segredos e variáveis tipados |
| Testes e qualidade | pytest, pytest-asyncio, httpx, Testcontainers, ruff e mypy | Cobre a lógica do pet, fuso e horário de verão |
| Observabilidade | Sentry, structlog e PostHog sem dados pessoais | Erros e métricas de retenção |
| Empacotamento e CI | uv, Docker e GitHub Actions | Ambiente reproduzível |
| Hospedagem | Fly.io, Railway ou Render no início, com Postgres e Redis gerenciados | Custo baixo, com caminho para AWS |
| Elo com o app | Cliente TypeScript gerado a partir do OpenAPI (openapi-typescript) | Mantém os tipos alinhados entre Python e React Native |

### Convenções de código

- **Idioma:** código, banco, API, commits, branches, README e comentários em inglês. Só os textos que o usuário vê ficam em português, em arquivos de tradução (i18n).
- **Nomes:** `snake_case` no Python e no Postgres, `camelCase` no TypeScript.
- **API:** rotas, campos JSON e mensagens de erro em inglês, com códigos de erro estáveis (como `DAILY_LIMIT_REACHED`) que o app traduz.
- **IA de imagem:** o resultado estruturado volta em inglês, com campos fixos; a descrição mostrada ao usuário é gerada no idioma dele.

### Padrão de provedores (Ports and Adapters)

Todo serviço externo que pode mudar entra por uma interface nossa (a porta), e cada provedor é um adaptador. O núcleo do sistema nunca importa o SDK de um provedor. O padrão também é conhecido como arquitetura hexagonal e se apoia na inversão de dependência.

| Porta (interface nossa) | Primeiro adaptador | Outros possíveis |
| --- | --- | --- |
| PaymentProvider | Stripe | Apple IAP, Google Play, RevenueCat, Mercado Pago |
| FoodVisionProvider (avaliação da foto) | Modelo de visão escolhido | Outro modelo ou provedor |
| PushProvider | Expo Push | FCM e APNs direto, OneSignal |
| AuthProvider (Apple, Google, e-mail) | Um adaptador por método de login | Outros logins sociais |
| StorageProvider (fotos, se guardar) | Tigris ou Cloudflare R2 | S3, Google Cloud Storage |
| EmailProvider | A definir (Resend, SES ou Postmark) | Qualquer outro |
| AnalyticsProvider | PostHog | Outro, ou adaptador nulo |
| ErrorReporter | Sentry | Outro |
| Clock e IdGenerator | Relógio e uuid do sistema | Versões fixas para teste |

**Regras**

- **Porta no domínio:** cada Protocol fica em `app/<module>/ports.py` e usa só tipos nossos, nunca tipos do SDK.
- **Adaptadores isolados:** o SDK externo só é importado dentro de `providers/`. Uma regra automática no CI (import-linter) barra imports fora dali.
- **Escolha por configuração:** uma fábrica lê `PAYMENT_PROVIDER`, `VISION_PROVIDER`, `PUSH_PROVIDER` e entrega o adaptador, injetado com Depends do FastAPI.
- **Erros e eventos traduzidos:** o adaptador converte respostas e erros do provedor para tipos nossos (ProviderUnavailable, RateLimited, InvalidInput).
- **Resultado normalizado:** a IA de imagem devolve sempre o mesmo esquema Pydantic, seja qual for o modelo.
- **Falso para teste:** cada porta tem um adaptador Fake que roda nos testes, sem rede e sem custo.
- **Provedor no dado:** registros que nascem de um provedor guardam o nome dele e a versão (como `model_version`).
- **Testes de contrato:** o mesmo conjunto de testes roda contra todos os adaptadores da mesma porta.
- **Sem exagero:** porta só para o que é externo e pode mudar; Redis e ARQ ficam fora no MVP.

**Estrutura de pastas**

- `app/payments/`: ports.py, service.py, providers/stripe.py
- `app/vision/`: ports.py, service.py, providers/
- `app/push/`: ports.py, service.py, providers/expo.py
- `app/auth/`: ports.py, service.py, providers/apple.py, google.py, password.py
- `app/storage/`: ports.py, providers/
- `app/core/`: config.py, clock.py, errors.py

### Pagamentos com Stripe

- **Interface:** PaymentProvider com create\_checkout, create\_portal\_session, cancel\_subscription e parse\_webhook. O parse\_webhook valida a assinatura e traduz o evento do provedor para eventos nossos (SubscriptionActivated, SubscriptionRenewed, SubscriptionCanceled, PaymentFailed, RefundIssued).
- **Fonte da verdade:** o serviço de assinaturas só consome eventos nossos e atualiza o banco. O app pergunta "tem premium?" e a resposta vem da tabela `subscription`, nunca do Stripe.
- **Webhooks:** rota `POST /webhooks/{provider}`, com chave secreta por provedor, processamento idempotente (por `external_event_id`) e tolerante a eventos fora de ordem. Um job do ARQ reconcilia o estado com o provedor por rotina.
- **Checkout e portal:** Stripe Checkout hospedado, sem dado de cartão no nosso sistema, e Customer Portal para cancelar e trocar o cartão.
- **Troca de provedor:** escrever outro adaptador e apontar os novos usuários para ele; os assinantes antigos ficam no provedor antigo (coluna `provider`) até renovarem. Cartões salvos não migram sozinhos.
- **Regras das lojas:** no iOS no Brasil, desde junho de 2026, é permitido oferecer pagamento alternativo ou link para a web, sempre ao lado da compra da Apple e com reembolso e suporte por nossa conta. Fora do Brasil e no Android, as regras podem ser outras e precisam ser conferidas; onde a compra da loja for obrigatória, entra um adaptador dela.
- **Antes de lançar:** conta do Stripe no Brasil (verificar se exige CNPJ), nota fiscal, política de reembolso e canal de atendimento.

### Padrão do front-end (app mobile)

- **Organização por funcionalidade:** `src/app` (rotas finas do Expo Router, sem lógica), `src/features/<name>` (pet, meal-log, auth, settings, subscription, cada uma com components, hooks, api, types e tests) e `src/shared` (ui, api, i18n, providers, lib). Uma funcionalidade não importa o interior de outra, só o `index.ts`; o CI barra o resto (eslint-plugin-boundaries).
- **Dados do servidor:** TanStack Query com hooks gerados do OpenAPI do FastAPI, incluindo atualização otimista (o pet reage na hora a uma foto).
- **Estado local:** Zustand, pequeno e por funcionalidade. Sem Redux no MVP.
- **Formulários:** React Hook Form com Zod, só para a entrada do usuário.
- **Dados sensíveis:** tokens no Expo SecureStore, nunca em armazenamento comum.
- **Ports and Adapters no app:** AnalyticsPort (PostHog), ErrorReportingPort (Sentry), PushPort (expo-notifications), CameraPort (expo-camera e expo-image-picker), AuthPort (Apple, Google e e-mail), PurchasePort (checkout web do Stripe, com a compra da loja como adaptador futuro) e StoragePort (SecureStore). Um ProvidersContext na raiz entrega os adaptadores; as telas usam hooks como `useAnalytics()`, nunca o SDK. Cada porta tem um adaptador falso para teste e Storybook.
- **Pet:** componente isolado (Lottie no MVP), controlado só por um estado vindo da API: `happy`, `tired`, `sleepy`, `fainted`.
- **Textos:** tudo o que o usuário vê passa pelo i18n (`t('pet.state.tired')`), sem string solta em componente.
- **Qualidade:** TypeScript estrito, ESLint, Prettier, Jest com React Native Testing Library, fluxos críticos com Maestro. Componentes em PascalCase, hooks em `useX`, arquivos em kebab-case, tudo em inglês.

### Design system e cores

- **Regra:** toda tela é montada com componentes do design system em `shared/ui`, e toda cor, espaçamento, raio e tamanho de texto vem de tokens semânticos (`primary`, `background`, `muted-foreground`, `border`), nunca de valor solto no componente. Isso é verificado no lint ou na revisão de PR.
- **Paleta inicial:** Índigo como cor de marca (ações e foco), Âmbar como acento pontual (destaques e avisos), neutros levemente azulados para fundo e texto. Tokens para os modos claro e escuro desde o início, com pares `-foreground` e estados `destructive`, `success` e `warning`.
- **Contraste:** WCAG AA em cada par texto/fundo (4,5:1 para texto normal, 3:1 para texto grande e componentes), medido e não estimado. Cor nunca é o único sinal: erro e sucesso também com ícone ou texto.
- **Troca de marca:** só altera os tokens; um componente que exija edição de cor foi escrito errado.
- **Decisão (biblioteca de interface):** o app usa Gluestack UI, que se apoia no NativeWind (classes do Tailwind) e traz componentes copiados para o repositório (\`shared/ui\`), no espírito do shadcn. Os tokens semânticos (\`primary\`, \`background\`, \`muted-foreground\`, \`border\`) ficam no tema do Gluestack e seguem os mesmos nomes da paleta. Os componentes do Gluestack são composição base: telas e componentes do app só usam o design system, nunca o Gluestack direto. O React Native não lê cores em OKLCH diretamente, então os valores OKLCH são convertidos para hex ou rgb na geração do tema. Se houver um painel de administração ou site em web (RF-70), ele usa shadcn/ui com Tailwind v4 e os mesmos tokens. Antes de fixar, conferir a versão atual do Gluestack, a compatibilidade com o Expo SDK e a New Architecture, e a atividade do repositório. Bibliotecas de apoio: Reanimated e Lottie (animações e pet), FlashList (listas), expo-image (imagens), lucide-react-native (ícones), @gorhom/bottom-sheet (sheets) e expo-haptics.

### Bibliotecas do app (mobile)

Lista sugerida para o MVP. As versões e a compatibilidade com o Expo SDK e a New Architecture devem ser conferidas na documentação de cada uma antes de fixar.

| Área | Biblioteca | Uso no app |
| --- | --- | --- |
| Base | Expo, React Native, TypeScript estrito | Projeto, builds com EAS |
| Navegação | Expo Router | Rotas por arquivo e deep links |
| Interface | Gluestack UI com NativeWind | Design system e tokens |
| Animação e gestos | Reanimated e Gesture Handler | Transições e gestos |
| Animação do pet | lottie-react-native | Estados do pet (happy, tired, sleepy, fainted) |
| Listas | FlashList | Histórico de refeições |
| Imagens | expo-image | Cache e carregamento |
| Ícones | lucide-react-native | Ícones do design system |
| Sheets e modais | @gorhom/bottom-sheet | Detalhe da refeição e menus |
| Área segura e telas | react-native-safe-area-context e react-native-screens | Layout em aparelhos com notch |
| Câmera e galeria | expo-camera e expo-image-picker | Foto da refeição |
| Preparo da foto | expo-image-manipulator | Reduzir e comprimir antes de enviar |
| Dados do servidor | TanStack Query | Cache, tentativas e atualização otimista |
| Cliente da API | openapi-typescript com openapi-fetch (ou orval) | Tipos e chamadas gerados do OpenAPI do FastAPI |
| Estado local | Zustand | Estado de interface por funcionalidade |
| Formulários | React Hook Form e Zod | Entrada do usuário |
| Login | expo-apple-authentication e @react-native-google-signin/google-signin | Apple e Google; e-mail e senha pela nossa API |
| Armazenamento seguro | expo-secure-store | Tokens |
| Dados locais | react-native-mmkv (se precisar de cache local rápido) | Preferências e cache simples |
| Rede | @react-native-community/netinfo | Estado offline e rede instável |
| Notificações | expo-notifications | Push e permissão |
| Pagamento | expo-web-browser | Abrir o checkout do Stripe |
| Textos e idioma | i18next, react-i18next e expo-localization | i18n (pt-BR primeiro) |
| Datas | date-fns | Formato e fuso horário |
| Retorno físico | expo-haptics | Pet reagindo à foto |
| Atualização | expo-updates (EAS Update) | Correções só de JavaScript |
| Erros e métricas | @sentry/react-native e posthog-react-native | Erros com release e funil, sem dado pessoal |
| Testes | Jest, React Native Testing Library, MSW e Maestro | Unidade, componentes, API simulada e fluxos críticos |
| Qualidade | ESLint, Prettier e eslint-plugin-boundaries | Estilo e fronteiras entre funcionalidades |

### Método e checklists de qualidade (FE, BE, CI/CD, mobile)

Adaptado do checklist de @greco\_dev (X, 24/11/2026). A ideia é investigar antes de codar, subir a escada do mais barato ao mais caro, diagnosticar pelo sintoma, garantir cobertura e só então rodar em volume.

**O método em 6 passos**

1. **Antes de codar (5 min):** entender o problema e o que já existe (contrato da API, componente, endpoint ou job reaproveitável).
2. **A escada:** começar pela solução mais simples e barata e só subir de degrau quando o anterior falhar (front: componente existente, estado local, estado compartilhado, cache de dados, biblioteca nova; back: SQL ou índice, cache, fila, réplica, novo serviço).
3. **Quando quebra:** diagnosticar pelo sintoma (status, log, métrica) em vez de chutar.
4. **Cobertura:** casos de borda e estados (vazio, erro, limite, offline, permissão negada).
5. **Entrega:** formato seguro, reprodutível e sem segredos no código.
6. **Antes de rodar em volume:** teste pequeno, limites, timeouts e plano de rollback.

**Front-end (mobile) antes de codar:** ler o contrato OpenAPI; definir os estados da tela (carregando, vazio, erro, sucesso, parcial); desenhar offline e rede ininstável desde o início; listar permissões (câmera, notificações) com o texto de justificativa; definir a versão mínima do app (o backend aceita versões antigas por meses).

**Front-end (mobile) cobertura e entrega:** testar em aparelhos reais (iPhone antigo e atual, Android de entrada e de topo); permissão negada, revogada e “só desta vez”; app em segundo plano e retomada; push com o app aberto, fechado e em segundo plano; acessibilidade (VoiceOver, TalkBack, fonte grande, contraste); nenhum segredo no bundle (tudo que vai no app pode ser extraído); tokens no Keychain e Keystore; rótulos de privacidade da Apple e Data Safety do Google atualizados; atualização OTA só para JavaScript e assets.

**Front-end (mobile) antes de ir para produção:** TestFlight e teste interno do Play; lançamento em etapas com acompanhamento do crash-free rate; aviso ou atualização forçada para versões antigas quando a API mudar de forma incompatível; feature flags remotas; versão anterior pronta para rollback com o backend compatível.

**Back-end:** contrato e códigos de erro combinados com o app; idempotência em POST, PUT e jobs reexecutados (webhooks inclusos); paginação com ordenação estável; migrações reversíveis e compatíveis com a versão anterior; segredos em cofre; logs estruturados com trace id e sem dado pessoal; métricas e alertas (latência, taxa de erro, gasto com IA); timeout e limite de tentativas em toda chamada externa (IA, Stripe, push); teste de carga no caminho crítico (envio de foto); leitura de sintoma por código (400 e 422 validação, 401 e 403 token ou permissão, 429 backoff com jitter, 500 stack trace e trace id, 504 consulta lenta ou pool esgotado).

**CI/CD:** rodar primeiro o que falha rápido e custa pouco (lint e tipos, testes unitários, integração, e2e só nos fluxos críticos); pipeline em todo PR e na branch principal; artefato imutável que vai do staging para produção; OIDC no lugar de segredos de longa duração; actions de terceiros fixadas por SHA e imagens base por digest; GITHUB\_TOKEN somente leitura por padrão; varredura de dependências e de segredos; assinatura de build e certificados no cofre do CI; smoke test e alertas após o deploy; rollback testado; um deploy por vez por ambiente.

**Pontos de plataforma a confirmar na documentação oficial antes de fixar** (as versões e os prazos mudam rápido): versão atual do Expo SDK e do React Native, com a New Architecture obrigatória nas versões recentes; Xcode e SDK do iOS exigidos pela App Store; API alvo do Android e versão mínima da Billing Library no Google Play (se houver compra pela loja); suporte a páginas de 16 KB em bibliotecas nativas; FastAPI com Pydantic v2.

### Backend em detalhe

&#91;embedded content: backend do MVP · API, banco, fila, worker e serviços externos\]

O app fala só com a API. A API guarda os dados no PostgreSQL, usa o Redis como cache e fila, chama o serviço de IA para validar treinos e entrega o que roda em segundo plano ao worker, que recalcula o estado do pet e agenda os avisos. A assinatura chega por webhook na Fase 2. Analytics e rastreio de erros ficam fora do desenho para ele ficar legível.

## Modelo de dados

Modelo do MVP de alimentação, com nomes em inglês. Não existe peso, altura, calorias contadas, nota da refeição nem ranking de corpo, de propósito. O estado do pet (animado, cansado, sonolento, desmaiado) não é gravado: é calculado a partir de `last_activity_at` e `rest_until`.

&#91;embedded content: modelo de dados do MVP · 9 entidades, 2 na Fase 2\]

O usuário é o centro: pet, refeições, consentimentos, tokens de push e uso diário saem dele, e os pontos ligam o pet à refeição que os gerou. Assinatura e eventos de pagamento entram na Fase 2.

| Entidade | Campos principais | Observação |
| --- | --- | --- |
| user | id, auth\_provider, email, password\_hash, timezone, adult\_confirmed\_at, created\_at, deleted\_at | password\_hash só no login por e-mail (argon2) |
| pet | id, user\_id, name, skin, last\_activity\_at, rest\_until, points, streak | Um pet por usuário no MVP |
| meal\_log | id, user\_id, logged\_at, status, ai\_result (JSON), photo\_ref, model\_version, provider | photo\_ref fica vazio se a foto for apagada após a avaliação |
| points\_event | id, pet\_id, meal\_log\_id, reason, points, created\_at | Só valores positivos |
| consent | id, user\_id, document, version, accepted\_at | Prova de aceite para a LGPD |
| push\_token | id, user\_id, token, platform |  |
| daily\_usage | user\_id, day, ai\_photos | Controla o limite diário de fotos com IA |
| subscription (Fase 2) | user\_id, plan, status, expires\_at, provider, external\_customer\_id, external\_subscription\_id | Campos neutros, sem nome de provedor |
| payment\_event (Fase 2) | id, provider, external\_event\_id (único), type, received\_at, payload | Idempotência, auditoria e reprocessamento |

**Direitos do usuário:** exportar e excluir os dados mexe em todas essas tabelas. Na exclusão, apagar conta, pet, refeições, pontos, tokens e consentimentos, ou anonimizar o que precisar ser mantido por obrigação legal.

**Fases seguintes:** treinos e pausas (Fase 2), itens e pets customizados (Fase 2), arena, grupos e ligas (Fase 3).

## Deploy e operação

A ideia é usar plataformas gerenciadas, com tudo em contêiner Docker e deploy automático pelo GitHub. AWS ou GCP só entram se o custo, a conformidade ou a escala pedirem. Os preços e as regiões das plataformas mudam, então confira a tabela atual antes de contratar.

**Onde cada parte roda**

| Parte | Onde | Observação |
| --- | --- | --- |
| API em FastAPI | Fly.io, região de São Paulo (gru) | Gunicorn com workers Uvicorn; HTTPS e balanceamento pelo Fly |
| Worker do ARQ | Fly.io, mesma imagem Docker | Outro comando de início, como segundo grupo de processos |
| PostgreSQL | Postgres gerenciado do Fly.io (ou Neon/Supabase) | Backups ligados desde o início e restauração testada antes do lançamento |
| Redis | Upstash Redis integrado ao Fly | Fila do ARQ e limites de uso; o Fly não tem Redis gerenciado próprio |
| Fotos | Não guardar após a avaliação; se guardar, Tigris ou Cloudflare R2 | Bucket privado, URL assinada e prazo de expiração |
| Borda (opcional) | Cloudflare: DNS, WAF e Turnstile | Protege o cadastro contra contas falsas e controla o custo da IA |
| App mobile | Expo EAS (Build, Submit e Update) | Builds na nuvem, envio às lojas e correções só de JavaScript |

**Como o deploy funciona**

- **Contêiner:** Dockerfile com uv; a API e o worker usam a mesma imagem.
- **Ambientes:** staging e produção, cada um com seu banco, seu Redis e suas chaves. O staging usa a menor máquina possível.
- **Pipeline (GitHub Actions):** a cada push roda ruff, mypy e pytest. Ao entrar na branch principal, faz deploy no staging; a produção sai com aprovação manual ou tag.
- **Migrações:** o Alembic roda no release\_command do Fly, antes de a nova versão entrar, e as mudanças de banco devem ser compatíveis com a versão anterior.
- **Segredos:** guardados com fly secrets e lidos pelo pydantic-settings, nunca no repositório.
- **Operação:** health check na API, Sentry para erros, alerta de gasto na conta da IA e limite diário de fotos por usuário.
- **Estado do pet:** calculado na leitura a partir da data da última atividade; os jobs do ARQ ficam só para avisos de push e resumo semanal.

**App mobile: do código à loja**

- **Desenvolvimento:** React Native com Expo, TypeScript e Expo Router; development build quando precisar de módulos nativos (compras no app, por exemplo).
- **Perfis de build:** development, preview (beta fechado) e production, cada um apontando para a API correta por variável de ambiente.
- **Envio às lojas:** EAS Submit para o TestFlight e para o teste interno do Google Play; EAS Update para correções sem nova revisão.
- **Contas:** Apple Developer (cerca de US$ 99 por ano) e Google Play Console (taxa única de cerca de US$ 25).
- **Regras das lojas:** login com Apple obrigatório quando há outros logins sociais, classificação etária 18+ com o sinal de idade das lojas (RF-02) e declarações de privacidade preenchidas (Apple Privacy Nutrition Labels e Data Safety do Google), por causa das fotos de comida e dos dados de saúde.
- **Cliente da API:** TypeScript gerado a partir do OpenAPI do FastAPI, para manter os tipos alinhados.

**Quando rever essa escolha:** se a conta da plataforma pesar, se houver exigência de conformidade ou se a escala pedir, a migração para AWS ou GCP é trabalhosa, mas não exige reescrever nada, porque tudo roda em Docker.

## Telas e fluxos

**Canvas com as telas:** [Papeto: telas do app](https://claude.ai/artifact/1kwmN9FBtScfqXR6yRmJ2N). A página Layout tem as 42 telas em alta fidelidade, com protótipo navegável pelo botão Play. A página Fluxo liga as telas por setas, e a página Wireframe guarda a versão em skeleton. Onde a tabela abaixo e o canvas diferirem, vale o canvas.

O app tem 42 telas no canvas, numeradas de 1 a 43 (o número 29 não é usado). As de 38 a 43 são estados e passos que entraram na validação de fluxo de 25/11. A numeração é a mesma do canvas.

| # | Tela | O que mostra | Plano e fase |
| --- | --- | --- | --- |
| 1 | Entrar | Logo do Papeto, login com Apple, Google ou e-mail | Grátis, MVP |
| 21 | Entrar com e-mail | E-mail, senha, “Esqueci minha senha” e “Criar conta” | Grátis, MVP |
| 22 | Criar conta | Nome, e-mail e senha com requisitos; sem peso, altura ou calorias | Grátis, MVP |
| 23 | Recuperar senha | Envio do link, sem confirmar se o e-mail existe | Grátis, MVP |
| 2 | Idade e consentimento | 18+, termos e privacidade, resumo do uso dos dados; Continuar só com as duas caixas marcadas | Grátis, MVP |
| 43 | Dê um nome ao pet | Nome antes de mostrar o pet (que fica escondido), até 20 letras, 3 sugestões | Grátis, MVP |
| 24 | Conheça o pet | Revelação do pet já com o nome e escolha da cor | Grátis, MVP |
| 30 | Como funcionam as vidas | As 3 regras das vidas, último passo do onboarding | Grátis, MVP |
| 3 | Início com o pet | Pet, estado, vidas (corações), sequência, última refeição, “Registrar refeição” e fotos restantes | Grátis, MVP |
| 40 | Início com as fotos do dia usadas | 2 de 2 fotos; Registrar leva ao Limite diário | Grátis, MVP |
| 9 | Permissão da câmera | Motivo antes do pedido do sistema, só no primeiro uso; galeria como alternativa | Grátis, MVP |
| 4 | Câmera | Guia para enquadrar o prato, galeria, flash e trocar câmera | Grátis, MVP |
| 5 | Analisando | Skeleton do resultado enquanto a IA responde; Cancelar volta à câmera | Grátis, MVP |
| 6 | Resultado | Descrição, itens, pontos, accordion “Sobre este prato”; salva sozinho, com Corrigir e Pronto | Grátis, MVP |
| 31 | Permitir avisos | Pedido de avisos depois da primeira refeição, com “Agora não” | Grátis, MVP |
| 10 | Erro na análise | Dicas de foto, nova tentativa, galeria e fila offline | Grátis, MVP |
| 11 | Limite diário | 2 de 2 fotos com IA; o pet não perde vida por isso | Grátis, MVP |
| 26 | Corrigir refeição | Tipo da refeição, remover e adicionar itens; pontos não mudam | Grátis, MVP |
| 7 | Histórico | Filtros por período, cards de refeição, botão de câmera | Grátis, MVP |
| 14 | Histórico vazio | Uma frase e um único botão para registrar | Grátis, MVP |
| 25 | Detalhe da refeição | Foto apagada, descrição, itens, horário, pontos, accordion, Corrigir e Apagar | Grátis, MVP |
| 37 | Apagar refeição | Confirmação com Apagar e Manter | Grátis, MVP |
| 42 | Histórico depois de apagar | Aviso “Refeição apagada” com Desfazer | Grátis, MVP |
| 28 | Perdeu uma vida | Vidas restantes, registrar agora ou pausar | Grátis, MVP (pausa premium) |
| 12 | Pet desmaiado | Sem vidas; pontos e histórico mantidos; acorda com 1 vida ao registrar | Grátis, MVP |
| 8 | Perfil | Plano, avisos, pausa, fuso, exportar e excluir dados, sair | Grátis, MVP |
| 27 | Avisos do pet | Exemplos de aviso, lembretes, resumo semanal, não incomodar; no máximo 2 por dia | Grátis, MVP |
| 36 | Exportar dados | O que vem no arquivo e envio por e-mail | Grátis, MVP |
| 35 | Excluir conta | O que se perde, 30 dias para desistir, atalho para exportar; botão só libera após confirmar | Grátis, MVP |
| 41 | Conta excluída | Confirmação, 30 dias para desistir, assinatura cancelada | Grátis, MVP |
| 15 | Assinar (overlay) | Benefícios, plano anual ou mensal, checkout pelo Stripe, restaurar assinatura, “Agora não” | Premium, Fase 2 |
| 16 | Premium ativo | Confirmação, o que foi liberado e “Ir para o início” | Premium, Fase 2 |
| 38 | Início (assinante) | Início com a pausa liberada e o Perfil de assinante | Premium, Fase 2 |
| 32 | Resultado (assinante) | “Seus hábitos” liberado | Premium, Fase 2 |
| 33 | Perfil (assinante) | Plano ativo e acesso a Sua assinatura | Premium, Fase 2 |
| 34 | Sua assinatura | Trocar plano, atualizar cartão, recibos e cancelar | Premium, Fase 2 |
| 13 | Pausar o pet | 1, 3 ou 7 dias; não perde vidas e guarda a sequência | Premium, Fase 2 |
| 39 | Início com o pet pausado | Pet dormindo, até quando vai a pausa e “Retomar agora” | Premium, Fase 2 |
| 17 | Painel da constância | Dias com registro, refeições, variedade, maior sequência, calendário e dias da semana | Premium, Fase 2 |
| 18 | Pets e visuais | Troca de pet e acessórios, mantendo pontos e histórico | Premium, Fase 2 |
| 19 | Evolução | Estágios do pet por treinos de força e resistência | Premium, Fase 2 |
| 20 | Arena | Liga semanal por porcentagem da própria meta; premium sem vantagem | Premium, Fase 3 |

**Accordion “Sobre este prato” na tela 6 (Resultado):** começa aberto e pode ser recolhido. A parte grátis mostra os grupos presentes (verduras, proteína, grãos, leguminosas, frutas, laticínios), a quantidade de itens, as cores e a confiança da leitura da IA. A parte premium, “Na sua semana”, compara com os registros da própria pessoa (por exemplo “3ª refeição com salada”, “almoço no seu horário de costume”) e aparece desfocada no grátis, com atalho para a assinatura. Segue as salvaguardas: sem calorias, macros, peso ou nota, e o que falta no prato aparece neutro. A saída estruturada da IA ganha os campos `food_groups`, `item_count`, `colors` e `confidence`.

**Parte premium do accordion, “Seus hábitos”:**

| Métrica | O que mostra | No grátis |
| --- | --- | --- |
| Como o prato se divide | Gráfico de rosca com a área aproximada de cada grupo no prato (estimativa visual, não quantidade) | Desfocado |
| Grupos nesta semana | Em quais dias da semana cada grupo apareceu (verduras, frutas, leguminosas, proteína) | Desfocado |
| Descobertas | Alimentos novos no prato e quantos alimentos diferentes no mês | Desfocado |
| Dica do Bolinha | Uma sugestão gentil que sempre acrescenta (“que tal uma fruta no lanche?”), nunca corta ou proíbe | Desfocado |
| Na sua semana | Comparações com os próprios registros (salada, horário de costume) | Desfocado |

No grátis, toda a seção “Seus hábitos” fica bloqueada e desfocada, com o botão “Desbloquear seus hábitos”, que abre a assinatura. Nenhuma métrica mostra calorias, macros, peso ou nota. A IA passa a devolver também `plate_share` (fração estimada da área por grupo) e `new_foods`; a dica vem de uma lista de frases aprovadas, não de texto livre.

### Mapa do app

O fluxo completo, com setas tela a tela, está na [página Fluxo do canvas](https://claude.ai/artifact/1kwmN9FBtScfqXR6yRmJ2N#page-fluxo). Ele é dividido em 6 fluxos, e o Início liga todos.

&#91;embedded content: mapa do app · 6 fluxos ligados pelo Início\]

1. **Primeiro acesso:** Entrar → Idade e termos → Dê um nome (o pet fica escondido) → Conheça o pet (revelação e cor) → Como funcionam as vidas → Início. Pelo e-mail, quem já tem conta vai direto ao Início.
2. **Registrar uma refeição:** Início → Permissão da câmera (só no primeiro uso) → Câmera → Analisando → Resultado → Permitir avisos (só na primeira refeição) → Início. Cancelar volta à câmera; uma falha da IA leva ao Erro; com 2 de 2 fotos usadas, a câmera leva ao Limite.
3. **Histórico:** lista → detalhe → apagar → lista com Desfazer. Sem refeições, mostra o Histórico vazio.
4. **Perfil e conta:** avisos, exportar dados e excluir conta. Excluir só libera depois da confirmação e termina na tela de conta excluída.
5. **Premium:** Assinar → Premium ativo → Início do assinante → Pausar → Início pausado → Retomar. Entra pelo Resultado (Seus hábitos), pelo Limite, pela pausa e pelo Perfil; "Agora não" volta ao Início.
6. **Vidas do pet:** ao abrir o app depois de um dia sem registro, aparece Perdeu uma vida; sem vidas, Desmaiado; uma refeição acorda o pet.

### Fluxo: registrar uma refeição

&#91;embedded content: fluxo de registrar uma refeição · decisões e caminhos\]

Toda foto lida vira registro e conta o dia para vidas e sequência. Uma foto que a IA não lê leva à tela de erro com dicas, e o limite diário de fotos nunca custa uma vida.

## Métricas, funil e monetização

A métrica central é quantos usuários voltam a treinar depois de um desmaio, porque mostra se o pet segura as pessoas sem puni-las.

| Métrica | O que mede | Como medir |
| --- | --- | --- |
| Ativação | Quem cria o pet e registra o primeiro treino no primeiro dia | Eventos de cadastro, criação do pet e primeiro treino |
| Retenção D7 e D30 | Quem volta após 7 e 30 dias | Eventos de abertura e de treino |
| Constância semanal | Treinos por semana em relação à meta do próprio usuário | Treinos e metas |
| Retorno pós-desmaio | Quem registra treino em até 7 dias depois de desmaiar | Estado do pet e treinos |
| Desinstalação após notificação | Se os avisos estão afastando as pessoas | Notificações enviadas e desinstalações |
| Compartilhamento | Cartões gerados e abertos | Eventos de compartilhar |
| Conversão para assinatura (Fase 2) | Quem assina | Stripe (via adaptador de pagamentos) |

**Funil de aquisição:** instalação, cadastro, pet criado, primeiro treino, segunda semana ativa, compartilhamento. Cada etapa tem um evento nomeado e uma parcela de usuários que o painel mostra. Os valores esperados são definidos depois do primeiro grupo de testadores.

**Crescimento:** cartão do pet compartilhável nas redes, convite por código, página de destino simples e conteúdo curto mostrando o pet desmaiando e voltando.

**Monetização (Fase 2):** o app básico é gratuito. A assinatura libera itens, cenários, espécies, extras do pet, evolução por força e resistência, arena de pets e módulo de alimentação. A divisão completa está na seção Free e premium. O preço será definido depois, a partir do custo real de operação (IA, infraestrutura e taxas das lojas) medido no beta. Não há venda de dados, e a assinatura não é necessária para manter o pet vivo.

## Página nas lojas

Rascunho da página na App Store e no Google Play. Os limites de caracteres estão entre parênteses; confira os limites atuais em cada loja antes de publicar.

| Campo | Português | English |
| --- | --- | --- |
| Nome (30) | Papeto: pet da constância | Papeto: consistency pet |
| Subtítulo, App Store (30) | Foto da refeição, pet feliz | Snap your meal, happy pet |
| Descrição curta, Google Play (80) | Fotografe suas refeições e cuide de um pet que vive da sua constância. | Photograph your meals and care for a pet that lives on your consistency. |
| Texto promocional (170) | Conheça o Bolinha: ele fica animado a cada refeição que você registra. Sem contar calorias, sem notas, só constância. | Meet Bolinha: he lights up with every meal you log. No calorie counting, no scores, just consistency. |
| Palavras-chave, App Store (100) | pet virtual,hábito,refeição,foto de comida,constância,diário alimentar,bichinho,rotina,lembrete | virtual pet,habit,meal log,food photo,streak,food diary,cute pet,routine,reminder |
| Categoria | Estilo de vida (secundária: Saúde e fitness) | Lifestyle (secondary: Health & Fitness) |
| Classificação etária | 18+ | 18+ |

**Descrição longa (PT)**

O Papeto transforma o hábito de registrar refeições em um cuidado divertido. Tire uma foto do prato e veja o Bolinha, seu pet, ficar animado.

- Registre em segundos: a IA descreve o prato para você, sem contar calorias e sem dar notas.
- Cuide do seu pet: ele tem vidas, humor e sequência. Um dia sem registro custa uma vida, mas nada se perde: uma refeição acorda ele.
- Veja o que tem no prato: grupos de alimentos, variedade e cores.
- Premium: pausa sem perder vidas, seus hábitos da semana, mais fotos por dia e novos pets.

As fotos são apagadas logo após a avaliação. Você exporta ou exclui seus dados quando quiser. O Papeto não é um app de dieta e não substitui orientação profissional.

**Capturas de tela (6, na ordem):** 1 Início com o pet (“Seu pet vive da sua constância”), 4 Câmera (“Fotografe a refeição”), 6 Resultado (“Registro em segundos, sem calorias”), 30 Vidas (“Cuide das vidas do Bolinha”), 12 Pet desmaiado (“Nada se perde, ele só desmaia”), 15 Premium (“Pausa, hábitos e novos pets”). O vídeo de 26 s serve de prévia do app.

**Antes de enviar:** declarações de privacidade (Apple Privacy Labels e Data Safety do Google), link da Política de Privacidade e dos Termos, e conta de teste para a revisão. Evitar promessas de saúde ou emagrecimento no texto, que travam a aprovação e contrariam o posicionamento.

## Riscos, conformidade e cuidados de saúde

O maior risco do produto é transformar um jogo de constância em fonte de pressão. Por isso as regras de bem-estar fazem parte dos requisitos, não de um texto de marketing.

| Risco | Impacto | Mitigação |
| --- | --- | --- |
| Pet vira fonte de culpa ou de exercício compulsivo | Dano ao usuário e avaliações ruins | Sem morte, desmaio reversível, descanso e pausa, sem ranking de volume ou corpo, avisos limitados |
| Treinar machucado para não perder a sequência | Lesão | Modo pausa fácil, mensagem de descanso, pausa sugerida ao relatar lesão |
| Dados de saúde sensíveis (LGPD) | Sanções e perda de confiança | Consentimento específico, coleta mínima, nenhum repasse a terceiros, exclusão no app |
| Menores de idade usando o app | Risco legal e de bem-estar | Idade mínima 18, sinal de idade da loja, verificação no cadastro, classificação etária adequada nas lojas e revisão jurídica antes do lançamento (ECA Digital) |
| Módulo de comida (fase posterior) estimula restrição | Dano ao usuário | Desligado por padrão, sem meta de calorias, números ocultos, detecção de padrão de risco e caminho de apoio |
| Estimativa de IA errada | Perda de confiança | Marcar como aproximada, pedir confirmação, permitir correção |
| Reprovação nas lojas | Atraso de lançamento | Política de privacidade, declaração de dados e aviso de que não substitui profissional |
| Retenção baixa depois da novidade | Produto não se sustenta | Medir retorno pós-desmaio cedo e testar com 10 a 20 pessoas antes de investir em IA |
| Custo de IA acima do esperado | Prejuízo | Limite diário, redução de imagem, cache, plano pago para uso intenso |
| Cópia de personagem ou identidade de terceiros | Risco legal | Arte e nome originais, sem referência a marcas existentes |
| Complexidade de integrações de saúde | Atraso | Deixar para a Fase 2 e entregar o MVP com registro manual |
| Validação por IA recusa treino real ou aceita qualquer imagem | Frustração do usuário ou perda do sentido do jogo | Confirmação do usuário, fallback manual, taxa de erro medida no beta e foco em constância, não em fiscalização |
| Arquivos enviados expõem rosto, local ou outras pessoas | Privacidade e LGPD | Descartar após a análise, não guardar a imagem, avisar antes do envio e não extrair dados além do treino |

**Aviso no app:** o aplicativo oferece orientação geral de constância e não substitui médico, nutricionista ou educador físico. Antes de começar atividade física, em caso de dor, doença ou dúvida, o usuário deve procurar um profissional.

## Plano por fases

&#91;embedded content: plano em 3 fases · 12 semanas, 2 gates\]

As fases estão em blocos iguais, não em escala. Os losangos são as decisões: só se passa para a fase seguinte se o critério do gate for atendido.

| Fase | Pronto quando | Requisitos principais |
| --- | --- | --- |
| Fase 1: MVP do pet com alimentação | O ciclo completo (criar, registrar refeição por foto, evoluir, desmaiar, voltar) funciona em Android e iOS com 10 a 20 testadores, a avaliação por IA identifica refeições reais dos testadores e o retorno depois do desmaio está medido | RF-01 a RF-04, RF-10 a RF-13, RF-90 a RF-98, RF-30, RF-31, RF-40 a RF-42, RF-70 |
| Fase 2: treino, saúde e lojas | O registro de treino funciona (manual, por prova com IA e pelo Apple Saúde e Health Connect), a assinatura funciona e o app passa na revisão das lojas | RF-05, RF-14, RF-16, RF-20 a RF-23, RF-26 a RF-28, RF-24, RF-32, RF-50, RF-51, RF-71, RF-64, RF-65, RF-72 a RF-74, RF-80 a RF-83 |
| Fase 3: arena e grupos | A arena e os grupos funcionam com ligas por nível e sem comparar peso, calorias ou volume de treino | RF-52, RF-53 |
