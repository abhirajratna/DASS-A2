from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CrewMember:
    name: str
    role: str | None = None
    skill_level: int | None = None


@dataclass
class Car:
    car_id: str
    model: str
    status: str = "ready"


@dataclass
class Race:
    race_id: str
    name: str
    driver_name: str
    car_id: str
    status: str = "scheduled"
    prize_money: int = 0
    position: int | None = None
    car_damaged: bool = False


@dataclass
class Mission:
    mission_id: str
    mission_type: str
    required_roles: List[str] = field(default_factory=list)
    assigned_members: Dict[str, str] = field(default_factory=dict)
    status: str = "planned"
