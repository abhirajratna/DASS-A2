from .crew_management import CrewManagementModule
from .inventory import InventoryModule
from .models import Race


class RaceManagementModule:
    def __init__(self, crew_management: CrewManagementModule, inventory: InventoryModule) -> None:
        self._crew_management = crew_management
        self._inventory = inventory
        self._races: dict[str, Race] = {}

    def create_race(self, race_id: str, name: str, driver_name: str, car_id: str) -> Race:
        if race_id in self._races:
            raise ValueError(f"Race '{race_id}' already exists")

        if not self._crew_management.member_has_role(driver_name, "driver"):
            raise ValueError(f"Member '{driver_name}' is not eligible as driver")

        car = self._inventory.get_car(car_id)
        if car.status != "ready":
            raise ValueError(f"Car '{car_id}' is not race-ready")

        race = Race(race_id=race_id, name=name, driver_name=driver_name, car_id=car_id)
        self._races[race_id] = race
        return race

    def get_race(self, race_id: str) -> Race:
        if race_id not in self._races:
            raise ValueError(f"Race '{race_id}' not found")
        return self._races[race_id]
