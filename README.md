# sdd-task-analyzer

[![CI](https://github.com/fernando-brum/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fernando-brum/sdd-task-analyzer/actions/workflows/ci.yml)

Motor de análise de produtividade (**TaskAnalyzer**) desenvolvido com *Spec-Driven Development* (SDD): o código é gerado por um assistente de IA a partir de uma especificação contratual e de regras de contexto, e depois homologado por um humano.

## Estrutura

```text
sdd-task-analyzer/
├── .github/
│   └── workflows/
│       └── ci.yml             # Pipeline de CI (GitHub Actions)
├── Dockerfile                 # Imagem python:3.11-slim que roda o Test Harness
├── docker-compose.yml         # Serviço "tests": a suíte em um único comando
├── .dockerignore              # Só src/, tests/, pytest.ini e requirements.txt entram na imagem
├── README.md                  # Este arquivo
├── CONTEXT_RULES.md           # Regras de governança para a IA
├── requirements.txt           # Dependências autorizadas (pytest, pytest-cov)
├── pytest.ini                 # Configuração do pytest e da cobertura mínima (90%)
├── .gitignore
├── specs/
│   ├── task_analyzer_spec.md  # Contrato SDD (v1.2), fonte da verdade
│   ├── requirements.yaml      # Rastreabilidade: requisito, regra e cenário → teste
│   └── system_design_document.pdf  # A spec em PDF, gerada a partir do .md
├── tests/
│   └── test_harness.py        # Test Harness (pytest)
└── src/
    └── task_analyzer.py       # Implementação gerada via IA e homologada
```

## Como executar

Requer Python 3.11 ou superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

O `pytest.ini` já ativa o relatório de cobertura e falha a execução se ela ficar abaixo de 90%.

## Execução com Docker

Não exige Python instalado, só o Docker. A imagem usa `python:3.11-slim`, roda como usuário não-root e executa `pytest tests/test_harness.py -v`.

```bash
docker build -t sdd-task-analyzer:1.2 .
docker run --rm sdd-task-analyzer:1.2
```

Ou, com o Docker Compose, em um único comando (`--build` garante a imagem atualizada):

```bash
docker compose run --rm --build tests
```

## Integração contínua

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda a cada push e Pull Request nas branches `main` e `develop`: em `ubuntu-latest` com Python 3.11, instala o `requirements.txt` e executa `pytest tests/test_harness.py -v`. O resultado aparece na aba [Actions](https://github.com/fernando-brum/sdd-task-analyzer/actions) e no badge acima.

## Exemplo de uso

```python
from datetime import datetime, timezone
from task_analyzer import Tarefa, analyze_tasks

utc = timezone.utc
tarefa = Tarefa(
    id_tarefa=1,
    titulo="Revisar PR",
    prioridade="alta",
    status="concluida",
    data_criacao=datetime(2026, 1, 10, 8, 0, tzinfo=utc),
    prazo=datetime(2026, 1, 10, 18, 0, tzinfo=utc),
    data_inicio=datetime(2026, 1, 10, 9, 0, tzinfo=utc),
    data_conclusao=datetime(2026, 1, 10, 11, 0, tzinfo=utc),
)
relatorio = analyze_tasks([tarefa])
relatorio.tempo_medio_conclusao_horas  # 2.0
```

## Fluxo de trabalho

- `feature/*`: uma branch por entrega, criada a partir da `develop`.
- `develop`: integração das features, por Pull Request.
- `main`: versão homologada; recebe apenas Pull Requests vindos da `develop`.
- Todo merge passa por Pull Request com os critérios da seção 5.4 da [spec](specs/task_analyzer_spec.md): testes verdes, check verde do GitHub Actions, cobertura ≥ 90%, aderência às [CONTEXT_RULES](CONTEXT_RULES.md) e registro do que a IA gerou e do que foi corrigido pelo humano.
