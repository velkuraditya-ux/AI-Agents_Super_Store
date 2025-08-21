import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq

# -------------------------------
# Streamlit Config
# -------------------------------
st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

radio_opt = ["Use SQLite (student.db)", "Connect to MySQL Workbench"]
selected_opt = st.sidebar.radio("Choose the DB:", options=radio_opt)

if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("MySQL Host", value="localhost")
    mysql_user = st.sidebar.text_input("MySQL User", value="root")
    mysql_password = st.sidebar.text_input("MySQL Password", type="password")
    mysql_db = st.sidebar.text_input("MySQL Database")
else:
    db_uri = LOCALDB

api_key = st.sidebar.text_input("Groq API Key", type="password")

if not db_uri:
    st.info("Please enter the database information and URI")

if not api_key:
    st.info("Please add the Groq API key")

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
    if db_uri == LOCALDB:
        dbfilepath = (Path(__file__).parent / "student.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        # IMPORTANT: give access to ALL tables in the database
        engine = create_engine(
            f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
        )
        return SQLDatabase(engine, include_tables=None)  
        # include_tables=None → agent can use ALL tables

if db_uri == MYSQL:
    db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
else:
    db = configure_db(db_uri)

# -------------------------------
# System Prompt (schema-aware)
# -------------------------------
system_prompt = """You are an AI SQL Agent that answers natural language questions by generating SQL queries on a MySQL database. 
The database contains the following tables and their purposes:

1. orders - Contains customer details and order details. Tracks what orders each customer has placed.
2. regional_managers - Contains manager names for the four regions: West, East, Central, and South.
3. returns - Contains order IDs and information about whether a product was returned or not.
4. state_managers - Contains manager names for each U.S. state.
5. segment_managers - Contains customer segments (Consumer, Home Office, Corporate) and their respective managers.
6. category_managers - Contains product categories (Technology, Furniture, Office Supplies) and their respective managers.
7. customer_success_managers - Contains regions (Central, East, South, West) and their respective customer success managers.

Your task:
- Always generate valid MySQL SQL queries based on user questions.
- Use the correct table names and columns logically based on the table descriptions above.
- If multiple tables could be relevant, infer reasonable join logic based on business context (e.g., linking orders with returns or managers).
- Never hallucinate columns or tables not listed above.
- Execute the SQL queries against the database to fetch results.
"""

# -------------------------------
# Agent Setup
# -------------------------------
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# -------------------------------
# Chat UI
# -------------------------------
if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input(placeholder="Ask anything from the database")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())

        # Prepend system prompt to user query
        full_query = system_prompt + "\nUser question: " + user_query

        # Let the agent run across all tables with system prompt context
        response = agent.run(full_query, callbacks=[streamlit_callback])

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)
