# Preparatório UFSC

Sistema web para administrar um cursinho preparatório para o vestibular da Universidade Federal de Santa Catarina (UFSC). Centraliza cadastros acadêmicos e apoia o acompanhamento de aulas, frequência, materiais e desempenho em simulados.

## Funcionalidades

- Dashboard com totais de alunos, professores, turmas ativas e disciplinas, próximas aulas e resultados recentes.
- CRUD persistente para alunos, professores, turmas, matrículas, disciplinas, aulas, materiais de estudo, simulados, questões, resultados, frequências e planos.
- Relacionamentos entre cadastros, incluindo professores e disciplinas, materiais e turmas, e simulados e questões.
- Validações de matrícula, capacidade de turma, horários de aulas, conflitos de professor e frequência vinculada à turma do aluno.
- Exclusão lógica e restauração de registros, preservando o histórico.
- SQLite para desenvolvimento local e MySQL configurável para produção.

Não são criados registros de demonstração automaticamente. Ao iniciar pela primeira vez, o banco fica vazio.

## Tecnologias

- Python 3.11+
- Streamlit
- SQLAlchemy 2
- SQLite (desenvolvimento) e MySQL (produção)
- uv
- python-dotenv

## Estrutura

```text
.
├── .env.example
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/                       # Banco SQLite local (ignorado pelo Git)
├── pyproject.toml
├── README.md
├── src/
│   ├── app.py                  # Entrada e navegação Streamlit
│   ├── database.py             # Configuração de conexão e criação das tabelas
│   ├── models.py               # Entidades e relacionamentos SQLAlchemy
│   ├── services.py             # Regras de negócio e operações persistentes
│   └── pages/
│       ├── crud.py             # Formulários reutilizáveis de CRUD
│       └── dashboard.py        # Indicadores e consultas iniciais
└── uv.lock
```

## Pré-requisitos e instalação

Instale o Python 3.11 ou superior. Instale o uv seguindo a documentação oficial ou, no Windows, pelo PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Na pasta do projeto, instale/sincronize as dependências:

```powershell
uv sync
```

## Execução local com SQLite

O SQLite é o modo padrão. Copie `.env.example` para `.env` (ou use o `.env` local) e confirme:

```dotenv
APP_DB_MODE=sqlite
SQLITE_PATH=data/cursinho_ufsc.db
```

Inicie o Streamlit:

```powershell
uv run python -m streamlit run src/app.py
```

As tabelas são criadas automaticamente em `data/cursinho_ufsc.db` na primeira execução. Não há migração automática de estruturas antigas: para um banco novo, configure um novo caminho em `SQLITE_PATH`.

## Configuração MySQL

Instale ou disponibilize um servidor MySQL e crie previamente o banco de dados. Defina as variáveis no ambiente de execução, sem gravar credenciais no código nem versioná-las:

```text
APP_DB_MODE=mysql
MYSQL_HOST=seu-host
MYSQL_PORT=3306
MYSQL_DATABASE=preparatorio_ufsc
MYSQL_USER=usuario
MYSQL_PASSWORD=senha
```

Também é possível fornecer a conexão completa por `MYSQL_URL`, por exemplo `mysql+pymysql://usuario:senha@host:3306/preparatorio_ufsc`. Quando usuário ou senha contiverem caracteres especiais, prefira as variáveis separadas, que são codificadas com segurança pelo SQLAlchemy.

O programa cria tabelas ausentes ao iniciar, mas não executa migrações para alterações futuras de esquema. Para produção, planeje migrações antes de atualizar tabelas que já contenham dados.

## Deploy futuro no Streamlit Community Cloud

1. Publique o repositório no GitHub sem `.env`, arquivos de banco de dados ou credenciais.
2. Crie o app no [Streamlit Community Cloud](https://share.streamlit.io/) e indique `src/app.py` como arquivo principal.
3. Configure `APP_DB_MODE=mysql` e as credenciais MySQL nos **Secrets** do app. É possível informar os valores em formato plano:

   ```toml
   APP_DB_MODE = "mysql"
   MYSQL_HOST = "seu-host"
   MYSQL_PORT = "3306"
   MYSQL_DATABASE = "preparatorio_ufsc"
   MYSQL_USER = "usuario"
   MYSQL_PASSWORD = "senha"
   ```

   Também é aceito um bloco `[database]` com essas mesmas chaves. A instância MySQL deve ser acessível pela aplicação hospedada.
4. Mantenha `uv.lock` versionado para instalações reproduzíveis. O sistema está preparado para receber configurações pelos Secrets; o SQLite local do Community Cloud não deve ser tratado como armazenamento permanente.

## Regras relevantes

- CPF e e-mail são únicos dentro de cada cadastro (alunos e professores).
- Matrícula ativa só pode ser criada para aluno, turma e plano válidos; aluno não pode ter duas matrículas ativas na mesma turma e a capacidade máxima é respeitada.
- O horário de início de uma aula deve preceder o encerramento e o professor não pode ter aulas agendadas em horários sobrepostos.
- A frequência exige matrícula ativa do aluno na turma da aula.
- Excluir pelo sistema marca o registro como excluído; os dados podem ser consultados e restaurados. Resultados não dependem da permanência de uma matrícula ativa e ficam associados ao aluno e ao simulado.
