# sdd-task-analyzer

Motor de análise de produtividade (**TaskAnalyzer**) desenvolvido com *Spec-Driven Development* (SDD): o código é gerado por um assistente de IA a partir de uma especificação contratual e de regras de contexto, e depois homologado por um humano.

## Estrutura

```text
sdd-task-analyzer/
├── README.md                  # Este arquivo
├── CONTEXT_RULES.md           # Regras de governança para a IA
├── requirements.txt           # Dependências autorizadas (pytest, pytest-cov)
├── pytest.ini                 # Configuração do pytest e da cobertura mínima (90%)
├── .gitignore
├── specs/
│   └── task_analyzer_spec.md  # Contrato SDD (v1.1), fonte da verdade
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

- `main`: versão homologada.
- `feature/*`: uma branch por entrega (`feature/sdd-specification`, `feature/test-harness`, `feature/task-analyzer-impl`).
- Todo merge na `main` passa por Pull Request com os critérios da seção 5 da [spec](specs/task_analyzer_spec.md): testes verdes, cobertura ≥ 90%, aderência às [CONTEXT_RULES](CONTEXT_RULES.md) e registro do que a IA gerou e do que foi corrigido pelo humano.
