
import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
DB_URL = os.getenv("DB_URL")

def get_connection():
    return psycopg2.connect(DB_URL)

st.set_page_config(page_title="Reminder Manager", layout="wide")
st.title("🔔 Reminder Database Editor")

# --- EMERGENCY RESET BUTTON ---
with st.sidebar:
    st.warning("Database Connection Management")
    if st.button("🔴 Kill All Active Connections"):
        try:
            # We use a fresh connection just for this command
            conn = psycopg2.connect(DB_URL)
            conn.autocommit = True  # Required for termination commands
            with conn.cursor() as cur:
                # Note: We use your specific database name from the error message
                kill_query = """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'MyDatabase1_pickthrew'
                  AND pid <> pg_backend_pid();
                """
                cur.execute(kill_query)
                st.sidebar.success("All other connections closed!")
            conn.close()
        except Exception as e:
            st.sidebar.error(f"Could not reset: {e}")

# 1. Load Data
@st.cache_data(show_spinner=False)
def load_data():
    conn = get_connection()
    query = "SELECT id, reminder, reminder_date_arg_tz, activated FROM my_schema_1.reminders ORDER BY id ASC;"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Initialize Data in State
if "df" not in st.session_state:
    st.session_state.df = load_data()

# 2. The Data Editor
# We disable editing the 'id' column because it is managed by Postgres (Serial)
st.subheader("Edit Reminders")
edited_data = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "activated": st.column_config.CheckboxColumn("Activated"),
        "reminder_date_arg_tz": st.column_config.DatetimeColumn("Reminder Date")
    },
    key="editor_key",
    use_container_width=True
)

# 3. Handle Changes
if st.button("Save Changes"):
    # This dictionary tracks exactly what the user changed in the UI
    changes = st.session_state.editor_key
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Handle UPDATES
        for row_index, updated_values in changes["edited_rows"].items():
            row_id = st.session_state.df.iloc[row_index]["id"]
            for col, val in updated_values.items():
                # Note: Using f-string for column name is safe here as it's from our DB schema
                sql = f"UPDATE my_schema_1.reminders SET {col} = %s WHERE id = %s"
                cur.execute(sql, (val, int(row_id)))

        # Handle DELETIONS
        for row_index in changes["deleted_rows"]:
            row_id = st.session_state.df.iloc[row_index]["id"]
            cur.execute("DELETE FROM my_schema_1.reminders WHERE id = %s", (int(row_id),))

        # Handle ADDITIONS
        for row in changes["added_rows"]:
            cur.execute(
                "INSERT INTO my_schema_1.reminders (reminder, reminder_date_arg_tz, activated) VALUES (%s, %s, %s)",
                (row.get("reminder"), row.get("reminder_date_arg_tz"), row.get("activated", True))
            )

        conn.commit()
        st.success("Successfully updated database!")
        
        # Clear cache and state to refresh data from DB
        st.cache_data.clear()
        st.session_state.df = load_data()
        st.rerun()

    except Exception as e:
        conn.rollback()
        st.error(f"Error: {e}")
    finally:
        cur.close()
        conn.close()