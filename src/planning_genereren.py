import random
from database_wrapper import Database
import json
import pprint
import asyncio
import queue

def _generate_plan_thread(bezoeker, temperatuur, regen):
    asyncio.run(_generate_plan(bezoeker, temperatuur, regen))

async def bereken_fixed_items(voorkeur_eten:list, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool, cursor):
    gereserveerde_items = queue.Queue(-1)
    gereserveerde_tijd = 0
    is_weer_gevoelig = rekening_houden_weer and (temperatuur > 20 or regen > 50)
    langer_dan_4_uur = verblijfsduur > 240
    hvl_horeca_nodig = 0
    hvl_horeca_nodig = 1 if not langer_dan_4_uur else verblijfsduur // 120


    #TODO
    #1.paraplu winkels, ijswinkels en souvenir winkels hoeven maar 1 keer opgehaald te worden
    #er kan al in main makkelijk gekeken worden of dit nodig is, en dan kan dit als argument meegegeven worden aan deze functie
    #2. check of actief is
    #3. reken hescahte wachttijd en doorlooptijd ook mee
    #4. check of de voorzieing binnen is wanneer het regent
    #5. wanner regen api failed moet er nog steeds verder gegaand worden

    if is_weer_gevoelig:
        if regen > 50:
            paraplu_winkels = await cursor.execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'winkel' AND productaanbod = 'Regenaccessoires'
            """)
            paraplu_winkel = random.choice(paraplu_winkels)
            gereserveerde_items.put(paraplu_winkel)
        if temperatuur > 20:
            ijswinkels = await cursor.execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' AND productaanbod = 'ijs'
            """)
            ijswinkel = random.choice(ijswinkels)
            gereserveerde_items.put(ijswinkel)
            hvl_horeca_nodig -= 1

    #haal alvaste souvenir winkel op voor einde
    souvenir_winkels = await cursor.execute_query(f"""
        SELECT * FROM voorziening WHERE type = 'winkel' AND productaanbod = 'Souvenirs'
    """)
    souvenir_winkel =  random.choice(souvenir_winkels)
    gereserveerde_tijd += 15

    if hvl_horeca_nodig > 0:
        if not voorkeur_eten:
            horeca_list: list = await cursor.execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' 
            """)
            horeca_list_copy = horeca_list.copy()

            for _ in range(hvl_horeca_nodig):
                if len(horeca_list_copy) == 0:
                    horeca_list_copy = horeca_list.copy()
                gereserveerde_items.put(horeca_list_copy.pop(horeca_list_copy.index(random.choice(horeca_list_copy))))
                gereserveerde_tijd += 15
        else:
            voorkeuren_lijst = [item.strip() for item in voorkeur_eten.split(",")]
            horeca_list: list = await cursor.execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' AND productaanbod IN({", ".join(["%s"] * len(voorkeuren_lijst))}) 
            """, tuple(voorkeuren_lijst))
            horeca_list_copy = horeca_list.copy()
            
            for _ in range(hvl_horeca_nodig):
                if len(horeca_list_copy) == 0:
                    horeca_list_copy = horeca_list.copy()
                gereserveerde_items.put(horeca_list_copy.pop(horeca_list_copy.index(random.choice(horeca_list_copy))))
                gereserveerde_tijd += 15

    gereserveerde_items.put(souvenir_winkel)

    if gereserveerde_tijd > verblijfsduur:
        raise Exception("Error: verblijfsduur is te kort voor verijsde basis voorzieningen.")

    return gereserveerde_items, gereserveerde_tijd

async def bereken_attracties(bezoeker, voorzieningen, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool):
    pass

async def merge_attracties_en_fixed_items(voorzieningen, gereserveerde_items: queue.Queue, regen, verblijfsduur, rekening_houden_weer, temperatuur):
    #BUG
    #.get() op een lege queue blijft eeuwig hangen
    voorzieningen_lijst = []
    if rekening_houden_weer and regen > 50:
        voorzieningen_lijst.append(gereserveerde_items.get())

    pass

async def schrijf_json_bestand(bezoeker, dagprogramma):
    pass

async def _generate_plan(bezoeker, temperatuur, regen):
    thread_db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
    await thread_db.connect()

    tijd_gebruikt = 0
    
    #TODO
    #Deze functie uitwerken om de juiste horeca en winkels vooraf te berkenen
    gereserveerde_items, gereserveerde_tijd = bereken_fixed_items(
        voorkeur_eten=bezoeker["voorkeuren_eten"], 
        verblijfsduur=bezoeker["verblijfsduur"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        temperatuur=temperatuur,
        regen=regen,
        cursor=thread_db.cursor
    )

    tijd_gebruikt += gereserveerde_tijd

    #----#
    
    voorzieningen = await thread_db.execute_query(f"""
        SELECT * FROM voorziening WHERE
        (attractie_min_lengte <= %s OR attractie_min_lengte IS NULL) AND
        (attractie_max_lengte >= %s OR attractie_max_lengte IS NULL) AND
        (attractie_min_leeftijd <= %s OR attractie_min_leeftijd IS NULL) AND
        (attractie_max_gewicht >= %s OR attractie_max_gewicht IS NULL) AND
        type != 'winkel' AND type != 'horeca'
    """, (bezoeker["lengte"], bezoeker["lengte"], bezoeker["leeftijd"], bezoeker["gewicht"]))

    lievelingsattracties = bezoeker["lievelingsattracties"].split(",") if bezoeker["lievelingsattracties"] else []
    voorkeuren_attractietypes = bezoeker["voorkeuren_attractietypes"].split(",") if bezoeker["voorkeuren_attractietypes"] else []

    attractielijst = []
    for favoriet in lievelingsattracties:
        for voorziening in voorzieningen:
            if favoriet == voorziening["naam"]:
                favoriete_attractietijd_nodig = (int(voorziening["geschatte_wachttijd"]) + int(voorziening["doorlooptijd"])) * 2
                if favoriete_attractietijd_nodig + tijd_gebruikt <= bezoeker["verblijfsduur"]:
                    voorziening["is_favoriet"] = True
                    attractielijst.append(voorziening)
                    attractielijst.append(voorziening)
                    tijd_gebruikt += favoriete_attractietijd_nodig
                    break

    midden = len(attractielijst) // 2
    attractielijst.insert(midden, gekozen_horeca)

    print(bezoeker["naam"])
    pprint.pp(attractielijst)   
    print(tijd_gebruikt) 

    bezoeker["rekening_houden_met_weer"] = True if bezoeker["rekening_houden_met_weer"] == 1 else False

    dagprogramma = {
        "bezoekersgegevens" : {
            "naam": bezoeker['naam'],
            #"gender": bezoeker['gender'], volgens testplan hoeft gender er niet in?
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
        "totale_duur": tijd_gebruikt
    }
    
    with open(f'../output/dagprogramma_bezoeker_{bezoeker["naam"]}.json', 'w') as json_bestand_uitvoer:
        json.dump(dagprogramma, json_bestand_uitvoer, indent=4)

    #close connectie
    await thread_db.close()
