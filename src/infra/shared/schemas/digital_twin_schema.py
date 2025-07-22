from pydantic import BaseModel


class DigitalTwinBase(BaseModel):
    name: str


class DigitalTwinCreate(DigitalTwinBase):
    financial_profile: dict


class DigitalTwin(DigitalTwinBase):
    id: int
    user_id: int
    simulation_results: dict | None

    class Config:
        from_attributes = True
