from pydantic import BaseModel


class DigitalTwinBase(BaseModel):
    name: str


class DigitalTwinCreate(DigitalTwinBase):
    financial_profile: dict


from typing import Optional


class DigitalTwin(DigitalTwinBase):
    id: int
    user_id: int
    simulation_results: Optional[dict]

    class Config:
        from_attributes = True
