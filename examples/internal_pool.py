"""
Test the internal pool and creating instances of the User Model
"""
from postDB import Model, Column, types, exceptions

import asyncio


DB_URI: str = "..."
# PostgreSQL database uri.
# Must be provided to run the example.


loop = asyncio.get_event_loop()


class User(Model):
    id = Column(types.Serial, primary_key=True)
    username = Column(types.String)
    email = Column(types.String, unique=True)

    async def insert(self):
        query = """
        INSERT INTO users (username, email)
        VALUES ($1, $2)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
        """
        record = await self.pool.fetchrow(query, self.username, self.email)
        if record is None:
            raise exceptions.UniqueViolationError(
                "A user with this email already exists."
            )

        setattr(self, "id", record["id"])


async def main():
    try:
        await Model.create_pool(uri=DB_URI)
    except ValueError:
        print("[!] Error: Invalid DB uri provided.")
        exit(1)

    await User.create_table(verbose=True)

    user = User(username="notreal", email="notreal@gmail.com")

    try:
        await user.insert()
    except exceptions.UniqueViolationError as e:
        print("[!] ERROR: ", e)

    print(await Model.pool.fetch("SELECT * FROM users"))

    try:
        await asyncio.wait_for(Model.pool.close(), timeout=3.0)
    except asyncio.TimeoutError:
        print("Exiting by timeout...")


if __name__ == "__main__":
    loop.run_until_complete(main())
