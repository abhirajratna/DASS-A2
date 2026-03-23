from .models import Car


class InventoryModule:
    def __init__(self, opening_cash: int = 0) -> None:
        self._cars: dict[str, Car] = {}
        self._spare_parts: dict[str, int] = {}
        self._tools: dict[str, int] = {}
        self._cash_balance = opening_cash

    def add_car(self, car_id: str, model: str) -> Car:
        if car_id in self._cars:
            raise ValueError(f"Car '{car_id}' already exists")
        car = Car(car_id=car_id, model=model)
        self._cars[car_id] = car
        return car

    def get_car(self, car_id: str) -> Car:
        if car_id not in self._cars:
            raise ValueError(f"Car '{car_id}' not found")
        return self._cars[car_id]

    def add_spare_part(self, part_name: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        self._spare_parts[part_name] = self._spare_parts.get(part_name, 0) + quantity

    def add_tool(self, tool_name: str, quantity: int) -> None:
        if quantity < 0:
            raise ValueError("Quantity cannot be negative")
        self._tools[tool_name] = self._tools.get(tool_name, 0) + quantity

    def update_cash(self, amount: int) -> int:
        self._cash_balance += amount
        return self._cash_balance

    def get_cash_balance(self) -> int:
        return self._cash_balance
