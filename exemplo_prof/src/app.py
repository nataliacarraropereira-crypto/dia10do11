import streamlit as st

st.set_page_config(
    page_title="Preparatório UFSC",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.database import init_db
from src.pages.crud import ENTITIES, render_crud
from src.pages.dashboard import render_dashboard

st.markdown(
    """
    <style>
    :root { --ink: #15324b; --accent: #0c7c75; }
    .stApp { background: #f5f8fb; color: var(--ink); }
    [data-testid="stSidebar"] { background: #eaf1f5; }
    [data-testid="stMetric"] {
        background: white; border: 1px solid #dce6ec; border-radius: 12px;
        padding: 16px 18px;
    }
    div[data-testid="stForm"] {
        background: white; border: 1px solid #dce6ec; border-radius: 12px;
        padding: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

home = st.Page(render_dashboard, title="Visão geral", icon="🎓", default=True)
crud_pages = [
    st.Page(
        lambda key=entity_key: render_crud(key),
        title=config["label"],
        url_path=entity_key,
        icon="📝",
    )
    for entity_key, config in ENTITIES.items()
]
navigation = st.navigation({"Início": [home], "Gestão acadêmica": crud_pages})
navigation.run()
