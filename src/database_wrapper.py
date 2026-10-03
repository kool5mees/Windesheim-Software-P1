import mysql.connector.aio as db

class Database:
    def __init__(self, host, gebruiker, wachtwoord, database):

        self.host = host
        self.gebruiker = gebruiker
        self.wachtwoord = wachtwoord
        self.database = database
        self.connection = None

    async def connect(self):
        try:
            self.connection =  await db.connect(
                host=self.host,
                user=self.gebruiker,
                password=self.wachtwoord,
                database=self.database,
                use_pure = True
            )
            #print("Verbonden met de database!")
        except db.connection.Error as err:
            print(f"Fout bij verbinden met de database: {err}")

    async def execute_query(self, query, params = None):
        if self.connection:
            try:
                cursor = await self.connection.cursor(dictionary=True)
                await cursor.execute(query, params)
                if cursor.description:
                    return await cursor.fetchall()
                else:
                    #print("Aantal rijen geupdated {}".format(cursor.rowcount)) 
                    await self.connection.commit()
                    return cursor.rowcount > 0
            except db.connection.Error as err:
                print(f"Fout bij uitvoeren van query: {err}")
                return False
            finally:
                await cursor.close()
        else:
            print("Niet verbonden met de database. Maak eerst verbinding m.b.v. de connect()-functie")

    async def close(self):
        if self.connection:
            await self.connection.close()
            #print("Databaseverbinding gesloten.")
        else:
            print("Er is geen actieve databaseverbinding om te sluiten.")

