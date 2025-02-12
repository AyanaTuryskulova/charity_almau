import sqlite3


conn = sqlite3.connect("donations.db")
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    description TEXT,
    photo TEXT
)
''')

conn.commit()
conn.close()

def add_donation(user_id, description, photo):
    conn = sqlite3.connect("donations.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO donations (user_id, description, photo) VALUES (?, ?, ?)", (user_id, description, photo))
    conn.commit()
    conn.close()

def get_all_donations():
    conn = sqlite3.connect("donations.db")
    cursor = conn.cursor()
    cursor.execute("SELECT description, photo FROM donations")
    items = cursor.fetchall()
    conn.close()
    return items
