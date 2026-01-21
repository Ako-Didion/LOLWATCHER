import os
from datetime import datetime
from dotenv import load_dotenv
import requests
from dataclasses import dataclass,field
import asyncio
import aiohttp
from typing import Dict, List
import json
from dataclasses import asdict

@dataclass
class t_mastery:
    name: str
    level: int
    points: int
    last_play: float
    champImageUrl : str
    
@dataclass
class joueur:
    name: str
    level: str
    profilePicture : str

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


@dataclass
class ChampionSummary:
    """Stocke la synthèse pour un champion précis"""
    name: str
    games: int = 0
    wins: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gold: int = 0
    cs: int = 0
    damage: int = 0

    @property
    def winrate(self) -> float:
        return (self.wins / self.games) * 100 if self.games > 0 else 0

    @property
    def kda(self) -> float:
        return (self.kills + self.assists) / max(1, self.deaths)

@dataclass
class GlobalReport:
    """Stocke le résultat final de toute l'analyse"""
    total_matches: int
    avg_gold: float
    avg_cs: float
    winrate_global: float
    # Dictionnaire liant le nom du champion à son objet ChampionSummary
    champions: Dict[str, ChampionSummary] = field(default_factory=dict)

@dataclass
class FinalExport:
    player_info: joueur
    masteries: List[t_mastery]
    match_report: GlobalReport
    
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

gameName = "cascade2chiasse"
tagLine = "caca"

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


def get_player_profile(puuid):
    endPointProfile = f"/summoner/v4/summoners/by-puuid/{puuid}"
    url = LOL_URL+endPointProfile
    response = requests.get(url,headers=headers)
    data = response.json()
    urlP = f"https://ddragon.leagueoflegends.com/cdn/16.2.1/img/profileicon/{data["profileIconId"]}.png"
    return joueur(name=gameName,level=data["summonerLevel"],profilePicture=urlP)
    
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
    endPointForMatch=f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=40"
    url = REGION_URL+endPointForMatch
    response = requests.get(url,headers=headers)
    if(response.status_code == 200):
        dataGames = response.json()
    else:
        print(f"Erreur dans la récuperation des matchs du joueur :{gameName}#{tagLine}")
    return dataGames

def analyze_to_class(tabMatchStats: List[MatchStats]) -> GlobalReport:
    # On filtre les remakes
    valid_matches = [m for m in tabMatchStats if m.duration_ss > 300]
    nb = len(valid_matches)
    
    if nb == 0:
        return None

    # Calculs globaux
    g_wins = sum(1 for m in valid_matches if m.win)
    g_gold = sum(m.gold_earned for m in valid_matches) / nb
    g_cs = sum(m.total_cs for m in valid_matches) / nb
    
    # Création de l'objet de rapport
    report = GlobalReport(
        total_matches=nb,
        avg_gold=g_gold,
        avg_cs=g_cs,
        winrate_global=(g_wins / nb) * 100
    )

    # Remplissage des stats par champion
    for m in valid_matches:
        if m.champion_name not in report.champions:
            report.champions[m.champion_name] = ChampionSummary(name=m.champion_name)
        
        c = report.champions[m.champion_name]
        c.games += 1
        c.wins += 1 if m.win else 0
        c.kills += m.kills
        c.deaths += m.deaths
        c.assists += m.assists
        c.gold += m.gold_earned
        c.cs += m.total_cs
        c.damage += m.damage_dealt

    return report

def save_report_to_json(report, filename="stats_result.json"):
    # asdict transforme récursivement l'objet et les sous-objets (champions) en dictionnaires
    report_dict = asdict(report)
    
    with open(filename, "w", encoding="utf-8") as f:
        # indent=4 permet de rendre le JSON lisible (pas tout sur une seule ligne)
        json.dump(report_dict, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Rapport sauvegardé avec succès dans {filename}")

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
            if p["puuid"] == puuidJoueur and match["info"]["gameMode"] == "CLASSIC":
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
    # 1. Récupération des données de base
    puuid = get_puuid(gameName, tagLine)
    player = get_player_profile(puuid)
    champMasteries = get_the_masteries(puuid)
    
    # 2. Traitement des maîtrises
    tabChampsBestMasteries = treats_masteries_information(champMasteries, champIdAndInfo)
    
    # 3. Récupération et analyse des matchs
    idGames = get_id_recents_games(puuid)
    tabMatchStats = await analyse_recent_games_async(idGames, puuid)
    report = analyze_to_class(tabMatchStats)
    
    # 4. Regroupement de TOUTES les données
    # On crée l'objet final qui contient tout
    final_data = FinalExport(
        player_info=player,
        masteries=tabChampsBestMasteries,
        match_report=report
    )
    
    # 5. Export en JSON
    save_report_to_json(final_data, filename=f"stats_{gameName}.json")

if __name__ == "__main__":
    asyncio.run(main())
    






