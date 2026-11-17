import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

with psycopg.connect(
    host="localhost",
    port=5432,
    dbname="tennis_fantasy",
    user="postgres",
    password=os.environ["DB_PASSWORD"],
    connect_timeout=10,
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("""
        INSERT INTO players(id, name, tour, ranking)
        VALUES(%s,%s,%s,%s);
        """,
        ("sr:competitor:407573", "Carlos Alcaraz", "ATP", 3))

        cursor.execute("SELECT * from players")
        players = cursor.fetchall()
        print(players)