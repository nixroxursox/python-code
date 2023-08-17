from typing import Dict

from starsessions import SessionStore


# instance of class which manages session persistence

class InMemoryStore(SessionStore):
    def __init__(self):
        self._storage = {}

    async def read(self, session_id: str, lifetime: int) -> Dict:
        """ Read session data from a data source using session_id. """
        return self._storage.get(session_id, {})

    async def write(self, session_id: str, data: Dict, lifetime: int, ttl: int) -> str:
        """ Write session data into data source and return session id. """
        self._storage[session_id] = data
        return session_id

    async def remove(self, session_id: str):
        """ Remove session data. """
        del self._storage[session_id]

    async def exists(self, session_id: str) -> bool:
        return session_id in self._storage