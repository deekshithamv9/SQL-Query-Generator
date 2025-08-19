# SQL Query Generator

## 📌 Project Overview

**SQL Query Generator** is a **Streamlit + Flask-based web application** that enables users to convert **natural language text** into **SQL queries** and execute them on a relational database.

Instead of writing complex SQL manually, users can simply type plain English commands such as:

* *“List all employees hired after 2022”*
* *“Show departments with more than 10 employees”*
* *“Find employees working on the ‘Website Revamp’ project”*

The system will then:

1.  **Generate** the SQL query automatically
2.  **Execute** it on the database
3.  **Display** the results in a simple, user-friendly interface
4.   Additionally, the system provides step-by-step **explanations** of the generated queries
---

## Features

* **Natural Language to SQL**: Convert plain English into SQL queries.
* **Database Explorer**: Visualize database, tables, and fields on the left panel.
* **One-click Copy**: Copy AI-generated SQL queries easily.
* **Query Execution**: Run SQL queries directly and display results in the UI.
* **AI Explanation**: Understand the query in simple English.
* **JOINs and Aggregates**: Supports complex SQL queries like joins, group by, and filters.

---

## Technologies and Libraries Used

### Backend

* **Flask** → REST API for DB connection and query execution.
* **MySQL** → Relational database (Employee Management System).
* **SQLAlchemy** → ORM and database handling.
* **Google Gemini AI API** → Convert English text into SQL queries.

### Frontend

* **Streamlit** → Interactive UI for text input, results, and DB explorer.
* **Pandas** → For displaying query results in tabular format.

---

## Code Structure

```
sql-query-generator/
│── backend/
│   ├── app.py                # Flask backend API
│   ├── db_config.py          # Database connection setup
│   └── requirements.txt      # Python dependencies
│
│── frontend/
│   ├── app.py                # Streamlit frontend UI
│   ├── utils.py              # Helper functions
│   └── assets/               # Screenshots, logos
│
│── .gitignore
│── README.md
│── LICENSE
```

---

## Installation and Setup

### Prerequisites

* Python 3.10+
* pip package manager
* GitHub account
* Google Gemini API key

### Steps

1. **Clone the repo**

   ```bash
   git clone https://github.com/deekshithamv9/SQL-Query-Generator.git
   cd SQL-Query-Generator
   ```

2. **Setup virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # (Linux/Mac)
   .venv\Scripts\activate      # (Windows)
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   Create a `.env` file inside the root folder:

   ```
   GEMINI_API_KEY=your_api_key_here
   DATABASE_URL=mysql+pymysql://user:password@localhost/employee_management
   ```

5. **Run Backend (Flask)**

   ```bash
   cd backend
   python app.py
   ```

6. **Run Frontend (Streamlit)**

   ```bash
   cd frontend
   streamlit run app.py
   ```

---

## How to Run the Project

1. Start Flask backend → connects to DB.
2. Run Streamlit frontend → open UI in browser.
3. Enter English text → see generated SQL query → execute → view results and explanation.

---

## Example Queries

* "List all employees who joined after 2022."
* "Find employees working in Engineering department and their projects."
* "Get employees and their manager names."
* "Show projects with no employees assigned."
* "List departments with average salary greater than 50,000."

---

## API Routes

* `POST /generate-sql` → Converts natural language to SQL.
* `POST /execute-sql` → Executes SQL query and returns results.
* `GET /db-schema` → Returns DB tables and fields.

---

## Screenshots

### Query Generation  
![Query Generation](frontend/assets/query_generate.png)  

### Query Display  
![Query Display](frontend/assets/query_display.png)  

### Query Execution  
![Query Execution](frontend/assets/query_execute.png)  

---

## License

This project is licensed under the **MIT License** 

---


