# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
from requests import get
from concurrent.futures import ThreadPoolExecutor
import asyncio
from random import randint

#Database connectie
db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
db.connect()

#creer een threadpool voor het multithreaden van planningen berekenen
executor = ThreadPoolExecutor(max_workers=10)

#roep meteo weer api aan en return regen en temperatuur
def roep_weer_api():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 5.22,
        "current": "temperature_2m,rain",
        "timezone": "auto",
    }
    response = get(url=url, params=params)
    #pakt de response body en zet de json om naar een python struct
    data = response.json()
    temperatuur = data["current"]["temperature_2m"]
    regen = data["current"]["rain"]
    return temperatuur, regen

def bereken_fixed_items(voorkeur_eten:list, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool):
    if temperatuur >= 20 and rekening_houden_weer == True:
        return "ijsje"

    if regen == True and rekening_houden_weer == True:
        return  "regen"

    if verblijfsduur >= 240:
        return "elke 2 uur lunch"
    else:
        return "1 keer lunch"

def _generate_plan(bezoeker, temperatuur, regen):
    thread_db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
    thread_db.connect()

    #reserverd_items, reserverd_time =bereken_fixed_items(
    #    voorkeur_eten=bezoeker["voorkeuren_eten"], 
    #    verblijfsduur=bezoeker["verblijfsduur"],
    #    rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
    #    temperatuur=temperatuur,
    #    regen=regen,
    #    )

    #tijd_left = bezoeker["verblijfsduur"] - reserverd_time

    tijd_over = bezoeker["verblijfsduur"]
    
    voorzieningen = thread_db.execute_query(f"""
        SELECT * FROM voorziening WHERE
        attractie_min_lengte <= {bezoeker["lengte"]} OR attractie_min_lengte IS NULL AND
        attractie_max_lengte >= {bezoeker["lengte"]} OR attractie_max_lengte IS NULL AND
        attractie_min_leeftijd <= {bezoeker["leeftijd"]} OR attractie_min_leeftijd  IS NULL AND
        attractie_max_gewicht >= {bezoeker["gewicht"]} OR attractie_max_gewicht IS NULL AND
        type != 'winkel' AND type != 'horeca'
    """)

    if not bezoeker["voorkeuren_eten"]:
        horeca = thread_db.execute_query(f"""
            SELECT * FROM voorziening WHERE type = 'horeca' 
        """)
        gekozen_horeca = horeca[randint(0, len(horeca))]
        tijd_over -= 15
    else:
        voorkeuren_lijst = [item.strip() for item in bezoeker["voorkeuren_eten"].split(",")]
        voorkeuren_string = ", ".join(f"'{item}'" for item in  voorkeuren_lijst)
        horeca = thread_db.execute_query(f"""
            SELECT * FROM voorziening WHERE type = 'horeca' AND productaanbod IN({voorkeuren_string}) 
        """)
        gekozen_horeca = horeca[randint(0, len(horeca))]
        tijd_over -= 15

    lievelingsattracties = bezoeker["lievelingsattracties"].split(",") if bezoeker["lievelingsattracties"] else []
    voorkeuren_attractietypes = bezoeker["voorkeuren_attractietypes"].split(",") if bezoeker["voorkeuren_attractietypes"] else []

    attractielijst = []
    for favoriet in lievelingsattracties:
        for voorziening in voorzieningen:
            if favoriet == voorziening["naam"]:
                favoriete_attractietijd_nodig = (int(voorziening["geschatte_wachttijd"]) + int(voorziening["doorlooptijd"])) * 2
                if tijd_over - favoriete_attractietijd_nodig >= 0:
                    attractielijst.append(voorziening)
                    attractielijst.append(voorziening)
                    tijd_over -= favoriete_attractietijd_nodig
                    break

    midden = len(attractielijst) // 2
    attractielijst.insert(midden, gekozen_horeca)

    print(bezoeker["naam"])
    pprint.pp(attractielijst)   
    print(tijd_over) 

    bezoeker["rekening_houden_met_weer"] = True if bezoeker["rekening_houden_met_weer"] == 1 else False

    dagprogramma = {
        "bezoekersgegevens" : {
            "naam": bezoeker['naam'],
            "gender": bezoeker['gender'],
            "verblijfsduur": bezoeker["verblijfsduur"],
            "leeftijd": bezoeker["leeftijd"],
            "lengte": bezoeker["lengte"],
            "gewicht": bezoeker["gewicht"],
            "voorkeuren_attractietypes": bezoeker["voorkeuren_attractietypes"],
            "lievelingsattracties": bezoeker["lievelingsattracties"],
            "voorkeuren_eten": bezoeker["voorkeuren_eten"],
            "rekening_houden_met_weer": bezoeker["rekening_houden_met_weer"]
        },
        "weergegevens" : {
            "temperatuur": temperatuur,
            "kans_op_regen": regen
        }, 
        "voorzieningen": attractielijst
        ,
        "totale_duur": 0 # STAP 3: aanpassen naar daadwerkelijke totale duur
    }
    
    with open(f'dagprogramma_bezoeker_{bezoeker["naam"]}.json', 'w') as json_bestand_uitvoer:
        json.dump(dagprogramma, json_bestand_uitvoer, indent=4)


async def main():
    #maak async?
    temperatuur, regen = roep_weer_api()
    print(temperatuur, regen)


    bezoekers = db.execute_query("SELECT * FROM Bezoeker;")
    db.close()

    #haal de async event loop op
    loop = asyncio.get_event_loop()

    #maar een lijst met daarin _generate_plan en zijn argumeenten voor elke bezoeker die parallel gerund gaat worden
    planningen = [loop.run_in_executor(None, _generate_plan, bezoeker, temperatuur, regen) for bezoeker in bezoekers]
    
    #verzamel alle _generate_plans en start ze in hun eigen threads
    await asyncio.gather(*planningen)

if __name__ == "__main__":
    asyncio.run(
        main()
        )