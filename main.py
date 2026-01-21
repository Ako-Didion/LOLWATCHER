import os
import time
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import aiohttp

@dataclass
class t_mastery:
    name: str
    level: int
    points: int
    last_play: float
    champImageUrl : str
    
    
@dataclass
class MatchStats:
    # Identité
    champion_id: int
    champion_name: str
    position: str
    
    # Résultat
    win: bool
    duration_ss: int  # Durée en secondes
    
    # KDA
    kills: int
    deaths: int
    assists: int
    
    # Économie
    gold_earned: int
    gold_spent: int
    total_cs: int      # Minions + Jungle
    
    # Combat & Vision
    damage_dealt: int
    damage_taken: int
    vision_score: int

    # Méthodes de calcul automatique (Pratique pour les moyennes)
    @property
    def kda(self):
        # On évite la division par zéro si 0 morts
        return (self.kills + self.assists) / max(1, self.deaths)

    @property
    def gold_per_minute(self):
        return self.gold_earned / (self.duration_ss / 60)

# /D:/Iut/lolWatcher/main.py
# Simple Riot API client to fetch a summoner and their recent matches.
# Requires: pip install requests
# Set your Riot API key in the environment variable RIOT_API_KEY
    
load_dotenv()

API_KEY = os.getenv("RIOT_API_KEY")
if not API_KEY:
    raise SystemExit("Please set RIOT_API_KEY environment variable")

# CORRECTED: Riot utilise 'X-Riot-Token' au lieu de 'Authorization'
headers = {
    "X-Riot-Token": API_KEY
}

# CORRECTED: Utilise l'URL du serveur régional (americas, europe, ou asia)
# Pour les comptes Riot ID, c'est généralement 'europe' ou 'americas'
REGION_URL = "https://europe.api.riotgames.com"
LOL_URL = "https://euw1.api.riotgames.com/lol"

gameName = "ChampiFou"
tagLine = "CRAZY"

# Construction de l'URL finale
url = REGION_URL

dataChampion = (requests.get("https://ddragon.leagueoflegends.com/cdn/16.1.1/data/fr_FR/champion.json")).json()

nameKey = list(dataChampion["data"].keys())
champIdAndInfo = []

for name in nameKey:
    champ_id = int(dataChampion["data"][name]["key"])
    champImageUrl = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{name}_0.jpg"
    # On ajoute une petite liste [ID, Nom] à chaque fois
    champIdAndInfo.append([champ_id, name, champImageUrl])

# Pour trier par ID (très facile avec cette structure) :
champIdAndInfo.sort()

def time_past_in_hour(timestamp_ms):
    diff_secondes = (datetime.now().timestamp()) - (timestamp_ms / 1000)
    heures_totale = diff_secondes // 3600
    
    return heures_totale

def get_puuid(gameName,tagLine):
    endPointForPuuid = f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}" 
    url = REGION_URL+endPointForPuuid    
    response = requests.get(url, headers=headers)
    if(response.status_code == 200):
        dataPuuid = response.json()
        print(dataPuuid["puuid"])
    else:
        print(f"le joueur :{gameName}#{tagLine} N'est pas dans la base de donées en Europe")
    return dataPuuid["puuid"]
    
    
def get_the_masteries(puuid):
    endPoinForMasteries = f"/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=5"
    url = LOL_URL+endPoinForMasteries
    response = requests.get(url,headers=headers)
    if(response.status_code == 200):
        dataMasteries = response.json()
    else:
        print(f"Erreur dans la récuperation des masteries du joueur :{gameName}#{tagLine}")
    return dataMasteries


def treats_masteries_information(champMasteries,champIdAndInfo):
    longeurMasteries = len(champMasteries)
    longeurChamp = len(champIdAndInfo)
    tabChampsBestMasteries = []
    for i in range(longeurMasteries):
        trouve=0
        j=0
        while j<longeurChamp and trouve==0:
            if(int(champMasteries[i]["championId"]) == int(champIdAndInfo[j][0])):
                nameC=champIdAndInfo[j][1]
                ChampsBestMasteries = t_mastery(name=nameC,level=champMasteries[i]["championLevel"],
                                                points=champMasteries[i]["championPoints"],
                                                last_play=time_past_in_hour(champMasteries[i]["lastPlayTime"]),
                                                champImageUrl=champIdAndInfo[j][2])
                tabChampsBestMasteries.append(ChampsBestMasteries)
            j=j+1
    return tabChampsBestMasteries

def get_id_recents_games(puuid):
    endPointForMatch=f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"
    url = REGION_URL+endPointForMatch
    response = requests.get(url,headers=headers)
    if(response.status_code == 200):
        dataGames = response.json()
    else:
        print(f"Erreur dans la récuperation des matchs du joueur :{gameName}#{tagLine}")
    return dataGames



import asyncio
import aiohttp

# 1. Fonction pour récupérer UN SEUL match
async def fetch_one_match(session, match_id, puuidJoueur):
    url = f"{REGION_URL}/lol/match/v5/matches/{match_id}"
    
    # On utilise la session partagée pour faire la requête
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            return None
        
        match = await response.json()
        participants = match["info"]["participants"]

        for p in participants:
            if p["puuid"] == puuidJoueur:
                # On retourne l'objet MatchStats
                return MatchStats(
                    champion_id=p["championId"],
                    champion_name=p["championName"],
                    position=p["individualPosition"],
                    win=p["win"],
                    duration_ss=p["timePlayed"],
                    kills=p["kills"],
                    deaths=p["deaths"],
                    assists=p["assists"],
                    gold_earned=p["goldEarned"],
                    gold_spent=p["goldSpent"],
                    total_cs=p["totalMinionsKilled"] + p["neutralMinionsKilled"],
                    damage_dealt=p["totalDamageDealtToChampions"],
                    damage_taken=p["totalDamageTaken"],
                    vision_score=p["visionScore"]
                )
    return None

# 2. Fonction principale asynchrone
async def analyse_recent_games_async(recentsGames, puuidJoueur):
    # On crée une session unique pour toutes les requêtes (plus rapide)
    async with aiohttp.ClientSession() as session:
        tasks = []
        for match_id in recentsGames:
            # On prépare la tâche sans la lancer
            tasks.append(fetch_one_match(session, match_id, puuidJoueur))
        
        # On lance TOUTES les tâches en parallèle et on attend les résultats
        results = await asyncio.gather(*tasks)
        
        # On filtre les résultats pour enlever les éventuels "None" (erreurs)
        return [r for r in results if r is not None]

async def main():
    puuid = get_puuid(gameName,tagLine)
    champMasteries = get_the_masteries(puuid)
    tabChampsBestMasteries = treats_masteries_information(champMasteries,champIdAndInfo)
    idGames = get_id_recents_games(puuid)
    tabMatchStats = await analyse_recent_games_async(idGames, puuid)
    print(tabMatchStats[0])
    pass


if __name__ == "__main__":
    asyncio.run(main())
    






