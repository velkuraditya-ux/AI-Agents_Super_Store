# AI-Agents_Super_Store

For Output, please check AI_Agents_Task.pdf

#  LangChain SQL Agents (Streamlit + Groq)

This repo contains **Streamlit apps + ingestion script** powered by **LangChain** + **Groq LLMs** to query, manage, and escalate data in **MySQL / SQLite** databases.

---

##  Components

### 1.  Data Ingestion (`data-ingestion.py`)
- Reads all sheets from an Excel file.
- Pushes each sheet as a **table in MySQL Workbench**.
- Automates DB setup for the agents.

### 2. Data Access Agent (`agent-1.py`)
- Works with **SQLite (`student.db`)** or **MySQL**.
- Conversational SQL agent across 7 business tables.
- Natural language → **valid MySQL SQL**.

# Note:
I have created 2 different kinds of applications for 2nd Agent (Customer Success Agent) 

### 3. Customer Success Agent (`agent-2.py`)
- Simple CRUD Application (No Chat UI, Non Agentic AI Application)
- Restricted to **`orders_2` table** in `super_market` schema.
- Supports **SELECT / INSERT / UPDATE / DELETE**.
- Enforces **30-day return policy** for returns.

### 4. Customer Success Agent (`agent-2-new.py`)
- Chatbot (Agentic AI Application)
- Restricted to **`orders_2` table** in `super_market` schema.
- Supports **SELECT / INSERT / UPDATE / DELETE**.
- Enforces **30-day return policy** for returns.

### 5. Human Resource Agent (`agent-3.py`)
- Automates **issue escalation** using hierarchy:



