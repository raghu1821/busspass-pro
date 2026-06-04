import mysql.connector
import os

print("Connecting to TiDB...")
db = mysql.connector.connect(
    host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    user="iSHHmk7WSpBUcMH.root",
    password="p1baf55QoBAxlooP",
    database="sys",
    port=4000,
    ssl_disabled=False,
    ssl_verify_cert=False,
    ssl_verify_identity=False
)

cursor = db.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS buspassdb;")
cursor.execute("USE buspassdb;")

with open("buspassdb_backup.sql", "r", encoding="utf-16") as f:
    sql_script = f.read()

# Split the statements (simple split, not perfect but usually works for mysqldump)
# mysqldump usually separates commands by ; at the end of the line
statements = sql_script.split(';')

for statement in statements:
    if statement.strip():
        try:
            cursor.execute(statement)
        except Exception as e:
            pass # Ignore drops and existing table errors

db.commit()
print("Import complete!")
