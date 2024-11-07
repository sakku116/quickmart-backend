from fastapi import Depends
from config.mongodb import MongodbClient
from domain.model import refresh_token_model
from pymongo import ReturnDocument
from typing import Union


class RefreshTokenRepo:
    def __init__(self, mongo_db: MongodbClient = Depends()):
        self.user_coll = mongo_db.db[refresh_token_model.RefreshTokenModel()._coll_name]

    def create(self, data: refresh_token_model.RefreshTokenModel):
        return self.user_coll.insert_one(data.model_dump())

    def update(
        self, id: str, data: refresh_token_model.RefreshTokenModel
    ) -> Union[refresh_token_model.RefreshTokenModel, None]:
        _return = self.user_coll.find_one_and_update(
            {"id": id},
            {"$set": data.model_dump(exclude=["id"])},
            return_document=ReturnDocument.AFTER,
        )

        return refresh_token_model.RefreshTokenModel(**_return) if _return else None

    def delete(self, id: str) -> Union[refresh_token_model.RefreshTokenModel, None]:
        _return = self.user_coll.find_one_and_delete({"id": id})
        return refresh_token_model.RefreshTokenModel(**_return) if _return else None

    def deleteManyByCreatedBy(
        self, created_by: str
    ) -> int:
        _return = self.user_coll.delete_many({"created_by": created_by})
        return _return.deleted_count

    def getById(self, id: str) -> Union[refresh_token_model.RefreshTokenModel, None]:
        _return = self.user_coll.find_one({"id": id})
        return refresh_token_model.RefreshTokenModel(**_return) if _return else None
