# CONTEXT_RULES — Regras de governança para agentes de IA

Este arquivo é entregue ao assistente de IA **antes** de qualquer geração de código, junto com [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md) (v1.1). Se as regras e a spec conflitarem, a spec vence e o conflito deve ser apontado ao humano.

## 1. Diretrizes arquiteturais (o que FAZER)

- **DA-01:** Usar Python 3.11+.
- **DA-02:** Type hints em 100% dos parâmetros e retornos.
- **DA-03:** Seguir a PEP-8 e o *Single Responsibility Principle* (SRP).
- **DA-04:** Docstrings no estilo Google (`Args`, `Returns`, `Raises`).
- **DA-05:** Funções puras, pequenas (meta: menos de 20 linhas úteis) e coesas.
- **DA-06:** Logs com a biblioteca padrão `logging`. `print` é proibido.
- **DA-07:** Lançar apenas as exceções do contrato (`TaskAnalyzerError`, `TaskValidationError`), com mensagens que digam o id da tarefa e o motivo.
- **DA-08:** Impedir divisão por zero com verificação explícita, nunca com `try/except ZeroDivisionError`.

## 2. Proibições explícitas (o que NÃO FAZER)

- **PR-01:** Nenhuma biblioteca de terceiros além de `pytest`/`pytest-cov`, e só nos testes.
- **PR-02:** Proibido ignorar ou silenciar exceções (ex.: `except Exception: pass`).
- **PR-03:** Proibido alterar a assinatura pública ou inventar campos no retorno.
- **PR-04:** Proibido acoplar a lógica de negócio a rede, disco ou relógio do sistema (`datetime.now()`, `time.time()`).
- **PR-05:** Proibido entregar código parcial ou sem a cobertura de testes exigida (≥ 90%).
- **PR-06:** Proibido alterar a especificação ou os testes para fazer o código passar. Se um teste parecer errado, pergunte ao humano.

## 3. Protocolo de interação

1. O agente recebe este arquivo e a spec antes de gerar código.
2. Diante de lacuna ou ambiguidade, o agente **pergunta**. Nunca inventa comportamento.
3. Todo código gerado passa por auditoria linha a linha do responsável humano antes do merge.
4. O PR registra o que a IA gerou e o que precisou de intervenção humana.
