from fastapi import Depends
from config.mongodb import MongodbClient
from domain.model import user_model
from pymongo import ReturnDocument
from typing import Union


class UserRepo:
    def __init__(self, mongo_db: MongodbClient = Depends()):
        self.user_coll = mongo_db.db[user_model.UserModel()._coll_name]

    def create(self, data: user_model.UserModel):
        return self.user_coll.insert_one(data.model_dump())

    def update(
        self, id: str, data: user_model.UserModel
    ) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one_and_update(
            {"id": id},
            {"$set": data.model_dump(exclude=["id"])},
            return_document=ReturnDocument.AFTER,
        )

        return user_model.UserModel(**_return) if _return else None

    def updateEmailVerified(self, id: str, email_verified: bool) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one_and_update(
            {"id": id},
            {"$set": {"email_verified": email_verified}},
            return_document=ReturnDocument.AFTER,
        )

        return user_model.UserModel(**_return) if _return else None

    def updateLastActive(self, id: str, last_active: int) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one_and_update(
            {"id": id},
            {"$set": {"last_active": last_active}},
            return_document=ReturnDocument.AFTER,
        )

        return user_model.UserModel(**_return) if _return else None

    def delete(self, id: str) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one_and_delete({"id": id})
        return user_model.UserModel(**_return) if _return else None

    def getById(self, id: str) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one({"id": id})
        return user_model.UserModel(**_return) if _return else None

    def getByUsername(self, username: str) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one({"username": username})
        return user_model.UserModel(**_return) if _return else None

    def getByEmail(self, email: str) -> Union[user_model.UserModel, None]:
        _return = self.user_coll.find_one({"email": email})
        return user_model.UserModel(**_return) if _return else None
