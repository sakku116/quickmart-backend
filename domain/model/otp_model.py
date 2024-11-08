from .base_model import MyBaseModel

class OtpModel(MyBaseModel):
    _coll_name = "otps"

    verified: bool = False
    code: str = ""