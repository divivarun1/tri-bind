from typing import Optional, Literal
from pydantic import BaseModel, Field

class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=3, max_length=64)
    device_type: str = Field(min_length=1, max_length=64)
    context_id: str
    firmware_hash: str = Field(min_length=64, max_length=64)
    credential: str = Field(min_length=8)

class IdentityVerify(BaseModel):
    challenge: str
    response: str

class FirmwareVerify(BaseModel):
    current_firmware_hash: str = Field(min_length=64, max_length=64)

class ContextVerify(BaseModel):
    context_id: str

class CbotGenerate(BaseModel):
    firmware_hash: str = Field(min_length=64, max_length=64)

class CbotVerify(BaseModel):
    token: str

class TelemetryIn(BaseModel):
    packet_rate: float = Field(ge=0)
    communication_frequency: float = Field(ge=0)
    destination: str
    port: int = Field(ge=1, le=65535)
    protocol: str
    connection_success: float = Field(ge=0, le=1)
    scanning: bool = False
    lateral_movement: bool = False

class AttackSim(BaseModel):
    device_id: str
    attack_type: Literal['rogue_device','cloned_device','stolen_credential','cbot_replay','cbot_tampering','firmware_tampering','context_mismatch','network_scanning','lateral_movement','compromised_legitimate_device']
