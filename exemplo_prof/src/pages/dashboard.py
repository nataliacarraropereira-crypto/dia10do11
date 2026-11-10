from __future__ import annotations

from datetime import date

import streamlit as st
from sqlalchemy import func, select

from src.database import SessionLocal
from src.models import Aluno, Aula, Disciplina, Professor, Resultado, Turma


def render_dashboard() -> None:
    st.title("Preparatório UFSC")
    st.caption("Organização acadêmica para uma preparação consistente rumo à UFSC.")

    with SessionLocal() as session:
        student_count = session.scalar(
            select(func.count(Aluno.id)).where(Aluno.excluido.is_(False))
        ) or 0
        teacher_count = session.scalar(
            select(func.count(Professor.id)).where(Professor.excluido.is_(False))
        ) or 0
        class_count = session.scalar(
            select(func.count(Turma.id)).where(
                Turma.excluido.is_(False), Turma.situacao == "Ativa"
            )
        ) or 0
        subject_count = session.scalar(
            select(func.count(Disciplina.id)).where(Disciplina.excluido.is_(False))
        ) or 0

        columns = st.columns(4)
        columns[0].metric("Alunos cadastrados", student_count)
        columns[1].metric("Professores", teacher_count)
        columns[2].metric("Turmas ativas", class_count)
        columns[3].metric("Disciplinas", subject_count)

        left, right = st.columns(2)
        with left:
            st.subheader("Próximas aulas")
            lessons = session.scalars(
                select(Aula)
                .where(
                    Aula.excluido.is_(False),
                    Aula.situacao == "Agendada",
                    Aula.data >= date.today(),
                )
                .order_by(Aula.data, Aula.horario_inicio)
                .limit(6)
            ).all()
            if lessons:
                st.dataframe(
                    [
                        {
                            "Data": lesson.data.strftime("%d/%m/%Y"),
                            "Horário": lesson.horario_inicio.strftime("%H:%M"),
                            "Aula": lesson.titulo,
                            "Disciplina": lesson.disciplina.nome,
                            "Professor": lesson.professor.nome_completo,
                            "Turma": lesson.turma.nome,
                        }
                        for lesson in lessons
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Nenhuma aula futura agendada.")

        with right:
            st.subheader("Últimos resultados de simulados")
            results = session.scalars(
                select(Resultado)
                .where(Resultado.excluido.is_(False))
                .order_by(Resultado.data_realizacao.desc(), Resultado.id.desc())
                .limit(6)
            ).all()
            if results:
                st.dataframe(
                    [
                        {
                            "Data": result.data_realizacao.strftime("%d/%m/%Y"),
                            "Aluno": result.aluno.nome_completo,
                            "Simulado": result.simulado.titulo,
                            "Acertos": result.quantidade_acertos,
                            "Pontuação": result.pontuacao_obtida,
                            "Correção": result.situacao_correcao,
                        }
                        for result in results
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("Ainda não há resultados cadastrados.")
