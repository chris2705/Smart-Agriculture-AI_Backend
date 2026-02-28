import sqlite3
conn = sqlite3.connect('sql_app.db')
cursor = conn.cursor()
try:
    cursor.execute("ALTER TABLE fields ADD COLUMN soil_type VARCHAR;")
    conn.commit()
    print("Table altered successfully")
except Exception as e:
    print(e)
conn.close()
