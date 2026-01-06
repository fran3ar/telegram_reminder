import warnings
warnings.filterwarnings('ignore')

#%%
import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables desde .env
load_dotenv()

DB_URL = os.getenv("DB_URL")

#######
# --- EMERGENCY RESET BUTTON ---

try:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        kill_query = """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = 'MyDatabase1_pickthrew'
            AND pid <> pg_backend_pid();
        """
        cur.execute(kill_query)
        print("All other connections closed!")
    conn.close()
except Exception as e:
    print(f"Could not reset: {e}")
########

conn = psycopg2.connect(DB_URL)


#%%
import pandas as pd

def display_table(query):
    cursor = conn.cursor()
    try:
        query = query
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print("Error al mostrar la tabla:", e)
        return None
    finally:
        cursor.close()
        # NO cerramos conn aquí

def update_record(query, params=None):
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        conn.commit()
        print("Record updated successfully")
    except Exception as e:
        conn.rollback()
        print("Error updating record:", e)
    finally:
        cursor.close()

#%%

data1 = display_table("""                                        
SELECT *
FROM my_schema_1.reminders
WHERE activated = TRUE
"""
)


#%%

import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

def send_telegram_message(token, chat_id, text_msg):
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text_msg}
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None

#%%

from datetime import datetime
import time
now = datetime.now()

now_yyyymm = now.strftime("%Y-%m")

print(now_yyyymm)


#%%



for _, row in data1.iterrows():
    should_send = False
    frequency = row['frequency']

    day_of_week = row['day_of_week']
    day_value = row['day_value']
    month_value = row['month_value']
    year_value = row['year_value']
    hour_value = row['hour_value']
    minute_value = row['minute_value']
    last_completed_at = row['last_completed_at']
    print(last_completed_at)
    
    last_completed_at_yyyymm = last_completed_at.strftime("%Y-%m")

    chat_id = row['chat_id']
    reminder = row['reminder']
    print(f"frequency: {frequency}")
    print(f"id: {row['id']}")

    if frequency == "monthly" and round(day_value) <= now.day and last_completed_at_yyyymm != now_yyyymm:
        should_send = True
    
    if should_send:
        send_telegram_message(BOT_TOKEN, chat_id, reminder)
        print("Sent")

        now = datetime.now()

        query123 = """
        UPDATE my_schema_1.reminders
        SET last_completed_at = %s
        WHERE id = %s
        """

        update_record(query123, (now, row['id']))

        time.sleep(3)  # delays for 3 seconds

#%%

# Cerrar conexión al final
conn.close()