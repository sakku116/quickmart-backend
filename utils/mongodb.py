import logging

from pymongo.database import Database

from domain.model import user_model
import os
import importlib
import inspect
from utils import helper
from domain.model.base_model import MyBaseModel

from core.logging import logger


def ensureIndexes(db: Database):
    logger.info("Ensuring mongodb collection indexes")

    model_filenames = os.listdir("domain/model")
    logger.debug(f"found model files: {model_filenames}")
    for filename in model_filenames:
        if filename.endswith(".py") and filename.removesuffix(".py") not in [
            "__init__",
            "base_model",
        ]:
            module_path = __import__(
                f"domain.model.{filename[:-3]}", fromlist=[filename[:-3]]
            )
            for member_name, member in inspect.getmembers(module_path):
                if (
                    inspect.isclass(member)
                    and member_name.lower().endswith("model")
                    and member_name != "BaseModel"  # exclude pydantic.BaseModel
                ):
                    try:
                        member: MyBaseModel = member()
                        coll_name = member._coll_name
                        indexes = member._default_indexes + member._custom_indexes
                        logger.info(f"\tEnsuring index for '{coll_name}' collection")
                        existing_indexes = list(db[coll_name].list_indexes())
                        for index in indexes:
                            logger.info("\t\tchecking if index is exist")
                            for i, key in enumerate(index.keys.copy()):
                                keyname = key[0]
                                keytype = key[1]
                                for exist in existing_indexes:
                                    if (
                                        keyname in exist.get("key", {})
                                        and exist.get("key", {})[keyname] == keytype
                                        and exist.get("unique", False) == index.unique
                                    ):
                                        logger.info(
                                            f"\t\t\tindex already exist: {index.model_dump()}"
                                        )

                                        # remove from index
                                        index.keys.pop(i)

                            if len(index.keys) != 0:
                                logger.info(f"\t\tindex: {index.model_dump()}")
                                db[coll_name].create_index(**index.model_dump())
                                logger.info(f"\t\tcreated index: {index.model_dump()}")
                    except Exception as e:
                        logger.warning(f"\tFailed to create index: {e}")
