from fastapi import FastAPI, Query, HTTPException
from typing import Annotated, Literal
import requests
from dotenv import load_dotenv
import os
import psycopg
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

sports_api = os.getenv("SPORTSAPI")
db_pw = os.getenv("DB_PASSWORD")

def fetch_api():
    url = "https://api.sportradar.com/tennis/trial/v3/en/rankings.json"
    headers = {
        "accept": "application/json",
        "x-api-key": sports_api,
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data

class Teams(BaseModel):
    team: str

@app.get("/")
async def root():
    return {"message": "Welcome to Tennis Fantasy Simulator"}

@app.get("/ranking")
def get_ranking(tour: Annotated[Literal["ATP","WTA"], Query()] = "ATP", limit: Annotated[int, Query(ge=1, le=100)] = 100):
    data = fetch_api()
    name = []
    for rank in data["rankings"]:
        if(rank["name"] == tour):
            for player in rank["competitor_rankings"]:
                if(player["rank"] <= limit):
                    name.append({
                        "id":  player["competitor"]["id"],
                        "rank":  player["rank"],
                        "name": player["competitor"]["name"]
                    })
    return name

@app.get("/players")
def get_players():
    with psycopg.connect(dbname="tennis_fantasy",
    user="postgres",
    password=db_pw,
    host="localhost",
    port=5432) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT id, name, tour, ranking 
            FROM players
            ORDER BY ranking
            """)
            rows = cur.fetchall()
    players = []
    for player in rows:
        players.append({
            "id": player[0],
            "name": player[1],
            "tour": player[2],
            "ranking": player[3]
        })  
    return players

@app.get("/players/{id}")
def get_players(id:str):
    with psycopg.connect(dbname="tennis_fantasy",
    user="postgres",
    password=db_pw,
    host="localhost",
    port=5432) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            SELECT id, name, tour, ranking 
            FROM players
            WHERE id = %s
            """, (id,))
            row = cur.fetchone()
            if row == None:
                raise HTTPException(status_code=404, detail="Item not found")
    return row

@app.post("/players")
def insert_players(limit: Annotated[int, Query(ge=1,le=100)] = 100, tour: Annotated[Literal["ATP","WTA"],Query()] = "ATP"):
    data = fetch_api()  
    count = 0
    with psycopg.connect(dbname="tennis_fantasy",
        user="postgres",
        password=db_pw,
        host="localhost",
        port=5432) as conn:
            with conn.cursor() as cur:
                for rank in data["rankings"]:
                    if rank["name"] == tour:
                        for player in rank["competitor_rankings"]:
                            if player["rank"] <= limit:
                                count += 1
                                cur.execute("""
                                INSERT INTO players(id,name,tour,ranking)
                                VALUES(%s,%s,%s,%s) ON CONFLICT(id) DO UPDATE SET
                                    ranking = EXCLUDED.ranking,
                                    name = EXCLUDED.name,
                                    tour = EXCLUDED.tour
                                """,(player["competitor"]["id"], player["competitor"]["name"], rank["name"], player["rank"]))
    return {"saved": count}

@app.post("/teams", status_code=201)
def insert_teams(name:Teams):
    new_team = name.model_dump()
    if len(name.team) > 50:
        raise HTTPException(status_code=400,detail="Team name is too long, must be under 50 characters")
    with psycopg.connect(dbname="tennis_fantasy",
        user="postgres",
        password=db_pw,
        host="localhost",
        port=5432) as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO teams(team)
            VALUES(%s)
            RETURNING id, team
            """, (name.team,))
            row = cur.fetchone()
    return {"id": row[0], "team": row[1]}