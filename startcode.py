# import modulen
from pathlib import Path
import json
import pprint
from database_wrapper import Database

# -----------------------------------------
# Database initialisatie en verbinden
# -----------------------------------------
# parameters voor connectie met de database
db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
# altijd verbinding openen om query's uit te voeren
db.connect()

# -----------------------------------------
# Haal de eigenschappen op van een bezoeker
# -----------------------------------------
bezoeker_id = 1 # pas id aan om een andere bezoeker te selecteren

# SQL-query om alle gegevens van één bezoeker op te halen op basis van het ID.
select_query = f"SELECT * FROM bezoeker WHERE id = {bezoeker_id}"
resultaat = db.execute_query(select_query)

# haal de eerste rij uit het resultaat.
bezoeker = resultaat[0]

# voorbeeld van hoe je bij een eigenschap komt
print(bezoeker['naam']) 

# -----------------------------------------
# Haal alle voorzieningen op
# -----------------------------------------
# pas deze query aan en voeg queries toe om de juiste voorzieningen op te halen
select_query = "SELECT * FROM voorziening"
voorzieningen = db.execute_query(select_query)

# print de resultaten van de query op een overzichtelijke manier
pprint.pp(voorzieningen) 

# print de naam van de eerste voorziening
print(voorzieningen[0]["naam"])

# altijd verbinding sluiten met de database als je klaar bent
db.close()

# verzamel alle benodigde gegevens in een dictionary
dagprogramma = {
    "bezoekersgegevens" : {
        "naam": bezoeker['naam'] # voorbeeld van hoe je bij een eigenschap komt
        # STAP 1: vul aan met andere benodigde eigenschappen
    },
    "weergegevens" : {
        # STAP 4: vul aan met weergegevens
    }, 
    "voorzieningen": [] # STAP 2: hier komt een lijst met alle voorzieningen
    ,
    "totale_duur": 0 # STAP 3: aanpassen naar daadwerkelijke totale duur
}

# uiteindelijk schrijven we de dictionary weg naar een JSON-bestand, die kan worden ingelezen door de acceptatieomgeving
with open('dagprogramma_bezoeker_x.json', 'w') as json_bestand_uitvoer:
    json.dump(dagprogramma, json_bestand_uitvoer, indent=4)