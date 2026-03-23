from .inventory import InventoryModule
from .race_management import RaceManagementModule


class ResultsModule:
    def __init__(self, race_management: RaceManagementModule, inventory: InventoryModule) -> None:
        self._race_management = race_management
        self._inventory = inventory
        self._rankings: dict[str, int] = {}

    def record_result(self, race_id: str, position: int, prize_money: int, car_damaged: bool) -> None:
        if position < 1:
            raise ValueError("Position must be >= 1")
        race = self._race_management.get_race(race_id)
        race.status = "completed"
        race.position = position
        race.prize_money = prize_money
        race.car_damaged = car_damaged

        self._rankings[race.driver_name] = self._rankings.get(race.driver_name, 0) + (11 - min(position, 10))
        self._inventory.update_cash(prize_money)

        car = self._inventory.get_car(race.car_id)
        if car_damaged:
            car.status = "damaged"

    def get_ranking_points(self, driver_name: str) -> int:
        return self._rankings.get(driver_name, 0)
