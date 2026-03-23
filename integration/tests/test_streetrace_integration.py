import pytest

from streetrace_manager import StreetRaceManager


def test_register_driver_then_enter_race_success() -> None:
    manager = StreetRaceManager(opening_cash=1000)
    manager.register_member("Ari")
    manager.assign_role("Ari", "driver", 8)
    manager.add_car("C1", "Nissan Skyline")

    manager.create_race("R1", "Harbor Sprint", "Ari", "C1")

    race = manager.race_management.get_race("R1")
    assert race.driver_name == "Ari"
    assert race.car_id == "C1"
    assert race.status == "scheduled"


def test_enter_race_without_registered_driver_fails() -> None:
    manager = StreetRaceManager()
    manager.add_car("C2", "Toyota Supra")

    with pytest.raises(ValueError, match="not registered"):
        manager.create_race("R2", "Tunnel Run", "Blaze", "C2")


def test_complete_race_updates_result_rankings_and_inventory_cash() -> None:
    manager = StreetRaceManager(opening_cash=500)
    manager.register_member("Nova")
    manager.assign_role("Nova", "driver", 9)
    manager.add_car("C3", "Mazda RX-7")
    manager.create_race("R3", "Midnight Circuit", "Nova", "C3")

    manager.complete_race("R3", position=1, prize_money=300, car_damaged=False)

    race = manager.race_management.get_race("R3")
    assert race.status == "completed"
    assert race.position == 1
    assert manager.results.get_ranking_points("Nova") == 10
    assert manager.inventory.get_cash_balance() == 800


def test_damaged_car_mission_requires_mechanic_before_proceeding() -> None:
    manager = StreetRaceManager(opening_cash=1000)
    manager.register_member("Rex")
    manager.assign_role("Rex", "driver", 7)
    manager.add_car("C4", "Honda Civic")
    manager.create_race("R4", "Dock Drift", "Rex", "C4")
    manager.complete_race("R4", position=2, prize_money=150, car_damaged=True)

    with pytest.raises(ValueError, match="mechanic"):
        manager.plan_and_start_mission("M1", "rescue", ["mechanic"])

    manager.register_member("Mia")
    manager.assign_role("Mia", "mechanic", 8)
    manager.mission_planning.plan_mission("M2", "repair_support", ["mechanic"])
    mission = manager.mission_planning.start_mission("M2")
    assert mission.status == "in_progress"
    assert mission.assigned_members["mechanic"] == "Mia"


def test_mission_cannot_start_if_required_roles_unavailable() -> None:
    manager = StreetRaceManager()
    manager.register_member("Ivy")
    manager.assign_role("Ivy", "driver", 6)
    manager.mission_planning.plan_mission("M3", "delivery", ["driver", "strategist"])

    with pytest.raises(ValueError, match="strategist"):
        manager.mission_planning.start_mission("M3")
