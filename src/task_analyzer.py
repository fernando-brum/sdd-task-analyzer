"""Motor de análise de produtividade (TaskAnalyzer).

Implementa o contrato de specs/task_analyzer_spec.md (v1.1). O módulo opera
apenas em memória e não depende de rede, disco ou relógio do sistema.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

logger = logging.getLogger(__name__)

PRIORIDADES: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: frozenset[str] = frozenset(
    {"pendente", "concluida", "cancelada"}
)
TAMANHO_MAXIMO_TITULO = 200
SEGUNDOS_POR_HORA = 3600
CASAS_DECIMAIS = 2


class TaskAnalyzerError(Exception):
    """Base de todas as exceções do TaskAnalyzer."""


class TaskValidationError(TaskAnalyzerError):
    """Uma tarefa da entrada viola o contrato de entrada.

    Attributes:
        id_tarefa: Id da tarefa inválida, ou None se não for identificável.
        motivo: Descrição da violação.
    """

    def __init__(self, id_tarefa: int | None, motivo: str) -> None:
        self.id_tarefa = id_tarefa
        self.motivo = motivo
        alvo = "não identificada" if id_tarefa is None else str(id_tarefa)
        super().__init__(f"Tarefa {alvo}: {motivo}")


@dataclass(frozen=True)
class Tarefa:
    """Unidade de trabalho recebida do sistema externo."""

    id_tarefa: int
    titulo: str
    prioridade: str
    status: str
    data_criacao: datetime
    prazo: datetime
    data_inicio: datetime | None = None
    data_conclusao: datetime | None = None


@dataclass(frozen=True)
class IndicadorPrioridade:
    """Métricas de um subconjunto de tarefas concluídas."""

    quantidade: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float


@dataclass(frozen=True)
class RelatorioProdutividade:
    """Relatório consolidado devolvido por analyze_tasks."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    indicadores_por_prioridade: dict[str, IndicadorPrioridade]


def analyze_tasks(tarefas: list[Tarefa]) -> RelatorioProdutividade:
    """Analisa uma lista de tarefas e retorna métricas de produtividade.

    Args:
        tarefas: Lista de tarefas a serem analisadas. Pode ser vazia.

    Returns:
        Relatório com totais, métricas gerais e indicadores por prioridade.

    Raises:
        TaskValidationError: Se alguma tarefa violar as restrições do contrato.
    """
    logger.debug("Iniciando análise de %d tarefa(s)", len(tarefas))
    _validar_lista(tarefas)
    concluidas = [t for t in tarefas if t.status == "concluida"]
    geral = _calcular_indicador(concluidas)
    relatorio = RelatorioProdutividade(
        total_tarefas=len(tarefas),
        total_concluidas=len(concluidas),
        total_pendentes=sum(1 for t in tarefas if t.status == "pendente"),
        tempo_medio_conclusao_horas=geral.tempo_medio_conclusao_horas,
        taxa_atraso_percentual=geral.taxa_atraso_percentual,
        indicadores_por_prioridade=_indicadores_por_prioridade(concluidas),
    )
    logger.info("Análise concluída: %d tarefa(s), %d concluída(s)",
                relatorio.total_tarefas, relatorio.total_concluidas)
    return relatorio


# --- Validação ---------------------------------------------------------------


def _validar_lista(tarefas: list[Tarefa]) -> None:
    """Valida cada tarefa e a unicidade dos ids (fail-fast, RN-10).

    Args:
        tarefas: Lista recebida por analyze_tasks.

    Raises:
        TaskValidationError: Na primeira violação encontrada.
    """
    ids_vistos: set[int] = set()
    for tarefa in tarefas:
        _validar_tarefa(tarefa)
        if tarefa.id_tarefa in ids_vistos:
            raise TaskValidationError(
                tarefa.id_tarefa, "id_tarefa duplicado na lista"
            )
        ids_vistos.add(tarefa.id_tarefa)


def _validar_tarefa(tarefa: object) -> None:
    """Aplica todas as regras do contrato de entrada a uma tarefa.

    Args:
        tarefa: Elemento da lista de entrada.

    Raises:
        TaskValidationError: Se o elemento não for Tarefa ou violar o contrato.
    """
    if not isinstance(tarefa, Tarefa):
        raise TaskValidationError(
            None, f"elemento do tipo {type(tarefa).__name__} não é uma Tarefa"
        )
    _validar_id(tarefa)
    _validar_titulo(tarefa)
    _validar_dominios(tarefa)
    _validar_datas(tarefa)
    _validar_cronologia(tarefa)


def _validar_id(tarefa: Tarefa) -> None:
    """Exige id_tarefa inteiro (não bool) e maior que zero.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se o id for inválido.
    """
    valor = tarefa.id_tarefa
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise TaskValidationError(
            None, f"id_tarefa deve ser int, recebido {valor!r}"
        )
    if valor <= 0:
        raise TaskValidationError(valor, "id_tarefa deve ser maior que zero")


def _validar_titulo(tarefa: Tarefa) -> None:
    """Exige título não vazio, não só espaços e com até 200 caracteres.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se o título for inválido.
    """
    titulo = tarefa.titulo
    if not isinstance(titulo, str) or not titulo.strip():
        raise TaskValidationError(
            tarefa.id_tarefa, "titulo deve ser texto não vazio"
        )
    if len(titulo) > TAMANHO_MAXIMO_TITULO:
        raise TaskValidationError(
            tarefa.id_tarefa,
            f"titulo excede {TAMANHO_MAXIMO_TITULO} caracteres "
            f"({len(titulo)})",
        )


def _validar_dominios(tarefa: Tarefa) -> None:
    """Exige prioridade e status dentro dos domínios do contrato.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se prioridade ou status estiverem fora do domínio.
    """
    if tarefa.prioridade not in PRIORIDADES:
        raise TaskValidationError(
            tarefa.id_tarefa,
            f"prioridade {tarefa.prioridade!r} fora do domínio "
            f"{list(PRIORIDADES)}",
        )
    if tarefa.status not in STATUS_VALIDOS:
        raise TaskValidationError(
            tarefa.id_tarefa,
            f"status {tarefa.status!r} fora do domínio "
            f"{sorted(STATUS_VALIDOS)}",
        )


def _validar_datas(tarefa: Tarefa) -> None:
    """Exige datas em UTC; início e conclusão são obrigatórios se concluída.

    Args:
        tarefa: Tarefa a validar.

    Raises:
        TaskValidationError: Se faltar data obrigatória ou alguma não for UTC.
    """
    concluida = tarefa.status == "concluida"
    _validar_data_utc(tarefa, "data_criacao", obrigatoria=True)
    _validar_data_utc(tarefa, "prazo", obrigatoria=True)
    _validar_data_utc(tarefa, "data_inicio", obrigatoria=concluida)
    _validar_data_utc(tarefa, "data_conclusao", obrigatoria=concluida)


def _validar_data_utc(tarefa: Tarefa, campo: str, obrigatoria: bool) -> None:
    """Valida um campo de data: presença, tipo datetime e fuso UTC.

    Args:
        tarefa: Tarefa a validar.
        campo: Nome do campo de data.
        obrigatoria: Se o campo não pode ser None.

    Raises:
        TaskValidationError: Se o campo violar alguma dessas regras.
    """
    valor = getattr(tarefa, campo)
    if valor is None:
        if obrigatoria:
            raise TaskValidationError(
                tarefa.id_tarefa, f"{campo} é obrigatório"
            )
        return
    if not isinstance(valor, datetime):
        raise TaskValidationError(
            tarefa.id_tarefa, f"{campo} deve ser datetime"
        )
    if valor.utcoffset() != timedelta(0):
        raise TaskValidationError(
            tarefa.id_tarefa, f"{campo} deve ser timezone-aware em UTC"
        )


def _validar_cronologia(tarefa: Tarefa) -> None:
    """Exige criação <= início <= conclusão para as datas informadas.

    Args:
        tarefa: Tarefa com datas já validadas como UTC.

    Raises:
        TaskValidationError: Se houver anomalia cronológica.
    """
    criacao, inicio, conclusao = (
        tarefa.data_criacao, tarefa.data_inicio, tarefa.data_conclusao
    )
    if conclusao is not None and conclusao < criacao:
        raise TaskValidationError(
            tarefa.id_tarefa, "data_conclusao anterior a data_criacao"
        )
    if inicio is not None and inicio < criacao:
        raise TaskValidationError(
            tarefa.id_tarefa, "data_inicio anterior a data_criacao"
        )
    if inicio is not None and conclusao is not None and conclusao < inicio:
        raise TaskValidationError(
            tarefa.id_tarefa, "data_conclusao anterior a data_inicio"
        )


# --- Cálculo -----------------------------------------------------------------


def _indicadores_por_prioridade(
    concluidas: list[Tarefa],
) -> dict[str, IndicadorPrioridade]:
    """Calcula os indicadores de cada prioridade, com as 3 chaves (RN-09).

    Args:
        concluidas: Tarefas concluídas e já validadas.

    Returns:
        Dicionário com as chaves baixa, media e alta.
    """
    return {
        prioridade: _calcular_indicador(
            [t for t in concluidas if t.prioridade == prioridade]
        )
        for prioridade in PRIORIDADES
    }


def _calcular_indicador(concluidas: list[Tarefa]) -> IndicadorPrioridade:
    """Calcula quantidade, tempo médio e taxa de atraso (RN-02 a RN-08).

    Args:
        concluidas: Tarefas concluídas e já validadas.

    Returns:
        Indicador com valores arredondados, ou zerado se a lista for vazia.
    """
    quantidade = len(concluidas)
    if quantidade == 0:
        return IndicadorPrioridade(
            quantidade=0,
            tempo_medio_conclusao_horas=0.0,
            taxa_atraso_percentual=0.0,
        )
    horas = math.fsum(_duracao_horas(t) for t in concluidas)
    atrasadas = sum(1 for t in concluidas if _em_atraso(t))
    return IndicadorPrioridade(
        quantidade=quantidade,
        tempo_medio_conclusao_horas=round(horas / quantidade, CASAS_DECIMAIS),
        taxa_atraso_percentual=round(
            atrasadas / quantidade * 100, CASAS_DECIMAIS
        ),
    )


def _duracao_horas(tarefa: Tarefa) -> float:
    """Calcula o tempo de conclusão em horas (RN-02).

    Args:
        tarefa: Tarefa concluída, com data_inicio e data_conclusao validadas.

    Returns:
        Intervalo entre início e conclusão, em horas.
    """
    inicio = cast(datetime, tarefa.data_inicio)
    conclusao = cast(datetime, tarefa.data_conclusao)
    return (conclusao - inicio).total_seconds() / SEGUNDOS_POR_HORA


def _em_atraso(tarefa: Tarefa) -> bool:
    """Indica se a conclusão foi estritamente posterior ao prazo (RN-03).

    Args:
        tarefa: Tarefa concluída, com data_conclusao validada.

    Returns:
        True se a tarefa foi concluída após o prazo.
    """
    return cast(datetime, tarefa.data_conclusao) > tarefa.prazo
