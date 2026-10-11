# Spider Desk 🕷️

Mesa de trading multi-agente para tokens na rede Solana, com uma sala de jogo animada (a partir da Fase 4).
**Roda sempre em MODO PAPEL**: usa dados reais quando disponíveis, mas nenhuma ordem real é enviada.

> Isto é uma ferramenta de estudo e disciplina. Memecoins são extremamente arriscadas e a maioria
> perde valor. Nada aqui é recomendação de investimento nem promessa de resultado.

## Status: Fase 1 (Fundação)

| Componente | Estado |
|---|---|
| `config.yaml` validado (pydantic, `extra=forbid`) | ✅ |
| SQLite (eventos + snapshots, leitura sem lookahead) | ✅ |
| EventBus (assinantes + filas para WebSocket) | ✅ |
| CRAWLER: DexScreener + RPC Solana + Jupiter | ✅ adapter real · mock automático se a API cair |
| GATE: 11 regras + blocklist, dado ausente = reprova | ✅ |
| Adapter Jev (OpenRouter Decisions) + mock | ✅ (usado pelos agentes SCAN/VET na Fase 2) |

## Instalação

```bash
cd spider-desk
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # preencha OPENROUTER_API_KEY (Jev)
```

## Como rodar

```bash
python -m backend.run cycle              # 1 ciclo CRAWLER → GATE (dados reais; cai para mock se a API falhar)
python -m backend.run cycle --mock       # força dados falsos
python -m backend.run cycle --cycles 10  # 10 ciclos, a cada crawl.interval_s
python -m backend.run jev-check          # 1 chamada real ao Jev para validar a chave
python -m pytest -q                      # testes
```

## Ordem do GATE

O GATE roda em duas etapas para não gastar chamadas à toa:
1. **Mercado** (dados do DexScreener, grátis): idade, liquidez, volume, mcap, trades.
2. **On-chain** (só para quem passou): autoridades de mint/freeze (RPC), concentração por dono
   (excluindo pool e burn, ver `gate.excluded_owners`) e cotação de **venda** na Jupiter no tamanho
   máximo do ticket (detecta honeypot e impacto alto).

Cada regra gera um `RuleCheck` (✓/✗, valor e limiar) dentro do evento — é isso que vai acender o
painel `thresholds` na sala do jogo.

## Segurança

- Segredos só no `.env` (no `.gitignore`), carregados como `SecretStr` — nunca aparecem em log, banco ou evento.
- `mode: live` é recusado na inicialização até a Fase 7.
- Nome e descrição de tokens são **dados não confiáveis** (nunca entram como instrução em prompts).
