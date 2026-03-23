from .crew_management import CrewManagementModule
from .inventory import InventoryModule


class VehicleMaintenanceModule:
    def __init__(self, crew_management: CrewManagementModule, inventory: InventoryModule) -> None:
        self._crew_management = crew_management
        self._inventory = inventory

    def repair_car(self, car_id: str, repair_cost: int = 0) -> None:
        if not self._crew_management.has_role_available("mechanic"):
            raise ValueError("Repair cannot proceed: mechanic unavailable")

        car = self._inventory.get_car(car_id)
        if car.status != "damaged":
            raise ValueError(f"Car '{car_id}' is not damaged")

        self._inventory.update_cash(-repair_cost)
        car.status = "ready"
