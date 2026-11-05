import mysql.connector
import pandas as pd


def db_conn(warehouse=None):
    connection = mysql.connector.connect(
        user="root",
        password="root",
        host="localhost",  # For instances that run on the same machine as the client
        port=3306  # Use port 4566 for non-SSL, 443 for SSL connections
    )
    return connection


def execute(sql_str):
    statements = sql_str.strip().split(';')
    conn = db_conn()
    cur = conn.cursor()
    for s in statements:
        cur.execute(s)
        conn.commit()


def load_df(sql):
    conn = db_conn()
    return pd.read_sql(sql, conn)