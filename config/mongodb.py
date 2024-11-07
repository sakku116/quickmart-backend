from pymongo import MongoClient
from pymongo.database import Database
from fastapi import Depends

from .env import Env


def getMongoDB() -> Database:
    conn = MongoClient(Env.MONGODB_URI)
    return conn[Env.MONGODB_NAME]

class MongodbClient:
    conn: MongoClient = None
    db: Database = None

    @classmethod
    def init(cls):
        cls.conn = MongoClient(Env.MONGODB_URI)
        cls.db = cls.conn[Env.MONGODB_NAME]

    @classmethod
    def close(cls):
        cls.conn.close()
