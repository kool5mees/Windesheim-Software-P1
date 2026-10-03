# import modulen
from pathlib import Path
from database_wrapper import Database
import httpx
from concurrent.futures import ThreadPoolExecutor
import asyncio
from planning_genereren import _generate_plan_thread

#Database connectie
db = Database(host="localhost", gebruiker="user", wachtwoord="password", database="attractiepark_casus_a")

#creer een threadpool voor het multithreaden van planningen berekenen
executor = ThreadPoolExecutor(max_workers=10)

#roep meteo weer api aan en return regen en temperatuur
async def haal_weer_gegevens():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.52,
        "longitude": 5.22,
        "current": "temperature_2m,rain",
        "timezone": "auto",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
    data = r.json()
    temperatuur = data["current"]["temperature_2m"]
    regen = data["current"]["rain"]
    return temperatuur, regen

async def haal_bezoekers_uit_database():
    try:
        await db.connect()
        bezoekers = await db.execute_query("SELECT * FROM Bezoeker;")
        await db.close()
    except Exception as e:
        print(f"Fout opgetreden: {e}")
    return bezoekers

async def main():
    #haal bezoekers en weer gegevens op
    bezoekers, (temperatuur, regen) = await asyncio.gather(
        haal_bezoekers_uit_database(),
        haal_weer_gegevens()
    )

    print(temperatuur, regen)



    #haal de async event loop op
    loop = asyncio.get_event_loop()

    #maar een lijst met daarin _generate_plan en zijn argumeenten voor elke bezoeker die parallel gerund gaat worden
    planningen = [loop.run_in_executor(None, _generate_plan_thread, bezoeker, temperatuur, regen) for bezoeker in bezoekers]
    
    #verzamel alle _generate_plans en start ze in hun eigen threads
    await asyncio.gather(*planningen)

if __name__ == "__main__":
    asyncio.run(
        main()
        )

#TODO: correcte json velden toevoegen
#Onthou Types in gebruikers attractie voorkeuren zijn met hoofdletter maar type in voorziening is zonder hoofdletter