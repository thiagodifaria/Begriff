from pydantic import BaseModel

class ConnectAccountRequest(BaseModel):
    id_banco: str
