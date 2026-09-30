# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
from requests import get
from concurrent.futures import ThreadPoolExecutor
import asyncio

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
     
     return

def _generate_plan(bezoeker, temperatuur, regen):
    thread_db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
    thread_db.connect()

    bereken_fixed_items(
        voorkeur_eten=bezoeker["voorkeuren_eten"], 
        verblijfsduur=bezoeker["verblijfsduur"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        temperatuur=temperatuur,
        regen=regen,
        )
    
    voorzieningen = thread_db.execute_query(f"""
        SELECT * FROM voorziening WHERE
        attractie_min_lengte <= {bezoeker["lengte"]} AND
        attractie_max_lengte >= {bezoeker["lengte"]} AND
        attractie_min_leeftijd <= {bezoeker["leeftijd"]} AND
        attractie_max_gewicht >= {bezoeker["gewicht"]} OR 
        type = 'winkel' OR 
        type = 'horeca'
    """)

    print(bezoeker["naam"])
    pprint.pp(voorzieningen)    

    return


async def main():
    #maak async?
    bezoekers = db.execute_query("SELECT * FROM Bezoeker;")
    temperatuur, regen = roep_weer_api()
    
    print(temperatuur, regen)

    #haal de async event loop op
    loop = asyncio.get_event_loop()


    planningen = [loop.run_in_executor(None, _generate_plan, bezoeker, temperatuur, regen) for bezoeker in bezoekers]

    resultaten = await asyncio.gather(*planningen)




    # bezoeker_id = 1
    # select_query = f"SELECT * FROM Bezoeker WHERE id = {bezoeker_id}"
    # resultaat = db.execute_query(select_query)

    # bezoeker = resultaat[0]
    # print(bezoeker['naam']) 


    # select_query = "SELECT * FROM voorziening"
    # voorzieningen = db.execute_query(select_query)
    # pprint.pp(voorzieningen) 
    # print(voorzieningen[0]["naam"])

    db.close()

    # dagprogramma = {
    #     "bezoekersgegevens" : {
    #         "naam": bezoeker['naam'] # voorbeeld van hoe je bij een eigenschap komt
    #         # STAP 1: vul aan met andere benodigde eigenschappen
    #     },
    #     "weergegevens" : {
    #         # STAP 4: vul aan met weergegevens
    #     }, 
    #     "voorzieningen": [] # STAP 2: hier komt een lijst met alle voorzieningen
    #     ,
    #     "totale_duur": 0 # STAP 3: aanpassen naar daadwerkelijke totale duur
    # }

    # with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    #     json.dump(dagprogramma, json_bestand_uitvoer, indent=4)

if __name__ == "__main__":
    asyncio.run(
        main()
        )