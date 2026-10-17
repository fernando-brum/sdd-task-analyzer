"""Test Harness do TaskAnalyzer.

Traduz os cenários de aceite da seção 3 de specs/task_analyzer_spec.md (v1.1).
Todas as datas são fixas: nenhum teste depende do relógio do sistema.
"""

import copy
import dataclasses
from datetime import datetime, timedelta, timezone

import pytest

from task_analyzer import (
    IndicadorPrioridade,
    RelatorioProdutividade,
    Tarefa,
    TaskAnalyzerError,
    TaskValidationError,
    analyze_tasks,
)

UTC = timezone.utc
CRIACAO = datetime(2026, 1, 10, 8, 0, tzinfo=UTC)


def _dt(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 1, dia, hora, minuto, tzinfo=UTC)


def _tarefa(**campos: object) -> Tarefa:
    """Cria uma tarefa concluída e válida, sobrescrevendo os campos informados."""
    padrao: dict[str, object] = {
        "id_tarefa": 1,
        "titulo": "Tarefa de teste",
        "prioridade": "alta",
        "status": "concluida",
        "data_criacao": CRIACAO,
        "prazo": _dt(10, 18),
        "data_inicio": _dt(10, 9),
        "data_conclusao": _dt(10, 11),
    }
    padrao.update(campos)
    return Tarefa(**padrao)  # type: ignore[arg-type]


def _pendente(id_tarefa: int, prioridade: str = "baixa") -> Tarefa:
    return _tarefa(
        id_tarefa=id_tarefa,
        prioridade=prioridade,
        status="pendente",
        data_inicio=None,
        data_conclusao=None,
    )


ZERADO = IndicadorPrioridade(
    quantidade=0, tempo_medio_conclusao_horas=0.0, taxa_atraso_percentual=0.0
)


@pytest.fixture
def tarefas_cenario_1() -> list[Tarefa]:
    """As 5 tarefas do Cenário 1 da spec."""
    return [
        _tarefa(id_tarefa=1, prioridade="alta", data_inicio=_dt(10, 9),
                data_conclusao=_dt(10, 11), prazo=_dt(10, 18)),
        _tarefa(id_tarefa=2, prioridade="alta", data_inicio=_dt(10, 8),
                data_conclusao=_dt(10, 12), prazo=_dt(10, 10)),
        _tarefa(id_tarefa=3, prioridade="media", data_inicio=_dt(10, 14),
                data_conclusao=_dt(10, 14, 30), prazo=_dt(11, 12)),
        _pendente(4, "baixa"),
        _tarefa(id_tarefa=5, prioridade="baixa", status="cancelada",
                data_inicio=None, data_conclusao=None, prazo=_dt(12, 18)),
    ]


# --- Cenário 1: sucesso ------------------------------------------------------


def test_cenario_1_totais(tarefas_cenario_1: list[Tarefa]) -> None:
    relatorio = analyze_tasks(tarefas_cenario_1)

    assert isinstance(relatorio, RelatorioProdutividade)
    assert relatorio.total_tarefas == 5
    assert relatorio.total_concluidas == 3
    assert relatorio.total_pendentes == 1


def test_cenario_1_metricas_gerais(tarefas_cenario_1: list[Tarefa]) -> None:
    relatorio = analyze_tasks(tarefas_cenario_1)

    assert relatorio.tempo_medio_conclusao_horas == 2.17
    assert relatorio.taxa_atraso_percentual == 33.33


def test_cenario_1_indicadores_por_prioridade(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    relatorio = analyze_tasks(tarefas_cenario_1)

    assert relatorio.indicadores_por_prioridade == {
        "alta": IndicadorPrioridade(
            quantidade=2, tempo_medio_conclusao_horas=3.0,
            taxa_atraso_percentual=50.0,
        ),
        "media": IndicadorPrioridade(
            quantidade=1, tempo_medio_conclusao_horas=0.5,
            taxa_atraso_percentual=0.0,
        ),
        "baixa": ZERADO,
    }


# --- Cenário 2: datas inconsistentes -----------------------------------------


def test_cenario_2_conclusao_anterior_a_criacao_dispara_erro() -> None:
    tarefa = _tarefa(
        id_tarefa=7,
        data_criacao=_dt(10, 10),
        data_inicio=_dt(10, 7),
        data_conclusao=_dt(10, 8),
    )

    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([tarefa])

    assert erro.value.id_tarefa == 7
    assert "data_conclusao" in erro.value.motivo
    assert "data_criacao" in erro.value.motivo
    assert "7" in str(erro.value)


# --- Casos de borda ----------------------------------------------------------


def test_cb01_lista_vazia_retorna_metricas_zeradas() -> None:
    relatorio = analyze_tasks([])

    assert relatorio == RelatorioProdutividade(
        total_tarefas=0,
        total_concluidas=0,
        total_pendentes=0,
        tempo_medio_conclusao_horas=0.0,
        taxa_atraso_percentual=0.0,
        indicadores_por_prioridade={
            "baixa": ZERADO, "media": ZERADO, "alta": ZERADO,
        },
    )


def test_cb02_apenas_pendentes_retorna_metricas_zeradas() -> None:
    relatorio = analyze_tasks([_pendente(1, "alta"), _pendente(2, "media")])

    assert relatorio.total_tarefas == 2
    assert relatorio.total_concluidas == 0
    assert relatorio.total_pendentes == 2
    assert relatorio.tempo_medio_conclusao_horas == 0.0
    assert relatorio.taxa_atraso_percentual == 0.0
    assert set(relatorio.indicadores_por_prioridade) == {"baixa", "media", "alta"}
    assert all(
        indicador == ZERADO
        for indicador in relatorio.indicadores_por_prioridade.values()
    )


def test_cb03_conclusao_no_instante_do_prazo_nao_e_atraso() -> None:
    tarefa = _tarefa(data_conclusao=_dt(10, 18), prazo=_dt(10, 18))

    relatorio = analyze_tasks([tarefa])

    assert relatorio.taxa_atraso_percentual == 0.0


def test_conclusao_um_segundo_apos_o_prazo_e_atraso() -> None:
    prazo = _dt(10, 18)
    tarefa = _tarefa(data_conclusao=prazo + timedelta(seconds=1), prazo=prazo)

    assert analyze_tasks([tarefa]).taxa_atraso_percentual == 100.0


def test_media_e_arredondada_para_duas_casas() -> None:
    tarefa = _tarefa(data_inicio=_dt(10, 9), data_conclusao=_dt(10, 9, 20))

    assert analyze_tasks([tarefa]).tempo_medio_conclusao_horas == 0.33


# --- Validação (fail-fast) ---------------------------------------------------

FUSO_BRASILIA = timezone(timedelta(hours=-3))


@pytest.mark.parametrize(
    ("campos", "trecho_motivo"),
    [
        pytest.param({"data_conclusao": _dt(10, 8, 30)}, "data_inicio",
                     id="cb04-conclusao-antes-do-inicio"),
        pytest.param({"data_inicio": _dt(10, 7)}, "data_criacao",
                     id="inicio-antes-da-criacao"),
        pytest.param({"prioridade": "urgente"}, "prioridade",
                     id="cb05-prioridade-urgente"),
        pytest.param({"prioridade": "média"}, "prioridade",
                     id="cb05-prioridade-com-acento"),
        pytest.param({"prioridade": "ALTA"}, "prioridade",
                     id="cb05-prioridade-maiuscula"),
        pytest.param({"status": "feito"}, "status", id="cb05-status-invalido"),
        pytest.param({"id_tarefa": 0}, "id_tarefa", id="id-zero"),
        pytest.param({"id_tarefa": -1}, "id_tarefa", id="id-negativo"),
        pytest.param({"id_tarefa": True}, "id_tarefa", id="id-bool"),
        pytest.param({"id_tarefa": "1"}, "id_tarefa", id="id-str"),
        pytest.param({"data_criacao": datetime(2026, 1, 10, 8, 0)},
                     "data_criacao", id="cb07-criacao-naive"),
        pytest.param({"prazo": datetime(2026, 1, 10, 18, 0)}, "prazo",
                     id="cb07-prazo-naive"),
        pytest.param({"data_inicio": datetime(2026, 1, 10, 9, 0,
                                               tzinfo=FUSO_BRASILIA)},
                     "data_inicio", id="cb07-inicio-fora-de-utc"),
        pytest.param({"prazo": "2026-01-10"}, "prazo", id="prazo-str"),
        pytest.param({"data_inicio": None}, "data_inicio",
                     id="cb08-concluida-sem-inicio"),
        pytest.param({"data_conclusao": None}, "data_conclusao",
                     id="cb08-concluida-sem-conclusao"),
        pytest.param({"titulo": ""}, "titulo", id="cb09-titulo-vazio"),
        pytest.param({"titulo": "   "}, "titulo", id="cb09-titulo-espacos"),
        pytest.param({"titulo": "x" * 201}, "titulo",
                     id="cb09-titulo-201-caracteres"),
        pytest.param({"titulo": None}, "titulo", id="titulo-none"),
    ],
)
def test_tarefa_invalida_dispara_erro(
    campos: dict[str, object], trecho_motivo: str
) -> None:
    tarefa = _tarefa(**{"id_tarefa": 42, **campos})

    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([tarefa])

    assert trecho_motivo in erro.value.motivo


def test_titulo_com_200_caracteres_e_valido() -> None:
    assert analyze_tasks([_tarefa(titulo="x" * 200)]).total_tarefas == 1


def test_erro_expoe_id_da_tarefa_invalida() -> None:
    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([_tarefa(id_tarefa=1), _tarefa(id_tarefa=9, status="x")])

    assert erro.value.id_tarefa == 9


def test_cb06_ids_duplicados_disparam_erro() -> None:
    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([_tarefa(id_tarefa=3), _tarefa(id_tarefa=3)])

    assert erro.value.id_tarefa == 3
    assert "duplicado" in erro.value.motivo


def test_elemento_que_nao_e_tarefa_dispara_erro() -> None:
    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([{"id_tarefa": 1}])  # type: ignore[list-item]

    assert erro.value.id_tarefa is None


def test_rn13_pendente_com_data_inicio_valida_e_aceita() -> None:
    tarefa = _tarefa(status="pendente", data_conclusao=None)

    assert analyze_tasks([tarefa]).total_pendentes == 1


def test_rn13_pendente_com_data_naive_dispara_erro() -> None:
    tarefa = _tarefa(
        status="pendente",
        data_inicio=datetime(2026, 1, 10, 9, 0),
        data_conclusao=None,
    )

    with pytest.raises(TaskValidationError):
        analyze_tasks([tarefa])


def test_task_validation_error_herda_de_task_analyzer_error() -> None:
    assert issubclass(TaskValidationError, TaskAnalyzerError)
    assert not issubclass(TaskAnalyzerError, ValueError)


# --- Propriedades não funcionais ---------------------------------------------


def test_cb10_ordem_da_entrada_nao_altera_resultado(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    invertida = list(reversed(tarefas_cenario_1))

    assert analyze_tasks(invertida) == analyze_tasks(tarefas_cenario_1)


def test_cb11_analise_nao_modifica_a_entrada(
    tarefas_cenario_1: list[Tarefa],
) -> None:
    copia = copy.deepcopy(tarefas_cenario_1)

    analyze_tasks(tarefas_cenario_1)

    assert tarefas_cenario_1 == copia


def test_resultado_e_deterministico(tarefas_cenario_1: list[Tarefa]) -> None:
    assert analyze_tasks(tarefas_cenario_1) == analyze_tasks(tarefas_cenario_1)


def test_dataclasses_sao_imutaveis(tarefas_cenario_1: list[Tarefa]) -> None:
    relatorio = analyze_tasks(tarefas_cenario_1)

    with pytest.raises(dataclasses.FrozenInstanceError):
        tarefas_cenario_1[0].titulo = "alterado"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        relatorio.total_tarefas = 0  # type: ignore[misc]
