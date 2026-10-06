import random
from database_wrapper import Database
import json
import pprint
import asyncio
import queue

def _generate_plan_thread(bezoeker, temperatuur, regen):
    asyncio.run(_generate_plan(bezoeker, temperatuur, regen))

async def bereken_fixed_items(voorkeur_eten:list, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool, execute_query):
    #queue is eigenlijk voornamelijk voor thread safety en ookal doe ik multithreading is er geen comunicatie tussen threads
    #ik gebruik het voornamelijk omdat het first in first out is in plaats van een list die first in last out is
    #aangezien mijn fixed items list al gesorteerd is

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
    #6. error handeling

    if is_weer_gevoelig:
        if regen > 50:
            paraplu_winkels = await execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'winkel' AND productaanbod = 'Regenaccessoires'
            """)
            paraplu_winkel = random.choice(paraplu_winkels)
            gereserveerde_items.put(paraplu_winkel)
        if temperatuur > 20:
            ijswinkels = await execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' AND productaanbod = 'ijs'
            """)
            ijswinkel = random.choice(ijswinkels)
            gereserveerde_items.put(ijswinkel)
            hvl_horeca_nodig -= 1

    #haal alvaste souvenir winkel op voor einde
    souvenir_winkels = await execute_query(f"""
        SELECT * FROM voorziening WHERE type = 'winkel' AND productaanbod = 'Souvenirs'
    """)
    souvenir_winkel =  random.choice(souvenir_winkels)
    gereserveerde_tijd += 15

    if hvl_horeca_nodig > 0:
        if not voorkeur_eten:
            horeca_list: list = await execute_query(f"""
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
            horeca_list: list = await execute_query(f"""
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

    #pprint.pp(gereserveerde_items.queue)

    return gereserveerde_items, gereserveerde_tijd

async def attractielijst_onder_4uur(lengte, leeftijd, gewicht, verblijfsduur, gereserveerde_tijd, lievelingsattracties:str, voorkeuren_attractietypes:str, execute_query):
    voorzieningen:list = await execute_query(f"""
        SELECT * FROM voorziening WHERE
        (attractie_min_lengte <= %s OR attractie_min_lengte IS NULL) AND
        (attractie_max_lengte >= %s OR attractie_max_lengte IS NULL) AND
        (attractie_min_leeftijd <= %s OR attractie_min_leeftijd IS NULL) AND
        (attractie_max_gewicht >= %s OR attractie_max_gewicht IS NULL) AND
        type != 'winkel' AND type != 'horeca'
    """, (lengte, lengte, leeftijd, gewicht))


    voorkeuren_attractietypes = voorkeuren_attractietypes.casefold()
    lievelingsattracties = lievelingsattracties.casefold()

    lievelingsattracties:list = [item.strip() for item in lievelingsattracties.split(",")] if lievelingsattracties else []
    voorkeuren_attractietypes:list = [item.strip() for item in voorkeuren_attractietypes.split(",")] if voorkeuren_attractietypes else [] 

    totale_gebruikte_tijd = gereserveerde_tijd

    favoriete_lijst = []
    preffered_lijst = []
    overige_lijst = []

    for voorziening in voorzieningen:
        if voorziening["naam"].casefold() in lievelingsattracties:
            voorziening["is_favoriet"] = True
            favoriete_lijst.append(voorziening)
        elif voorziening["type"].casefold() in voorkeuren_attractietypes:
            voorziening["is_favoriet"] = False
            preffered_lijst.append(voorziening)
        else:
            voorziening["is_favoriet"] = False
            overige_lijst.append(voorziening)
    
    #lievelingsattracties
    attractielijst = []
    for favoriet in favoriete_lijst:
        favoriete_attractietijd_nodig = (int(favoriet["geschatte_wachttijd"]) + int(favoriet["doorlooptijd"])) * 2
        if favoriete_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(favoriet)
            attractielijst.append(favoriet)
            totale_gebruikte_tijd += favoriete_attractietijd_nodig

    #preffered attracties
    for preffered in preffered_lijst:
        preffered_attractietijd_nodig = (int(preffered["geschatte_wachttijd"]) + int(preffered["doorlooptijd"]))
        if preffered_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(preffered)
            totale_gebruikte_tijd += preffered_attractietijd_nodig

    #overige attracties
    for overige in overige_lijst:
        overige_attractietijd_nodig = (int(overige["geschatte_wachttijd"]) + int(overige["doorlooptijd"]))
        if overige_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(overige)
            totale_gebruikte_tijd += overige_attractietijd_nodig

    random.shuffle(attractielijst)
    
    return attractielijst, totale_gebruikte_tijd


async def bereken_attracties(
        lengte: int, 
        leeftijd: int, 
        gewicht: int, 
        lievelingsattracties: str,
        voorkeuren_attractietypes: str,
        verblijfsduur:int, 
        rekening_houden_weer:bool, 
        temperatuur, 
        regen:bool, 
        execute_query, 
        gereserveerde_tijd:int,
        gereserveerde_items: queue.Queue
    ):

    #TODO
    #1. check of actief is
    #2. check of de attractie binnen is wanneer het regent
    #3. maak ook planningen voor bezoekers die langer dan 4 uur blijven
    #4. nu wordt er eerste all favorieten en dan preffered type gedaan als preffered type bijv
    #fammily, draaien is dan wordt de planning mischien opgevuld met alleen maar family
 
    attracties_tijd = 0
    planning = []
    
    #BUG
    #.get() op een lege queue blijft eeuwig hangen
    if rekening_houden_weer and regen > 50 and not gereserveerde_items.empty():
        planning.append(gereserveerde_items.get())

    if verblijfsduur <= 240 and not gereserveerde_items.empty():
        attracties, totale_gebruikte_tijd = await attractielijst_onder_4uur(
            lengte=lengte, 
            leeftijd=leeftijd,
            gewicht=gewicht,
            lievelingsattracties=lievelingsattracties,
            verblijfsduur=verblijfsduur,
            voorkeuren_attractietypes=voorkeuren_attractietypes,
            execute_query=execute_query,
            gereserveerde_tijd=gereserveerde_tijd
            )
        planning.extend(attracties)
        midden = len(planning) // 2
        planning.insert(midden, gereserveerde_items.get())
        planning.append(gereserveerde_items.get())
        return planning, totale_gebruikte_tijd
    else:
        planning = []
        attracties_tijd = 0
        return planning, attracties_tijd

    #return planning, attracties_tijd

async def schrijf_json_bestand(bezoeker, dagprogramma, tijd_gebruikt, planning, temperatuur, regen):
    bezoeker["rekening_houden_met_weer"] = True if bezoeker["rekening_houden_met_weer"] == 1 else False
    pprint.pprint(dagprogramma) 

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
        "voorzieningen": planning
        ,
        "totale_duur": tijd_gebruikt
    }
    
    with open(f'../output/dagprogramma_bezoeker_{bezoeker["naam"]}.json', 'w') as json_bestand_uitvoer:
        json.dump(dagprogramma, json_bestand_uitvoer, indent=4)


async def _generate_plan(bezoeker, temperatuur, regen):
    thread_db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")
    await thread_db.connect()

    tijd_gebruikt = 0

    gereserveerde_items, gereserveerde_tijd = await bereken_fixed_items(
        voorkeur_eten=bezoeker["voorkeuren_eten"], 
        verblijfsduur=bezoeker["verblijfsduur"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        temperatuur=temperatuur,
        regen=regen,
        execute_query=thread_db.execute_query
    )

    tijd_gebruikt += gereserveerde_tijd

    #----#
    
    planning, attracties_tijd = await bereken_attracties(
        verblijfsduur=bezoeker["verblijfsduur"],
        gereserveerde_tijd=tijd_gebruikt,
        gereserveerde_items=gereserveerde_items,
        lengte=bezoeker["lengte"],
        leeftijd=bezoeker["leeftijd"],
        gewicht=bezoeker["gewicht"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        lievelingsattracties=bezoeker["lievelingsattracties"],
        voorkeuren_attractietypes=bezoeker["voorkeuren_attractietypes"],
        temperatuur=temperatuur,
        regen=regen,
        execute_query=thread_db.execute_query
    )


    #----#
    await schrijf_json_bestand(bezoeker, planning=planning, tijd_gebruikt=attracties_tijd, temperatuur=temperatuur, regen=regen, dagprogramma=planning)
        
    #close connectie
    await thread_db.close()
