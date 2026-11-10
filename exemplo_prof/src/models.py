from __future__ import annotations

import re
from datetime import date, time as time_type
from typing import Any

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Time,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from .database import Base


professor_disciplina = Table(
    "professor_disciplina",
    Base.metadata,
    Column("professor_id", ForeignKey("professores.id"), primary_key=True),
    Column("disciplina_id", ForeignKey("disciplinas.id"), primary_key=True),
)

material_turma = Table(
    "material_turma",
    Base.metadata,
    Column("material_id", ForeignKey("materiais.id"), primary_key=True),
    Column("turma_id", ForeignKey("turmas.id"), primary_key=True),
)

simulado_questao = Table(
    "simulado_questao",
    Base.metadata,
    Column("simulado_id", ForeignKey("simulados.id"), primary_key=True),
    Column("questao_id", ForeignKey("questoes.id"), primary_key=True),
)


class ExclusaoLogica:
    excluido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Aluno(ExclusaoLogica, Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(160), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(40), nullable=False)
    ano_conclusao_ensino_medio: Mapped[int | None] = mapped_column(Integer)
    escola_origem: Mapped[str | None] = mapped_column(String(180))
    curso_ufsc_pretendido: Mapped[str] = mapped_column(String(160), nullable=False)
    modalidade_concorrencia: Mapped[str] = mapped_column(String(100), nullable=False)
    data_cadastro: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativo", nullable=False)

    matriculas: Mapped[list[Matricula]] = relationship(back_populates="aluno")
    resultados: Mapped[list[Resultado]] = relationship(back_populates="aluno")
    frequencias: Mapped[list[Frequencia]] = relationship(back_populates="aluno")

    @validates("cpf")
    def normalizar_cpf(self, _key: str, value: str) -> str:
        return re.sub(r"\D", "", value)

    @validates("email")
    def normalizar_email(self, _key: str, value: str) -> str:
        return value.strip().lower()


class Professor(ExclusaoLogica, Base):
    __tablename__ = "professores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome_completo: Mapped[str] = mapped_column(String(160), nullable=False)
    cpf: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    telefone: Mapped[str] = mapped_column(String(40), nullable=False)
    formacao_academica: Mapped[str] = mapped_column(String(200), nullable=False)
    data_contratacao: Mapped[date] = mapped_column(Date, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativo", nullable=False)

    disciplinas: Mapped[list[Disciplina]] = relationship(
        secondary=professor_disciplina, back_populates="professores"
    )
    aulas: Mapped[list[Aula]] = relationship(back_populates="professor")
    materiais: Mapped[list[MaterialEstudo]] = relationship(back_populates="professor")

    @validates("cpf")
    def normalizar_cpf(self, _key: str, value: str) -> str:
        return re.sub(r"\D", "", value)

    @validates("email")
    def normalizar_email(self, _key: str, value: str) -> str:
        return value.strip().lower()


class Turma(ExclusaoLogica, Base):
    __tablename__ = "turmas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ano_vestibular_ufsc: Mapped[int] = mapped_column(Integer, nullable=False)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    data_encerramento: Mapped[date | None] = mapped_column(Date)
    turno: Mapped[str] = mapped_column(String(30), nullable=False)
    modalidade: Mapped[str] = mapped_column(String(30), nullable=False)
    capacidade_maxima: Mapped[int] = mapped_column(Integer, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativa", nullable=False)

    matriculas: Mapped[list[Matricula]] = relationship(back_populates="turma")
    aulas: Mapped[list[Aula]] = relationship(back_populates="turma")
    materiais: Mapped[list[MaterialEstudo]] = relationship(
        secondary=material_turma, back_populates="turmas"
    )
    simulados: Mapped[list[Simulado]] = relationship(back_populates="turma")


class Plano(ExclusaoLogica, Base):
    __tablename__ = "planos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    duracao: Mapped[str] = mapped_column(String(80), nullable=False)
    quantidade_aulas_incluidas: Mapped[int] = mapped_column(Integer, nullable=False)
    beneficios: Mapped[str | None] = mapped_column(Text)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativo", nullable=False)

    matriculas: Mapped[list[Matricula]] = relationship(back_populates="plano")


class Matricula(ExclusaoLogica, Base):
    __tablename__ = "matriculas"

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), nullable=False)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), nullable=False)
    plano_id: Mapped[int] = mapped_column(ForeignKey("planos.id"), nullable=False)
    data_matricula: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    valor: Mapped[float] = mapped_column(Float, nullable=False)
    forma_pagamento: Mapped[str] = mapped_column(String(50), nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativa", nullable=False)

    aluno: Mapped[Aluno] = relationship(back_populates="matriculas")
    turma: Mapped[Turma] = relationship(back_populates="matriculas")
    plano: Mapped[Plano] = relationship(back_populates="matriculas")


class Disciplina(ExclusaoLogica, Base):
    __tablename__ = "disciplinas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    area_conhecimento: Mapped[str] = mapped_column(String(100), nullable=False)
    carga_horaria: Mapped[int] = mapped_column(Integer, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativa", nullable=False)

    professores: Mapped[list[Professor]] = relationship(
        secondary=professor_disciplina, back_populates="disciplinas"
    )
    aulas: Mapped[list[Aula]] = relationship(back_populates="disciplina")
    materiais: Mapped[list[MaterialEstudo]] = relationship(back_populates="disciplina")
    questoes: Mapped[list[Questao]] = relationship(back_populates="disciplina")


class Aula(ExclusaoLogica, Base):
    __tablename__ = "aulas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao_conteudo: Mapped[str | None] = mapped_column(Text)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professores.id"), nullable=False)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    horario_inicio: Mapped[time_type] = mapped_column(Time, nullable=False)
    horario_encerramento: Mapped[time_type] = mapped_column(Time, nullable=False)
    tipo_aula: Mapped[str] = mapped_column(String(40), nullable=False)
    local_ou_link: Mapped[str | None] = mapped_column(String(300))
    situacao: Mapped[str] = mapped_column(String(20), default="Agendada", nullable=False)

    disciplina: Mapped[Disciplina] = relationship(back_populates="aulas")
    professor: Mapped[Professor] = relationship(back_populates="aulas")
    turma: Mapped[Turma] = relationship(back_populates="aulas")
    frequencias: Mapped[list[Frequencia]] = relationship(back_populates="aula")


class MaterialEstudo(ExclusaoLogica, Base):
    __tablename__ = "materiais"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    tipo_material: Mapped[str] = mapped_column(String(50), nullable=False)
    arquivo_ou_link: Mapped[str] = mapped_column(String(500), nullable=False)
    data_disponibilizacao: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey("professores.id"), nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Disponível", nullable=False)

    disciplina: Mapped[Disciplina] = relationship(back_populates="materiais")
    professor: Mapped[Professor] = relationship(back_populates="materiais")
    turmas: Mapped[list[Turma]] = relationship(
        secondary=material_turma, back_populates="materiais"
    )


class Simulado(ExclusaoLogica, Base):
    __tablename__ = "simulados"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(180), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text)
    ano_prova_ufsc_referencia: Mapped[int] = mapped_column(Integer, nullable=False)
    data_disponibilizacao: Mapped[date] = mapped_column(Date, nullable=False)
    data_realizacao: Mapped[date] = mapped_column(Date, nullable=False)
    horario_inicio: Mapped[time_type] = mapped_column(Time, nullable=False)
    tempo_maximo_duracao_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_questoes: Mapped[int] = mapped_column(Integer, nullable=False)
    pontuacao_maxima: Mapped[float] = mapped_column(Float, nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), default="Disponível", nullable=False)
    turma_id: Mapped[int] = mapped_column(ForeignKey("turmas.id"), nullable=False)

    turma: Mapped[Turma] = relationship(back_populates="simulados")
    questoes: Mapped[list[Questao]] = relationship(
        secondary=simulado_questao, back_populates="simulados"
    )
    resultados: Mapped[list[Resultado]] = relationship(back_populates="simulado")


class Questao(ExclusaoLogica, Base):
    __tablename__ = "questoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    enunciado: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey("disciplinas.id"), nullable=False)
    nivel_dificuldade: Mapped[str] = mapped_column(String(30), nullable=False)
    ano_prova_ufsc_origem: Mapped[int | None] = mapped_column(Integer)
    pontuacao: Mapped[float] = mapped_column(Float, nullable=False)
    resposta_correta: Mapped[str | None] = mapped_column(Text)
    resolucao_ou_comentario: Mapped[str | None] = mapped_column(Text)
    situacao: Mapped[str] = mapped_column(String(20), default="Ativa", nullable=False)

    disciplina: Mapped[Disciplina] = relationship(back_populates="questoes")
    simulados: Mapped[list[Simulado]] = relationship(
        secondary=simulado_questao, back_populates="questoes"
    )


class Resultado(ExclusaoLogica, Base):
    __tablename__ = "resultados"

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), nullable=False)
    simulado_id: Mapped[int] = mapped_column(ForeignKey("simulados.id"), nullable=False)
    data_realizacao: Mapped[date] = mapped_column(Date, nullable=False)
    quantidade_acertos: Mapped[int] = mapped_column(Integer, nullable=False)
    quantidade_erros: Mapped[int] = mapped_column(Integer, nullable=False)
    pontuacao_obtida: Mapped[float] = mapped_column(Float, nullable=False)
    tempo_utilizado_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    situacao_correcao: Mapped[str] = mapped_column(String(30), nullable=False)
    observacao_professor: Mapped[str | None] = mapped_column(Text)

    aluno: Mapped[Aluno] = relationship(back_populates="resultados")
    simulado: Mapped[Simulado] = relationship(back_populates="resultados")


class Frequencia(ExclusaoLogica, Base):
    __tablename__ = "frequencias"

    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey("alunos.id"), nullable=False)
    aula_id: Mapped[int] = mapped_column(ForeignKey("aulas.id"), nullable=False)
    situacao: Mapped[str] = mapped_column(String(20), nullable=False)
    data_registro: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    observacao: Mapped[str | None] = mapped_column(Text)

    aluno: Mapped[Aluno] = relationship(back_populates="frequencias")
    aula: Mapped[Aula] = relationship(back_populates="frequencias")


ENTITY_MODELS: dict[str, type[ExclusaoLogica]] = {
    "alunos": Aluno,
    "professores": Professor,
    "turmas": Turma,
    "matriculas": Matricula,
    "disciplinas": Disciplina,
    "aulas": Aula,
    "materiais": MaterialEstudo,
    "simulados": Simulado,
    "questoes": Questao,
    "resultados": Resultado,
    "frequencias": Frequencia,
    "planos": Plano,
}


def display_name(record: Any) -> str:
    for attribute in ("nome_completo", "nome", "titulo", "enunciado"):
        value = getattr(record, attribute, None)
        if value:
            return f"{value[:70]} (#{record.id})"
    return f"#{record.id}"
