# app_orders2_agent.py
import os
import streamlit as st
from sqlalchemy import create_engine, text
from langchain.agents import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.callbacks import StreamlitCallbackHandler
from langchain.sql_database import SQLDatabase
from langchain_groq import ChatGroq


# ==============================
# Streamlit UI
# ==============================
st.set_page_config(page_title="Orders_2 SQL Agent", page_icon="🛒", layout="wide")
st.title("🛒 SQL Agent for `orders_2` table (MySQL)")

with st.sidebar:
    st.header("🔧 Configuration")

    # ---- DB connection inputs
    db_host = st.text_input("MySQL Host", value="localhost")
    db_port = st.number_input("MySQL Port", value=3306, step=1)
    db_user = st.text_input("MySQL User", value="root")
    db_password = st.text_input("MySQL Password", value="1a0qaeta", type="password")
    db_name = st.text_input("Database (Schema)", value="super_market")

    st.markdown("---")
    # ---- Model settings
    groq_api_key = st.text_input("GROQ_API_KEY (env recommended)", value=os.getenv("GROQ_API_KEY", ""), type="password")
    model_name = st.selectbox(
        "Groq Model",
        options=[
            "Llama3-8b-8192",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ],
        index=0,
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)

    st.markdown("---")
    connect_btn = st.button("🔌 Connect / Reconnect")


# ==============================
# Build SQLAlchemy Engine
# ==============================
def build_connection_url(user: str, pwd: str, host: str, port: int, db: str) -> str:
    return f"mysql+mysqlconnector://{user}:{pwd}@{host}:{port}/{db}"

def make_engine() -> SQLDatabase | None:
    try:
        url = build_connection_url(db_user, db_password, db_host, db_port, db_name)
        engine = create_engine(url, pool_pre_ping=True)
        # quick smoke test
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return SQLDatabase(engine, include_tables=["orders_2"])
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        return None


# Maintain connection/model in session
if connect_btn or "db" not in st.session_state:
    st.session_state.db = make_engine()

# LLM setup
if "llm" not in st.session_state or connect_btn:
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    try:
        st.session_state.llm = ChatGroq(model_name=model_name, temperature=temperature)
    except Exception as e:
        st.error(f"❌ Could not initialize Groq LLM: {e}")
        st.stop()

# Agent setup
def make_agent(db: SQLDatabase):
    toolkit = SQLDatabaseToolkit(db=db, llm=st.session_state.llm)
    return create_sql_agent(
        llm=st.session_state.llm,
        toolkit=toolkit,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
    )

if st.session_state.get("db") is None:
    st.stop()

agent = make_agent(st.session_state.db)

# ==============================
# Schema Panel
# ==============================
with st.expander("📚 orders_2 schema", expanded=True):
    try:
        info = st.session_state.db.get_table_info(["orders_2"])
        st.code(info, language="sql")
    except Exception as e:
        st.warning(f"Could not load schema details: {e}")

# ==============================
# Sample Prompts
# ==============================
st.markdown(
    """
**Example prompts (for `orders_2` only):**
- *Show all undelivered orders.*
- *Insert a new order for Customer_ID `C-5001`, Customer_Name `Alice Green`, Product `Office Chair`, Quantity `5`.*
- *Update Alice Green’s order to 7 Office Chairs.*
- *Mark Customer_ID `C-5001` order as delivered.*
- *Return Alice Green’s order if within 30 days of purchase.*
- *Show top 5 products by total quantity ordered.*
- *How many orders were delivered in the last 30 days?*
    """
)

# ==============================
# Chat Interface
# ==============================
st.subheader("💬 Ask your question (restricted to orders_2)")

user_query = st.text_area(
    "Natural language to SQL (agent will generate & execute on orders_2):",
    height=120,
    placeholder="e.g., Return Alice Green’s order if eligible",
)

col_run, col_clear = st.columns([1, 1])
with col_clear:
    if st.button("Clear output"):
        st.session_state.pop("last_result", None)
        st.experimental_rerun()

with col_run:
    run_btn = st.button("Run", type="primary")

trace_area = st.container()
result_area = st.container()

if run_btn and user_query.strip():
    st_cb = StreamlitCallbackHandler(trace_area)

    guardrail = (
        "You are an SQL expert agent with full INSERT, UPDATE, DELETE, and SELECT rights "
        "on the MySQL table `orders_2` in schema `super_market`. "
        "Always generate valid SQL queries for this table and execute them. "
        "Rules:\n"
        "- The Delivered column can only be 'YES' or 'NO'.\n"
        "- For returns: validate if the Order_Date is within 30 days of today. "
        "Only then allow DELETE or mark as returned. If >30 days, politely deny.\n"
        "- Never refuse otherwise. If the user asks something outside orders_2, explain that "
        "you only manage this table.\n"
        "- Always output valid SQL query reasoning for LangChain execution."
    )

    try:
        prompt = f"{guardrail}\n\nUser question:\n{user_query}"
        response = agent.invoke({"input": prompt}, {"callbacks": [st_cb]})
        final_text = response.get("output", response)
        st.session_state.last_result = final_text
    except Exception as e:
        st.session_state.last_result = f"❌ Error: {e}"

if st.session_state.get("last_result"):
    with result_area:
        st.markdown("### ✅ Answer")
        st.write(st.session_state["last_result"])

# ==============================
# Footer
# ==============================
st.markdown("---")
st.caption(
    "This SQL Agent is restricted to the **orders_2** table only. "
    "It supports SELECT / INSERT / UPDATE / DELETE. "
    "Return requests are validated against a 30-day return policy."
)
