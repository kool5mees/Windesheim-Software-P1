import random
from database_wrapper import Database
import json
import pprint
import asyncio
import queue
from dotenv import load_dotenv
from os import getenv

#TODO
#dit is setup en hoort eigenlijk ergens anders maar ik heb het hier gezet voor nu zodat ik geen circular import krijg met main
load_dotenv()
db_credentials = {"host":getenv("host"), "gebruiker":getenv("gebruiker"), "wachtwoord": getenv("wachtwoord")}

def _generate_plan_thread(bezoeker, temperatuur, regen):
    asyncio.run(_generate_plan(bezoeker, temperatuur, regen))

async def bereken_fixed_items(voorkeur_eten:list, verblijfsduur:int, rekening_houden_weer:bool, temperatuur, regen:bool, execute_query):
    gereserveerde_items = queue.Queue(-1)
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

    if hvl_horeca_nodig > 0:
        if not voorkeur_eten:
            horeca_list: list = await execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' 
            """)
            horeca_list_copy = horeca_list.copy()

            for _ in range(hvl_horeca_nodig):
                if len(horeca_list_copy) == 0:
                    horeca_list_copy = horeca_list.copy()
                gekozen_item = horeca_list_copy.pop(horeca_list_copy.index(random.choice(horeca_list_copy)))
                gereserveerde_items.put(gekozen_item)
        else:
            voorkeuren_lijst = [item.strip() for item in voorkeur_eten.split(",")]
            horeca_list: list = await execute_query(f"""
                SELECT * FROM voorziening WHERE type = 'horeca' AND productaanbod IN({", ".join(["%s"] * len(voorkeuren_lijst))}) 
            """, tuple(voorkeuren_lijst))
            horeca_list_copy = horeca_list.copy()
            
            for _ in range(hvl_horeca_nodig):
                if len(horeca_list_copy) == 0:
                    horeca_list_copy = horeca_list.copy()
                gekozen_item = horeca_list_copy.pop(horeca_list_copy.index(random.choice(horeca_list_copy)))
                gereserveerde_items.put(gekozen_item)

    return gereserveerde_items, souvenir_winkel

async def attractielijst_kort_verblijf(verblijfsduur, favoriete_lijst, preffered_lijst, overige_lijst):
    #attractielijst + voorzieningen voor een bezoeker met korter dan 4 uur verblijfsduur
    totale_gebruikte_tijd = 0
    
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

def past_horeca(gereserveerde_items:queue.Queue, attractielijst:list, totale_gebruikte_tijd, verblijfsduur):
    if gereserveerde_items.empty():
        return totale_gebruikte_tijd, False
    horeca_item = gereserveerde_items.queue[0]
    horeca_tijd = 15 + horeca_item["geschatte_wachttijd"] + horeca_item["doorlooptijd"]
    if totale_gebruikte_tijd + horeca_tijd > verblijfsduur:
        return totale_gebruikte_tijd, False
    horeca_item = gereserveerde_items.get()
    attractielijst.append(horeca_item)
    return totale_gebruikte_tijd + horeca_tijd, True

async def attractieslijst_lang_verblijf(verblijfsduur, favoriete_lijst, preffered_lijst, overige_lijst, gereserveerde_items:queue.Queue):
    #attractielijst + voorziening voor bezoeker met verblijfsduur langer dan 4 uur
    #BUG
    #.get() op een lege queue blijft eeuwig hangen

    twee_uur = 0
    totale_gebruikte_tijd = 0
    #lievelingsattracties
    attractielijst = []
    for favoriet in favoriete_lijst:
        favoriete_attractietijd_nodig = (int(favoriet["geschatte_wachttijd"]) + int(favoriet["doorlooptijd"])) * 2
        if favoriete_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(favoriet)
            attractielijst.append(favoriet)
            totale_gebruikte_tijd += favoriete_attractietijd_nodig
            twee_uur += favoriete_attractietijd_nodig
            if twee_uur > 120:
                totale_gebruikte_tijd, toegevoegd = past_horeca(
                    gereserveerde_items=gereserveerde_items,
                    attractielijst=attractielijst,
                    totale_gebruikte_tijd=totale_gebruikte_tijd,
                    verblijfsduur=verblijfsduur
                    )
                if toegevoegd:
                    twee_uur = 0

    #preffered attracties
    for preffered in preffered_lijst:
        preffered_attractietijd_nodig = (int(preffered["geschatte_wachttijd"]) + int(preffered["doorlooptijd"]))
        if preffered_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(preffered)
            totale_gebruikte_tijd += preffered_attractietijd_nodig
            twee_uur += preffered_attractietijd_nodig
            if twee_uur > 120:
                totale_gebruikte_tijd, toegevoegd = past_horeca(
                    gereserveerde_items=gereserveerde_items,
                    attractielijst=attractielijst,
                    totale_gebruikte_tijd=totale_gebruikte_tijd,
                    verblijfsduur=verblijfsduur
                    )
                if toegevoegd:
                    twee_uur = 0
                
    #overige attracties
    for overige in overige_lijst:
        overige_attractietijd_nodig = (int(overige["geschatte_wachttijd"]) + int(overige["doorlooptijd"]))
        if overige_attractietijd_nodig + totale_gebruikte_tijd <= verblijfsduur:
            attractielijst.append(overige)
            totale_gebruikte_tijd += overige_attractietijd_nodig
            twee_uur += overige_attractietijd_nodig
            if twee_uur > 120:
                totale_gebruikte_tijd, toegevoegd = past_horeca(
                    gereserveerde_items=gereserveerde_items,
                    attractielijst=attractielijst,
                    totale_gebruikte_tijd=totale_gebruikte_tijd,
                    verblijfsduur=verblijfsduur
                    )
                if toegevoegd:
                    twee_uur = 0
    
    return attractielijst, totale_gebruikte_tijd


async def bereken_attracties(
        lengte: int, 
        leeftijd: int, 
        gewicht: int, 
        lievelingsattracties: str,
        voorkeuren_attractietypes: str,
        verblijfsduur:int, 
        rekening_houden_weer:bool,  
        regen:bool, 
        execute_query,
        gereserveerde_items: queue.Queue,
        souvenir_winekel
    ):

    #TODO
    #1. check of actief is
    #2. check of de attractie binnen is wanneer het regent
    #3. maak ook planningen voor bezoekers die langer dan 4 uur blijven
    #4. nu wordt er eerste all favorieten en dan preffered type gedaan als preffered type bijv
    #fammily, draaien is dan wordt de planning mischien opgevuld met alleen maar family
 
    attracties_tijd = 0
    planning = []

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

    #random shuffle helpt ietsje met het verbeteren van
    random.shuffle(preffered_lijst)
    random.shuffle(overige_lijst)
    totale_gebruikte_tijd = 0

    if rekening_houden_weer and regen > 50 and not gereserveerde_items.empty():
        paraplu_winkel = gereserveerde_items.get()
        planning.append(paraplu_winkel)
        totale_gebruikte_tijd += (paraplu_winkel["geschatte_wachttijd"] + paraplu_winkel["doorlooptijd"])

    beschikbaare_tijd = ((verblijfsduur - totale_gebruikte_tijd) - (souvenir_winekel["geschatte_wachttijd"] + souvenir_winekel["doorlooptijd"]))
    if verblijfsduur <= 240 and not gereserveerde_items.empty():
        horeca_item = gereserveerde_items.get()
        beschikbaare_tijd -= (15 + horeca_item["geschatte_wachttijd"] + horeca_item["doorlooptijd"])

    if verblijfsduur <= 240:
        attracties, voorzieningen_tijd = await attractielijst_kort_verblijf(
            verblijfsduur=beschikbaare_tijd,
            favoriete_lijst=favoriete_lijst,
            preffered_lijst=preffered_lijst,
            overige_lijst=overige_lijst
            )
        planning.extend(attracties)
        midden = len(planning) // 2
        planning.insert(midden, horeca_item)
        totale_gebruikte_tijd += (15 + horeca_item["geschatte_wachttijd"] + horeca_item["doorlooptijd"])
    else:
        attracties, voorzieningen_tijd = await attractieslijst_lang_verblijf(
            verblijfsduur=beschikbaare_tijd,
            favoriete_lijst=favoriete_lijst,
            preffered_lijst=preffered_lijst,
            overige_lijst=overige_lijst,
            gereserveerde_items=gereserveerde_items
        )
        planning.extend(attracties)
    
    planning.append(souvenir_winekel)
    totale_gebruikte_tijd += (souvenir_winekel["geschatte_wachttijd"] + souvenir_winekel["doorlooptijd"] + voorzieningen_tijd)
    return planning, totale_gebruikte_tijd

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
    
    with open(f'../output/dagprogramma_bezoeker_{bezoeker["id"]}.json', 'w') as json_bestand_uitvoer:
        json.dump(dagprogramma, json_bestand_uitvoer, indent=4)


async def _generate_plan(bezoeker, temperatuur, regen):
    thread_db = Database(host=db_credentials["host"], gebruiker=db_credentials["gebruiker"], wachtwoord=db_credentials["wachtwoord"], database="attractiepark_casus_a")
    await thread_db.connect()

    tijd_gebruikt = 0

    gereserveerde_items, souvenir_winkel = await bereken_fixed_items(
        voorkeur_eten=bezoeker["voorkeuren_eten"], 
        verblijfsduur=bezoeker["verblijfsduur"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        temperatuur=temperatuur,
        regen=regen,
        execute_query=thread_db.execute_query
    )

    #----#
    
    planning, attracties_tijd = await bereken_attracties(
        verblijfsduur=bezoeker["verblijfsduur"],
        gereserveerde_items=gereserveerde_items,
        lengte=bezoeker["lengte"],
        leeftijd=bezoeker["leeftijd"],
        gewicht=bezoeker["gewicht"],
        rekening_houden_weer=bool(bezoeker["rekening_houden_met_weer"]),
        lievelingsattracties=bezoeker["lievelingsattracties"],
        voorkeuren_attractietypes=bezoeker["voorkeuren_attractietypes"],
        regen=regen,
        souvenir_winekel=souvenir_winkel,
        execute_query=thread_db.execute_query
    )

    #----#
    await schrijf_json_bestand(bezoeker, planning=planning, tijd_gebruikt=attracties_tijd, temperatuur=temperatuur, regen=regen, dagprogramma=planning)
        
    #close connectie
    await thread_db.close()
