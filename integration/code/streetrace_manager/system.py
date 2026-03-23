from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .mission_planning import MissionPlanningModule
from .race_management import RaceManagementModule
from .registration import RegistrationModule
from .reputation import ReputationModule
from .results import ResultsModule
from .vehicle_maintenance import VehicleMaintenanceModule


class StreetRaceManager:
    def __init__(self, opening_cash: int = 0) -> None:
        self.registration = RegistrationModule()
        self.crew_management = CrewManagementModule(self.registration)
        self.inventory = InventoryModule(opening_cash=opening_cash)
        self.race_management = RaceManagementModule(self.crew_management, self.inventory)
        self.results = ResultsModule(self.race_management, self.inventory)
        self.mission_planning = MissionPlanningModule(self.crew_management)

        self.vehicle_maintenance = VehicleMaintenanceModule(self.crew_management, self.inventory)
        self.reputation = ReputationModule()

    def register_member(self, name: str) -> None:
        self.registration.register_member(name)

    def assign_role(self, name: str, role: str, skill_level: int) -> None:
        self.crew_management.assign_role_and_skill(name, role, skill_level)

    def add_car(self, car_id: str, model: str) -> None:
        self.inventory.add_car(car_id, model)

    def create_race(self, race_id: str, name: str, driver_name: str, car_id: str) -> None:
        self.race_management.create_race(race_id, name, driver_name, car_id)

    def complete_race(self, race_id: str, position: int, prize_money: int, car_damaged: bool) -> None:
        self.results.record_result(race_id, position, prize_money, car_damaged)
        self.reputation.update_after_race(position)

    def plan_and_start_mission(self, mission_id: str, mission_type: str, required_roles: list[str]) -> None:
        self.mission_planning.plan_mission(mission_id, mission_type, required_roles)
        self.mission_planning.start_mission(mission_id)
