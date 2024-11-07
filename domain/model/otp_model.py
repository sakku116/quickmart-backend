from .base_model import MyBaseModel

class OtpModel(MyBaseModel):
    _coll_name = "otps"

    code: str = ""