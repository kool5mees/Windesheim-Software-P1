# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database
from requests import get

#Database connectie
db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
# altijd verbinding openen om query's uit te voeren
db.connect()

def roep_weer_api():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 5.22,
        "current": "temperature_2m,rain",
        "timezone": "auto",
    }
    response = get(url=url, params=params)
    data = response.json()
    temperatuur = data["current"]["temperature_2m"]
    regen = data["current"]["rain"]
    return temperatuur, regen

def bereken_fixed_items(voorkeur_eten:list, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool):
     return



def main():

    #maak async?
    bezoekers = db.execute_query("SELECT * FROM Bezoeker;")
    temperatuur, regen = roep_weer_api()

    print(temperatuur, regen)
    for bezoeker in bezoekers:
        print(bezoeker["naam"])
        bereken_fixed_items(
            voorkeur_eten=bezoeker["voorkeuren_eten"], 
            verblijfsduur=bezoeker["verblijfsduur"],
            rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
            temperatuur=temperatuur,
            regen=regen,
            )

    roep_weer_api()




    # bezoeker_id = 1
    # select_query = f"SELECT * FROM Bezoeker WHERE id = {bezoeker_id}"
    # resultaat = db.execute_query(select_query)

    # bezoeker = resultaat[0]
    # print(bezoeker['naam']) 


    # select_query = "SELECT * FROM voorziening"
    # voorzieningen = db.execute_query(select_query)
    # pprint.pp(voorzieningen) 
    # print(voorzieningen[0]["naam"])

    # db.close()

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
    main()