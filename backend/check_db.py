import sqlite3
con = sqlite3.connect("app.db")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("TABLES:", [r[0] for r in cur.fetchall()])
