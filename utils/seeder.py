from config.mongodb import getMongoDB
from domain.model import user_model
from repository import user_repo
from utils import bcrypt as bcrypt_utils
from config.env import Env
from core.logging import logger
from utils import helper

def seedInitialUsers(user_repo: user_repo.UserRepo):
    users: list[user_model.UserModel] = []
    time_now = helper.timeNowEpoch()
    if Env.INITIAL_CUSTOMER_USER_USERNAME and Env.INITIAL_CUSTOMER_USER_PASSWORD:
        users.append(
            user_model.UserModel(
                id=helper.generateUUID4(),
                created_at=time_now,
                fullname=Env.INITIAL_CUSTOMER_USER_USERNAME.title().replace("_", " "),
                username=Env.INITIAL_CUSTOMER_USER_USERNAME,
                email=f"{Env.INITIAL_CUSTOMER_USER_USERNAME}@gmail.com",
                password=bcrypt_utils.hashPassword(Env.INITIAL_CUSTOMER_USER_PASSWORD),
                role="customer",
            )
        )

    if Env.INITIAL_SELLER_USER_USERNAME and Env.INITIAL_SELLER_USER_PASSWORD:
        users.append(
            user_model.UserModel(
                id=helper.generateUUID4(),
                created_at=time_now,
                fullname=Env.INITIAL_SELLER_USER_USERNAME.title().replace("_", " "),
                username=Env.INITIAL_SELLER_USER_USERNAME,
                email=f"{Env.INITIAL_SELLER_USER_USERNAME}@gmail.com",
                password=bcrypt_utils.hashPassword(Env.INITIAL_SELLER_USER_PASSWORD),
                role="seller",
            )
        )

    if Env.INITIAL_ADMIN_USER_USERNAME and Env.INITIAL_ADMIN_USER_PASSWORD:
        users.append(
            user_model.UserModel(
                id=helper.generateUUID4(),
                created_at=time_now,
                fullname=Env.INITIAL_ADMIN_USER_USERNAME.title().replace("_", " "),
                username=Env.INITIAL_ADMIN_USER_USERNAME,
                email=f"{Env.INITIAL_ADMIN_USER_USERNAME}@gmail.com",
                password=bcrypt_utils.hashPassword(Env.INITIAL_ADMIN_USER_PASSWORD),
                role="admin",
            )
        )

    for user in users:
        logger.info(f"Seeding initial user: {user.username}")
        existing = user_repo.getByUsername(user.username) or user_repo.getByEmail(user.email) or None
        if existing:
            logger.warning(f"User @{user.username} ({user.email}) already exists")
            continue

        user_repo.create(user)