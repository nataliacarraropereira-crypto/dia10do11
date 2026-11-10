from __future__ import annotations

from datetime import date, time
import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    Aula,
    Frequencia,
    Matricula,
    Plano,
    Professor,
    Turma,
)


def _validate_enrollment(session: Session, record: Matricula) -> None:
    is_active = record.situacao == "Ativa"
    if not is_active and record.id is not None:
        return

    turma = session.scalar(
        select(Turma).where(Turma.id == record.turma_id).with_for_update()
    )
    plano = session.get(Plano, record.plano_id)
    if turma is None or turma.excluido:
        raise ValueError("Selecione uma turma válida.")
    if turma.situacao != "Ativa":
        raise ValueError("Turmas inativas ou encerradas não recebem novas matrículas.")
    if plano is None or plano.excluido:
        raise ValueError("Selecione um plano válido.")
    if plano.situacao != "Ativo":
        raise ValueError("Planos inativos não recebem novas matrículas.")
    if not is_active:
        return

    duplicate = session.scalar(
        select(Matricula.id).where(
            Matricula.aluno_id == record.aluno_id,
            Matricula.turma_id == record.turma_id,
            Matricula.situacao == "Ativa",
            Matricula.excluido.is_(False),
            Matricula.id != (record.id or -1),
        )
    )
    if duplicate is not None:
        raise ValueError("Este aluno já possui uma matrícula ativa nesta turma.")

    enrollments = session.scalar(
        select(func.count(Matricula.id)).where(
            Matricula.turma_id == record.turma_id,
            Matricula.situacao == "Ativa",
            Matricula.excluido.is_(False),
            Matricula.id != (record.id or -1),
        )
    ) or 0
    if enrollments >= turma.capacidade_maxima:
        raise ValueError("A turma atingiu sua capacidade máxima.")


def _validate_lesson(session: Session, record: Aula) -> None:
    if record.horario_inicio >= record.horario_encerramento:
        raise ValueError("O horário inicial deve ser anterior ao horário de encerramento.")
    if record.situacao == "Cancelada":
        return

    overlap = session.scalar(
        select(Aula.id).where(
            Aula.professor_id == record.professor_id,
            Aula.data == record.data,
            Aula.situacao != "Cancelada",
            Aula.excluido.is_(False),
            Aula.horario_inicio < record.horario_encerramento,
            Aula.horario_encerramento > record.horario_inicio,
            Aula.id != (record.id or -1),
        )
    )
    if overlap is not None:
        raise ValueError("O professor já possui uma aula nesse intervalo de horário.")


def _validate_attendance(session: Session, record: Frequencia) -> None:
    aula = session.get(Aula, record.aula_id)
    if aula is None or aula.excluido:
        raise ValueError("Selecione uma aula válida.")
    enrollment = session.scalar(
        select(Matricula.id).where(
            Matricula.aluno_id == record.aluno_id,
            Matricula.turma_id == aula.turma_id,
            Matricula.situacao == "Ativa",
            Matricula.excluido.is_(False),
        )
    )
    if enrollment is None:
        raise ValueError("O aluno precisa estar matriculado na turma da aula.")


def validate_record(session: Session, record: Any) -> None:
    if isinstance(record, Matricula):
        _validate_enrollment(session, record)
    elif isinstance(record, Aula):
        _validate_lesson(session, record)
    elif isinstance(record, Frequencia):
        _validate_attendance(session, record)
    elif isinstance(record, Turma):
        if record.capacidade_maxima <= 0:
            raise ValueError("A capacidade máxima deve ser maior que zero.")
        if record.data_encerramento and record.data_encerramento < record.data_inicio:
            raise ValueError("A data de encerramento deve ser posterior ao início da turma.")
    elif isinstance(record, Plano):
        if record.valor < 0 or record.quantidade_aulas_incluidas < 0:
            raise ValueError("Valor e quantidade de aulas não podem ser negativos.")
    elif isinstance(record, Professor):
        if record.situacao not in {"Ativo", "Inativo"}:
            raise ValueError("Situação inválida para professor.")


def create_record(session: Session, model: type[Any], values: dict[str, Any]) -> Any:
    record = model(**values)
    validate_record(session, record)
    session.add(record)
    session.commit()
    return record


def update_record(
    session: Session, model: type[Any], record_id: int, values: dict[str, Any]
) -> Any:
    record = session.get(model, record_id)
    if record is None:
        raise ValueError("O registro selecionado não foi encontrado.")
    for field, value in values.items():
        setattr(record, field, value)
    validate_record(session, record)
    session.commit()
    return record


def soft_delete_record(session: Session, model: type[Any], record_id: int) -> None:
    record = session.get(model, record_id)
    if record is None:
        raise ValueError("O registro selecionado não foi encontrado.")
    record.excluido = True
    session.commit()


def restore_record(session: Session, model: type[Any], record_id: int) -> None:
    record = session.get(model, record_id)
    if record is None:
        raise ValueError("O registro selecionado não foi encontrado.")
    record.excluido = False
    validate_record(session, record)
    session.commit()


def parse_value(value: Any, kind: str) -> Any:
    if value is None:
        return None
    if kind == "cpf":
        return re.sub(r"\D", "", value)
    if kind in {"text", "textarea", "url"}:
        cleaned = value.strip()
        return cleaned or None
    if kind == "email":
        cleaned = value.strip().lower()
        return cleaned or None
    if kind == "date" and isinstance(value, date):
        return value
    if kind == "time" and isinstance(value, time):
        return value
    if kind == "integer":
        return int(value)
    if kind == "number":
        return float(value)
    return value
