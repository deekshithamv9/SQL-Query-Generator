import json
import streamlit as st
import requests
import google.generativeai as genai
import re
from backend_config import BACKEND_URL, GEMINI_API_KEY

st.set_page_config(page_title="AI SQL Generator & Executor", layout="wide")
genai.configure(api_key=GEMINI_API_KEY)

def clean_sql_query(sql_text):
    """Clean and optimize the generated SQL query"""
    if not sql_text:
        return sql_text
    
    # Remove markdown code blocks
    sql_text = re.sub(r'^```sql\s*\n?', '', sql_text, flags=re.IGNORECASE | re.MULTILINE)
    sql_text = re.sub(r'^```\s*\n?', '', sql_text, flags=re.MULTILINE)
    sql_text = re.sub(r'\n?```$', '', sql_text, flags=re.MULTILINE)
    
    # Remove leading/trailing whitespace and newlines
    sql_text = sql_text.strip()
    
    # Remove extra newlines and normalize spacing
    sql_text = re.sub(r'\n\s*\n', '\n', sql_text)
    sql_text = re.sub(r'\s+', ' ', sql_text)
    
    # Ensure the query ends with semicolon
    if not sql_text.endswith(';'):
        sql_text += ';'
    
    return sql_text

def validate_sql_syntax(sql_text):
    """Basic SQL syntax validation"""
    sql_upper = sql_text.upper().strip()
    
    # Check for common SQL keywords
    valid_starts = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'SHOW', 'DESCRIBE', 'EXPLAIN']
    
    if not any(sql_upper.startswith(keyword) for keyword in valid_starts):
        return False, "Query doesn't start with a valid SQL keyword"
    
    # Check for balanced parentheses
    if sql_text.count('(') != sql_text.count(')'):
        return False, "Unbalanced parentheses in query"
    
    # Check for balanced quotes
    single_quotes = sql_text.count("'") - sql_text.count("\\'")
    if single_quotes % 2 != 0:
        return False, "Unbalanced single quotes in query"
    
    return True, "Query syntax appears valid"

def fix_sql_with_ai(original_query, error_message, schema, db_name, original_request):
    """Ask Gemini to fix the SQL query based on error message"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        fix_prompt = (
            "You are a MySQL 8 expert. The following SQL query failed with an error. "
            "Fix the query and return ONLY the corrected SQL statement (no explanations, no markdown).\n\n"
            f"Original Request: {original_request}\n"
            f"Failed Query: {original_query}\n"
            f"Error Message: {error_message}\n"
            f"Database: {db_name}\n"
            f"Schema: {json.dumps(schema) if schema else 'Not available'}\n\n"
            "Requirements:\n"
            "- Fix the specific error mentioned\n"
            "- Use proper MySQL syntax and backticks for identifiers\n"
            "- Use efficient JOINs, proper indexing, and GROUP BY when needed\n"
            "- Return ONLY the corrected SQL query\n\n"
            "Corrected SQL:"
        )
        
        response = model.generate_content(fix_prompt)
        fixed_sql = clean_sql_query(response.text.strip())
        return fixed_sql
        
    except Exception as e:
        return None

# ---- Sidebar: DB Explorer ----
with st.sidebar:
    st.header("📂 Database Explorer")

    if st.button("🔍 List Databases"):
        try:
            dbs = requests.get(f"{BACKEND_URL}/list_dbs", timeout=10).json()
            st.session_state["dbs"] = dbs
        except Exception as e:
            st.error(e)

    dbs = st.session_state.get("dbs", [])
    if dbs:
        st.write(dbs)

    db_name = st.text_input("Database name", value="employee_mgmt")

    if st.button("📁 Show Tables"):
        try:
            schema = requests.get(f"{BACKEND_URL}/schema", params={"db": db_name}, timeout=20).json()
            st.session_state["schema"] = schema
        except Exception as e:
            st.error(e)

    schema = st.session_state.get("schema")
    if schema:
        tables = list(schema["tables"].keys())
        st.write("**Tables:**", tables)

    table_name = st.text_input("Table name")
    if st.button("📄 Show Columns"):
        if table_name:
            try:
                cols = requests.get(
                    f"{BACKEND_URL}/columns",
                    params={"db": db_name, "table": table_name},
                    timeout=15,
                ).json()
                st.session_state["cols"] = cols
            except Exception as e:
                st.error(e)

    if "cols" in st.session_state:
        st.write("**Columns in table:**")
        st.json(st.session_state["cols"])

# ---- Main: Header ----
st.title("🧠 AI-Powered SQL Query Generator & Executor")
st.caption("Type plain English → get SQL (Gemini) → run on MySQL → see results → short explanation.")

col_main, = st.columns([1])

# ---- Section: Generate SQL ----
st.subheader("🤖 AI-Powered SQL Generation")
english = st.text_area("Enter your query in plain English:", height=110, placeholder="e.g., list employee names and emails hired after 2022...")

if st.button("Generate SQL"):
    if not english:
        st.warning("Please enter a request in English.")
    else:
        # Give model the schema for better accuracy
        schema = st.session_state.get("schema")
        if not schema:
            # fetch once if not present
            try:
                schema = requests.get(f"{BACKEND_URL}/schema", params={"db": db_name}, timeout=20).json()
            except Exception as e:
                st.error(e)
                schema = None

        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Enhanced prompt for cleaner SQL generation
        prompt = (
            "You are a MySQL 8 SQL expert. Generate ONLY a clean, executable SQL statement. "
            "Requirements:\n"
            "- NO markdown formatting, NO code blocks, NO explanations\n"
            "- Return ONLY the raw SQL query\n"
            "- Use proper MySQL syntax and backticks for identifiers when needed\n"
            "- Use proper INDEXING hints when needed for performance\n"
            "- Use efficient JOINS instead of subqueries when possible\n"
            "- Use GROUP BY when aggregations are needed\n"
            "- Optimize for performance and readability\n"
            "- Ensure the query is complete and executable\n"
            f"Database: {db_name}\n"
            f"Schema: {json.dumps(schema) if schema else 'Not available'}\n"
            f"User request: {english}\n"
            "SQL Query:"
        )
        
        try:
            resp = model.generate_content(prompt)
            raw_sql = resp.text.strip()
            
            # Clean the generated SQL
            cleaned_sql = clean_sql_query(raw_sql)
            
            # Validate syntax
            is_valid, validation_msg = validate_sql_syntax(cleaned_sql)
            
            st.session_state["generated_sql"] = cleaned_sql
            st.session_state["sql_validation"] = {"is_valid": is_valid, "message": validation_msg}
            st.session_state["original_english_request"] = english  # Store for error fixing
            
        except Exception as e:
            st.error(f"Error generating SQL: {str(e)}")

if "generated_sql" in st.session_state:
    # Show validation status
    validation = st.session_state.get("sql_validation", {})
    if validation.get("is_valid"):
        st.success(f"✅ {validation.get('message', 'SQL generated successfully')}")
    else:
        st.warning(f"⚠️ {validation.get('message', 'Please review the generated SQL')}")
    
    st.code(st.session_state["generated_sql"], language="sql")
    
    # Show original vs cleaned comparison if there were changes
    if st.checkbox("Show cleaning details"):
        st.text("This helps debug any formatting issues that were automatically fixed.")

# ---- Section: Execute SQL ----
st.subheader(" Execute SQL Query")
default_sql = st.session_state.get("generated_sql", "")
sql_to_run = st.text_area("Enter SQL to execute:", value=default_sql, height=140)

# Real-time SQL validation
if sql_to_run:
    is_valid, msg = validate_sql_syntax(sql_to_run)
    if is_valid:
        st.success(f"✅ {msg}")
    else:
        st.error(f"❌ {msg}")

if st.button("▶️ Execute"):
    if not sql_to_run:
        st.warning("Enter a SQL query first.")
    else:
        # Final cleaning before execution
        final_sql = clean_sql_query(sql_to_run)
        
        try:
            resp = requests.post(
                f"{BACKEND_URL}/execute",
                json={"query": final_sql, "db": db_name},
                timeout=60,
            ).json()
            
            if resp.get("success"):
                if resp.get("type") == "resultset":
                    st.success("Query executed successfully!")
                    df = resp["data"]
                    st.dataframe(df)
                    
                    # Show result summary and download option
                    if df:
                        st.info(f"Retrieved {len(df)} rows")
                        
                        # Convert dataframe to CSV for download
                        import pandas as pd
                        if isinstance(df, list) and df:
                            # Convert list of dicts to DataFrame
                            df_for_download = pd.DataFrame(df)
                        else:
                            df_for_download = pd.DataFrame(df) if df else pd.DataFrame()
                        
                        if not df_for_download.empty:
                            csv_data = df_for_download.to_csv(index=False)
                            st.download_button(
                                "⬇️ Download Results (CSV)",
                                data=csv_data,
                                file_name=f"query_results_{db_name}.csv",
                                mime="text/csv",
                            )
                else:
                    st.success(f"✅ Query executed. Rows affected: {resp.get('rows_affected', 0)}")
            else:
                error_msg = resp.get("error", "Unknown error")
                st.error(f"❌ Execution failed: {error_msg}")
                
                # Store error details for potential fixing
                st.session_state["last_error"] = {
                    "query": final_sql,
                    "error": error_msg,
                    "original_request": st.session_state.get("original_english_request", "")
                }
                
                # Suggest common fixes
                if "syntax error" in error_msg.lower():
                    st.info(" Try checking for missing semicolons, unmatched quotes, or typos in table/column names.")
                elif "doesn't exist" in error_msg.lower():
                    st.info(" Check if table/column names are correct. Use the Database Explorer to verify.")
                elif "access denied" in error_msg.lower():
                    st.info(" Check database permissions or connection settings.")
                
                # Auto-fix option
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🤖 Ask AI to Fix This Error"):
                        with st.spinner(" AI is analyzing and fixing the error..."):
                            schema = st.session_state.get("schema")
                            if not schema:
                                try:
                                    schema = requests.get(f"{BACKEND_URL}/schema", params={"db": db_name}, timeout=20).json()
                                except:
                                    schema = None
                            
                            fixed_sql = fix_sql_with_ai(
                                final_sql, 
                                error_msg, 
                                schema, 
                                db_name, 
                                st.session_state.get("original_english_request", "")
                            )
                            
                            if fixed_sql:
                                st.session_state["generated_sql"] = fixed_sql
                                st.success(" AI has generated a fixed query! Check the 'Execute SQL Query' section above.")
                                st.info(" The fixed query has been updated above. Click 'Execute' to try again.")
                                # Auto-scroll suggestion
                                st.markdown(" **Scroll up to see the fixed query**")
                            else:
                                st.error("❌ AI couldn't generate a fix. Try rephrasing your original request.")
                
                with col2:
                    if st.button("📝 Edit Query Manually"):
                        st.info(" You can edit the SQL directly in the text area above and try again.")
                
        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")

# ---- Section: Explain SQL ----
if sql_to_run:
    st.subheader("💡 Query Explanation")
    
    if st.button("Explain Query"):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            explanation_prompt = (
                "Explain this SQL query in simple terms (2-3 sentences max). "
                "Focus on what data it retrieves/modifies and any important conditions:\n"
                f"{sql_to_run}"
            )
            exp = model.generate_content(explanation_prompt)
            st.info(f"📝 {exp.text}")
        except Exception as e:
            st.warning(f"Explanation unavailable: {str(e)}")

# ---- Footer ----
st.markdown("---")

# Show error history for debugging (collapsible)
if "last_error" in st.session_state:
    with st.expander("🔍 Last Error Details (for debugging)"):
        error_info = st.session_state["last_error"]
        st.text("Failed Query:")
        st.code(error_info["query"], language="sql")
        st.text("Error Message:")
        st.text(error_info["error"])
        st.text("Original Request:")
        st.text(error_info["original_request"])