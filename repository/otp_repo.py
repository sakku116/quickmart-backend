from core.logging import logger
from fastapi import Depends
from domain.model import otp_model
from config.mongodb import MongodbClient
from pymongo import ReturnDocument
from typing import Union


class OtpRepo:
    def __init__(self, mongo_db: MongodbClient = Depends()):
        self.user_coll = mongo_db.db[otp_model.OtpModel()._coll_name]

    def create(self, data: otp_model.OtpModel):
        return self.user_coll.insert_one(data.model_dump())

    def update(
        self, id: str, data: otp_model.OtpModel
    ) -> Union[otp_model.OtpModel, None]:
        _return = self.user_coll.find_one_and_update(
            {"id": id},
            {"$set": data.model_dump(exclude=["id"])},
            return_document=ReturnDocument.AFTER,
        )

        return otp_model.OtpModel(**_return) if _return else None

    def delete(self, id: str) -> Union[otp_model.OtpModel, None]:
        _return = self.user_coll.find_one_and_delete({"id": id})
        return otp_model.OtpModel(**_return) if _return else None

    def getLatestByCreatedBy(self, created_by: str) -> Union[otp_model.OtpModel, None]:
        _return = list(
            self.user_coll.find({"created_by": created_by}).sort("created_at", -1).limit(1)
        )
        return otp_model.OtpModel(**_return[0]) if len(_return) > 0 else None

    def deleteManyByCreatedBy(self, created_by: str) -> int:
        _return = self.user_coll.delete_many({"created_by": created_by})
        return _return.deleted_count