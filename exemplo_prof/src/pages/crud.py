from __future__ import annotations

from datetime import date, time
from typing import Any

import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.database import SessionLocal
from src.models import (
    ENTITY_MODELS,
    Aluno,
    Aula,
    Disciplina,
    Frequencia,
    MaterialEstudo,
    Matricula,
    Plano,
    Professor,
    Questao,
    Resultado,
    Simulado,
    Turma,
    display_name,
)
from src.services import (
    create_record,
    parse_value,
    restore_record,
    soft_delete_record,
    update_record,
)


def _field(name: str, label: str, kind: str = "text", **options: Any) -> dict[str, Any]:
    return {"name": name, "label": label, "kind": kind, **options}


ENTITIES: dict[str, dict[str, Any]] = {
    "alunos": {
        "label": "Alunos",
        "singular": "aluno",
        "model": Aluno,
        "columns": ["nome_completo", "cpf", "email", "curso_ufsc_pretendido", "situacao"],
        "fields": [
            _field("nome_completo", "Nome completo", required=True),
            _field("cpf", "CPF", "cpf", required=True),
            _field("data_nascimento", "Data de nascimento", "date", required=True),
            _field("email", "E-mail", "email", required=True),
            _field("telefone", "Telefone", required=True),
            _field("ano_conclusao_ensino_medio", "Ano de conclusão do Ensino Médio", "integer", optional=True),
            _field("escola_origem", "Escola de origem", optional=True),
            _field("curso_ufsc_pretendido", "Curso da UFSC pretendido", required=True),
            _field("modalidade_concorrencia", "Modalidade de concorrência", "choice", choices=["Ampla concorrência", "Escola pública", "PPI", "Pessoa com deficiência", "Outra"], required=True),
            _field("data_cadastro", "Data de cadastro", "date", required=True),
            _field("situacao", "Situação", "choice", choices=["Ativo", "Inativo"], required=True),
        ],
    },
    "professores": {
        "label": "Professores",
        "singular": "professor",
        "model": Professor,
        "columns": ["nome_completo", "email", "telefone", "formacao_academica", "situacao"],
        "fields": [
            _field("nome_completo", "Nome completo", required=True),
            _field("cpf", "CPF", "cpf", required=True),
            _field("email", "E-mail", "email", required=True),
            _field("telefone", "Telefone", required=True),
            _field("formacao_academica", "Formação acadêmica", required=True),
            _field("data_contratacao", "Data de contratação", "date", required=True),
            _field("situacao", "Situação", "choice", choices=["Ativo", "Inativo"], required=True),
            _field("disciplinas", "Disciplinas ministradas", "multi_relation", target=Disciplina),
        ],
    },
    "turmas": {
        "label": "Turmas",
        "singular": "turma",
        "model": Turma,
        "columns": ["nome", "ano_vestibular_ufsc", "modalidade", "capacidade_maxima", "situacao"],
        "fields": [
            _field("nome", "Nome", required=True),
            _field("descricao", "Descrição", "textarea", optional=True),
            _field("ano_vestibular_ufsc", "Ano do vestibular UFSC", "integer", required=True),
            _field("data_inicio", "Data de início", "date", required=True),
            _field("data_encerramento", "Data de encerramento", "date", optional=True),
            _field("turno", "Turno", "choice", choices=["Matutino", "Vespertino", "Noturno", "Integral"], required=True),
            _field("modalidade", "Modalidade", "choice", choices=["Presencial", "Online", "Híbrida"], required=True),
            _field("capacidade_maxima", "Capacidade máxima", "integer", required=True),
            _field("situacao", "Situação", "choice", choices=["Ativa", "Inativa", "Encerrada"], required=True),
        ],
    },
    "matriculas": {
        "label": "Matrículas",
        "singular": "matrícula",
        "model": Matricula,
        "columns": ["aluno", "turma", "plano", "data_matricula", "valor", "situacao"],
        "fields": [
            _field("aluno_id", "Aluno", "relation", target=Aluno, required=True),
            _field("turma_id", "Turma", "relation", target=Turma, required=True),
            _field("plano_id", "Plano", "relation", target=Plano, required=True),
            _field("data_matricula", "Data da matrícula", "date", required=True),
            _field("valor", "Valor contratado (R$)", "number", required=True),
            _field("forma_pagamento", "Forma de pagamento", "choice", choices=["Pix", "Cartão de crédito", "Cartão de débito", "Boleto", "Transferência", "Outra"], required=True),
            _field("situacao", "Situação", "choice", choices=["Ativa", "Cancelada", "Concluída"], required=True),
        ],
    },
    "disciplinas": {
        "label": "Disciplinas",
        "singular": "disciplina",
        "model": Disciplina,
        "columns": ["nome", "area_conhecimento", "carga_horaria", "situacao"],
        "fields": [
            _field("nome", "Nome", required=True),
            _field("descricao", "Descrição", "textarea", optional=True),
            _field("area_conhecimento", "Área do conhecimento", "choice", choices=["Linguagens", "Matemática", "Ciências da Natureza", "Ciências Humanas", "Redação", "Outra"], required=True),
            _field("carga_horaria", "Carga horária (horas)", "integer", required=True),
            _field("situacao", "Situação", "choice", choices=["Ativa", "Inativa"], required=True),
        ],
    },
    "aulas": {
        "label": "Aulas",
        "singular": "aula",
        "model": Aula,
        "columns": ["titulo", "disciplina", "professor", "turma", "data", "horario_inicio", "situacao"],
        "fields": [
            _field("titulo", "Título", required=True),
            _field("descricao_conteudo", "Descrição do conteúdo", "textarea", optional=True),
            _field("disciplina_id", "Disciplina", "relation", target=Disciplina, required=True),
            _field("professor_id", "Professor", "relation", target=Professor, required=True),
            _field("turma_id", "Turma", "relation", target=Turma, required=True),
            _field("data", "Data", "date", required=True),
            _field("horario_inicio", "Horário de início", "time", required=True),
            _field("horario_encerramento", "Horário de encerramento", "time", required=True),
            _field("tipo_aula", "Tipo de aula", "choice", choices=["Teórica", "Resolução de questões", "Revisão", "Simulado", "Outra"], required=True),
            _field("local_ou_link", "Local ou link de acesso", optional=True),
            _field("situacao", "Situação", "choice", choices=["Agendada", "Concluída", "Cancelada"], required=True),
        ],
    },
    "materiais": {
        "label": "Materiais de estudo",
        "singular": "material",
        "model": MaterialEstudo,
        "columns": ["titulo", "tipo_material", "disciplina", "professor", "data_disponibilizacao", "situacao"],
        "fields": [
            _field("titulo", "Título", required=True),
            _field("descricao", "Descrição", "textarea", optional=True),
            _field("tipo_material", "Tipo de material", "choice", choices=["Apostila", "Lista de exercícios", "Vídeo", "Apresentação", "Artigo", "Outro"], required=True),
            _field("arquivo_ou_link", "Arquivo ou link", required=True),
            _field("data_disponibilizacao", "Data de disponibilização", "date", required=True),
            _field("disciplina_id", "Disciplina", "relation", target=Disciplina, required=True),
            _field("professor_id", "Professor responsável", "relation", target=Professor, required=True),
            _field("turmas", "Turmas que receberão o material", "multi_relation", target=Turma),
            _field("situacao", "Situação", "choice", choices=["Disponível", "Indisponível"], required=True),
        ],
    },
    "simulados": {
        "label": "Simulados",
        "singular": "simulado",
        "model": Simulado,
        "columns": ["titulo", "ano_prova_ufsc_referencia", "data_realizacao", "quantidade_questoes", "situacao", "turma"],
        "fields": [
            _field("titulo", "Título", required=True),
            _field("descricao", "Descrição", "textarea", optional=True),
            _field("ano_prova_ufsc_referencia", "Ano da prova UFSC de referência", "integer", required=True),
            _field("data_disponibilizacao", "Data de disponibilização", "date", required=True),
            _field("data_realizacao", "Data de realização", "date", required=True),
            _field("horario_inicio", "Horário de início", "time", required=True),
            _field("tempo_maximo_duracao_minutos", "Tempo máximo (minutos)", "integer", required=True),
            _field("quantidade_questoes", "Quantidade de questões", "integer", required=True),
            _field("pontuacao_maxima", "Pontuação máxima", "number", required=True),
            _field("situacao", "Situação", "choice", choices=["Rascunho", "Disponível", "Encerrado"], required=True),
            _field("turma_id", "Turma", "relation", target=Turma, required=True),
            _field("questoes", "Questões", "multi_relation", target=Questao),
        ],
    },
    "questoes": {
        "label": "Questões",
        "singular": "questão",
        "model": Questao,
        "columns": ["enunciado", "tipo", "disciplina", "nivel_dificuldade", "ano_prova_ufsc_origem", "situacao"],
        "fields": [
            _field("enunciado", "Enunciado", "textarea", required=True),
            _field("tipo", "Tipo", "choice", choices=["Objetiva", "Discursiva"], required=True),
            _field("disciplina_id", "Disciplina", "relation", target=Disciplina, required=True),
            _field("nivel_dificuldade", "Nível de dificuldade", "choice", choices=["Fácil", "Médio", "Difícil"], required=True),
            _field("ano_prova_ufsc_origem", "Ano da prova UFSC de origem", "integer", optional=True),
            _field("pontuacao", "Pontuação", "number", required=True),
            _field("resposta_correta", "Resposta correta", "textarea", optional=True),
            _field("resolucao_ou_comentario", "Resolução ou comentário", "textarea", optional=True),
            _field("situacao", "Situação", "choice", choices=["Ativa", "Inativa"], required=True),
        ],
    },
    "resultados": {
        "label": "Resultados",
        "singular": "resultado",
        "model": Resultado,
        "columns": ["aluno", "simulado", "data_realizacao", "quantidade_acertos", "quantidade_erros", "pontuacao_obtida", "situacao_correcao"],
        "fields": [
            _field("aluno_id", "Aluno", "relation", target=Aluno, required=True),
            _field("simulado_id", "Simulado", "relation", target=Simulado, required=True),
            _field("data_realizacao", "Data de realização", "date", required=True),
            _field("quantidade_acertos", "Quantidade de acertos", "integer", required=True),
            _field("quantidade_erros", "Quantidade de erros", "integer", required=True),
            _field("pontuacao_obtida", "Pontuação obtida", "number", required=True),
            _field("tempo_utilizado_minutos", "Tempo utilizado (minutos)", "integer", required=True),
            _field("situacao_correcao", "Situação da correção", "choice", choices=["Pendente", "Corrigido", "Revisado"], required=True),
            _field("observacao_professor", "Observação do professor", "textarea", optional=True),
        ],
    },
    "frequencias": {
        "label": "Frequências",
        "singular": "frequência",
        "model": Frequencia,
        "columns": ["aluno", "aula", "situacao", "data_registro", "observacao"],
        "fields": [
            _field("aluno_id", "Aluno", "relation", target=Aluno, required=True),
            _field("aula_id", "Aula", "relation", target=Aula, required=True),
            _field("situacao", "Situação", "choice", choices=["Presente", "Ausente", "Justificada"], required=True),
            _field("data_registro", "Data do registro", "date", required=True),
            _field("observacao", "Observação", "textarea", optional=True),
        ],
    },
    "planos": {
        "label": "Planos",
        "singular": "plano",
        "model": Plano,
        "columns": ["nome", "valor", "duracao", "quantidade_aulas_incluidas", "situacao"],
        "fields": [
            _field("nome", "Nome", required=True),
            _field("descricao", "Descrição", "textarea", optional=True),
            _field("valor", "Valor (R$)", "number", required=True),
            _field("duracao", "Duração", required=True),
            _field("quantidade_aulas_incluidas", "Quantidade de aulas incluídas", "integer", required=True),
            _field("beneficios", "Benefícios", "textarea", optional=True),
            _field("situacao", "Situação", "choice", choices=["Ativo", "Inativo"], required=True),
        ],
    },
}


def _options(session: Any, model: type[Any]) -> list[Any]:
    statement = select(model).where(model.excluido.is_(False)).order_by(model.id)
    return list(session.scalars(statement))


def _render_field(
    session: Any,
    config: dict[str, Any],
    current: Any,
    key: str,
) -> Any:
    name = config["name"]
    label = config["label"] + (" *" if config.get("required") else "")
    kind = config["kind"]
    existing = getattr(current, name, None) if current is not None else None

    if kind in {"text", "email", "cpf"}:
        return st.text_input(label, value=existing or "", key=key)
    if kind == "textarea":
        return st.text_area(label, value=existing or "", key=key)
    if kind == "date":
        if config.get("optional"):
            has_date = st.checkbox(
                f"Informar {config['label'].lower()}",
                value=existing is not None,
                key=f"{key}_enabled",
            )
            if not has_date:
                return None
        initial = existing or date.today()
        return st.date_input(label, value=initial, key=key)
    if kind == "time":
        return st.time_input(label, value=existing or time(8, 0), key=key)
    if kind == "integer":
        minimum = 0 if config.get("optional") else 1
        value = int(existing or 0) if config.get("optional") else int(existing or 1)
        result = st.number_input(label, min_value=minimum, value=value, step=1, key=key)
        return None if config.get("optional") and result == 0 else int(result)
    if kind == "number":
        return st.number_input(
            label, min_value=0.0, value=float(existing or 0.0), step=0.5, key=key
        )
    if kind == "choice":
        choices = config["choices"]
        index = choices.index(existing) if existing in choices else 0
        return st.selectbox(label, choices, index=index, key=key)
    if kind == "relation":
        options = _options(session, config["target"])
        current_id = existing.id if existing is not None and not isinstance(existing, int) else existing
        choices = [None, *options]
        selected_index = next(
            (index for index, option in enumerate(choices) if getattr(option, "id", None) == current_id),
            0,
        )
        selected = st.selectbox(
            label,
            choices,
            index=selected_index,
            format_func=lambda value: "— Selecione —" if value is None else display_name(value),
            key=key,
        )
        return selected.id if selected is not None else None
    if kind == "multi_relation":
        options = _options(session, config["target"])
        current_ids = {item.id for item in existing or []}
        selected = st.multiselect(
            label,
            options,
            default=[item for item in options if item.id in current_ids],
            format_func=display_name,
            key=key,
        )
        return selected
    raise ValueError(f"Tipo de campo não suportado: {kind}")


def _form_values(
    session: Any, config: dict[str, Any], current: Any, form_key: str
) -> tuple[dict[str, Any], bool]:
    values: dict[str, Any] = {}
    with st.form(form_key):
        fields = config["fields"]
        for start in range(0, len(fields), 2):
            columns = st.columns(2)
            for offset, field in enumerate(fields[start : start + 2]):
                with columns[offset]:
                    value = _render_field(
                        session,
                        field,
                        current,
                        f"{form_key}_{field['name']}",
                    )
                if field["kind"] not in {"relation", "multi_relation"}:
                    value = parse_value(value, field["kind"])
                values[field["name"]] = value
        submitted = st.form_submit_button("Salvar")
    return values, submitted


def _validate_required(config: dict[str, Any], values: dict[str, Any]) -> None:
    missing = [
        field["label"]
        for field in config["fields"]
        if field.get("required")
        and (values.get(field["name"]) is None or values.get(field["name"]) == "")
    ]
    if missing:
        raise ValueError("Preencha os campos obrigatórios: " + ", ".join(missing) + ".")
    invalid_cpf = [
        field["label"]
        for field in config["fields"]
        if field["kind"] == "cpf" and len(values.get(field["name"], "")) != 11
    ]
    if invalid_cpf:
        raise ValueError("Informe um CPF com 11 dígitos.")


def _display_value(record: Any, column: str) -> str:
    value = getattr(record, column, None)
    if value is None:
        return "—"
    if isinstance(value, list):
        return ", ".join(display_name(item) for item in value) or "—"
    if hasattr(value, "__table__"):
        return display_name(value)
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def render_crud(entity_key: str) -> None:
    config = ENTITIES[entity_key]
    model = ENTITY_MODELS[entity_key]
    st.title(config["label"])
    st.caption(f"Cadastro e gestão de {config['label'].lower()} do cursinho UFSC.")

    with SessionLocal() as session:
        show_archived = st.checkbox("Incluir registros excluídos", key=f"{entity_key}_archived")
        statement = select(model).order_by(model.id)
        if not show_archived:
            statement = statement.where(model.excluido.is_(False))
        records = list(session.scalars(statement))

        if records:
            table_rows = [
                {
                    "ID": record.id,
                    **{label: _display_value(record, column) for label, column in zip(
                        [field.replace("_", " ").title() for field in config["columns"]],
                        config["columns"],
                    )},
                    **({"Excluído": "Sim"} if record.excluido else {}),
                }
                for record in records
            ]
            st.dataframe(table_rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado. Use o formulário abaixo para cadastrar.")

        tabs = st.tabs(["Cadastrar", "Editar / Excluir", "Visualizar"])
        with tabs[0]:
            st.subheader(f"Novo(a) {config['singular']}")
            values, submitted = _form_values(session, config, None, f"{entity_key}_create")
            if submitted:
                try:
                    _validate_required(config, values)
                    create_record(session, model, values)
                except ValueError as error:
                    session.rollback()
                    st.error(str(error))
                except IntegrityError:
                    session.rollback()
                    st.error("Não foi possível salvar: CPF/e-mail duplicado ou relacionamento inválido.")
                except SQLAlchemyError as error:
                    session.rollback()
                    st.error(f"Erro ao salvar no banco de dados: {error}")
                else:
                    st.success(f"{config['singular'].capitalize()} cadastrado(a) com sucesso.")
                    st.rerun()

        with tabs[1]:
            editable = [record for record in records if not record.excluido]
            archived = [record for record in records if record.excluido]
            selected = st.selectbox(
                "Registro",
                editable,
                format_func=display_name,
                key=f"{entity_key}_edit_selection",
            ) if editable else None
            if selected is not None:
                values, submitted = _form_values(
                    session, config, selected, f"{entity_key}_edit_{selected.id}"
                )
                if submitted:
                    try:
                        _validate_required(config, values)
                        update_record(session, model, selected.id, values)
                    except ValueError as error:
                        session.rollback()
                        st.error(str(error))
                    except IntegrityError:
                        session.rollback()
                        st.error("Não foi possível atualizar: CPF/e-mail duplicado ou relacionamento inválido.")
                    except SQLAlchemyError as error:
                        session.rollback()
                        st.error(f"Erro ao atualizar no banco de dados: {error}")
                    else:
                        st.success("Registro atualizado com sucesso.")
                        st.rerun()
                if st.button("Excluir registro (preservar histórico)", key=f"{entity_key}_delete_{selected.id}"):
                    try:
                        soft_delete_record(session, model, selected.id)
                    except (ValueError, SQLAlchemyError) as error:
                        session.rollback()
                        st.error(f"Não foi possível excluir o registro: {error}")
                    else:
                        st.success("Registro excluído logicamente; o histórico foi preservado.")
                        st.rerun()
            else:
                st.info("Não há registros ativos para editar ou excluir.")
            if archived:
                selected_archived = st.selectbox(
                    "Registro excluído",
                    archived,
                    format_func=display_name,
                    key=f"{entity_key}_restore_selection",
                )
                if st.button("Restaurar registro", key=f"{entity_key}_restore_{selected_archived.id}"):
                    try:
                        restore_record(session, model, selected_archived.id)
                    except (ValueError, IntegrityError, SQLAlchemyError) as error:
                        session.rollback()
                        st.error(f"Não foi possível restaurar o registro: {error}")
                    else:
                        st.success("Registro restaurado.")
                        st.rerun()

        with tabs[2]:
            if records:
                selected_detail = st.selectbox(
                    "Registro para visualizar",
                    records,
                    format_func=display_name,
                    key=f"{entity_key}_view_selection",
                )
                details = {
                    field["label"]: _display_value(selected_detail, field["name"])
                    for field in config["fields"]
                }
                details["ID"] = str(selected_detail.id)
                st.json(details)
            else:
                st.info("Cadastre ou selecione um registro para visualizar os detalhes.")
