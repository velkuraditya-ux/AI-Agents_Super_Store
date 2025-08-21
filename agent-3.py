import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="HR Escalation Agent", page_icon="📩")
st.title("📩 HR Escalation Agent")

# -------------------------------
# Sidebar - Database Connection
# -------------------------------
MYSQL = "USE_MYSQL"
radio_opt = ["Use SQLite (demo.db)", "Connect to MySQL Workbench"]
selected_opt = st.sidebar.radio("Choose the DB:", options=radio_opt)

if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("MySQL Host", value="localhost")
    mysql_user = st.sidebar.text_input("MySQL User", value="root")
    mysql_password = st.sidebar.text_input("MySQL Password", type="password")
    mysql_db = st.sidebar.text_input("MySQL Database")
else:
    db_uri = "USE_LOCALDB"

api_key = st.sidebar.text_input("Groq API Key", type="password")

if not db_uri or not api_key:
    st.info("Please enter DB info and API Key")

# -------------------------------
# LLM Model
# -------------------------------
llm = ChatGroq(
    groq_api_key=api_key,
    model_name="Llama3-8b-8192",
    streaming=True
)

# -------------------------------
# Database Connection
# -------------------------------
@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == "USE_LOCALDB":
        dbfilepath = (Path(__file__).parent / "demo.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri == MYSQL:
        engine = create_engine(
            f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
        )
        return SQLDatabase(engine, include_tables=None)  # agent can use all 7 tables

if db_uri == MYSQL:
    db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
else:
    db = configure_db(db_uri)

# -------------------------------
# Agent Setup
# -------------------------------
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
sql_agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# -------------------------------
# System Prompt with Hierarchy
# -------------------------------
system_prompt = """
You are an HR Escalation Agent.

Hierarchy (Top → Bottom):
1. Category Manager
2. Segment Manager
3. Regional Manager
4. State Manager
5. Customer

Rules:
- A Customer escalates to their State Manager.
- A State Manager escalates to their Regional Manager.
- A Regional Manager escalates to their Segment Manager.
- A Segment Manager escalates to their Category Manager.
- A Category Manager escalates to LOB/Executive (if available).

Steps:
1. Query the SQL DB for manager details (tables: category_managers, segment_managers, regional_managers, state_managers).
2. Identify the correct escalation target (manager role + name) based on hierarchy.
3. Generate a clear recommendation: "Escalate this issue to [Role: Name]".
4. Draft a polite escalation email addressed to that manager, including:
   - Sender name and role
   - Issue description
   - State (if applicable)
"""

# -------------------------------
# User Input Form
# -------------------------------
with st.form("hr_escalation_form"):
    user_name = st.text_input("Your Name")
    user_role = st.selectbox(
        "Your Role",
        ["Category Manager", "Segment Manager", "Regional Manager", "State Manager", "Customer"]
    )
    user_state = st.text_input("Your State (if applicable)")
    issue_desc = st.text_area("Describe the issue to escalate")
    submitted = st.form_submit_button("Submit Issue")

# -------------------------------
# Process Escalation
# -------------------------------
if submitted:
    st.write(f"📌 Thank you {user_name}, processing your escalation...")

    # Create structured query for the agent
    user_query = f"""
    SYSTEM PROMPT: {system_prompt}

    User Details:
    - Name: {user_name}
    - Role: {user_role}
    - State: {user_state}
    - Issue: {issue_desc}

    Task:
    - Identify escalation target (manager role + name) using DB + hierarchy.
    - Recommend escalation path.
    - Draft escalation email.
    """

    # Run SQL Agent with LLM reasoning
    response = sql_agent.run(user_query)

    st.subheader("📌 Escalation Recommendation")
    st.write(response)
