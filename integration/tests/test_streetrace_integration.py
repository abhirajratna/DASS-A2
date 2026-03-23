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


def test_assign_role_without_registration_fails() -> None:
    manager = StreetRaceManager()

    with pytest.raises(ValueError, match="not registered"):
        manager.assign_role("Ghost", "driver", 5)


def test_only_driver_role_can_be_entered_in_race() -> None:
    manager = StreetRaceManager()
    manager.register_member("Zen")
    manager.assign_role("Zen", "mechanic", 8)
    manager.add_car("C5", "Mitsubishi Lancer")

    with pytest.raises(ValueError, match="not eligible as driver"):
        manager.create_race("R5", "Neon Dash", "Zen", "C5")


def test_damaged_car_needs_repair_before_next_race_and_repair_cost_applies() -> None:
    manager = StreetRaceManager(opening_cash=1000)
    manager.register_member("Kai")
    manager.assign_role("Kai", "driver", 9)
    manager.register_member("Bolt")
    manager.assign_role("Bolt", "mechanic", 7)
    manager.add_car("C6", "BMW M3")

    manager.create_race("R6", "Riverline", "Kai", "C6")
    manager.complete_race("R6", position=3, prize_money=200, car_damaged=True)

    with pytest.raises(ValueError, match="not race-ready"):
        manager.create_race("R7", "Aftershock", "Kai", "C6")

    manager.vehicle_maintenance.repair_car("C6", repair_cost=120)
    assert manager.inventory.get_cash_balance() == 1080
    manager.create_race("R7", "Aftershock", "Kai", "C6")
    assert manager.race_management.get_race("R7").status == "scheduled"


def test_mission_start_with_multiple_roles_assigns_correct_members() -> None:
    manager = StreetRaceManager()
    manager.register_member("Luna")
    manager.assign_role("Luna", "driver", 8)
    manager.register_member("Orion")
    manager.assign_role("Orion", "strategist", 9)

    manager.mission_planning.plan_mission("M4", "intel_run", ["driver", "strategist"])
    mission = manager.mission_planning.start_mission("M4")

    assert mission.status == "in_progress"
    assert mission.assigned_members == {"driver": "Luna", "strategist": "Orion"}


def test_reputation_updates_after_race_and_mission_outcome() -> None:
    manager = StreetRaceManager()
    manager.register_member("Astra")
    manager.assign_role("Astra", "driver", 9)
    manager.add_car("C7", "Audi R8")
    manager.create_race("R8", "Coastal Rush", "Astra", "C7")

    manager.complete_race("R8", position=2, prize_money=100, car_damaged=False)
    assert manager.reputation.get_reputation() == 4

    manager.reputation.update_after_mission(success=True)
    assert manager.reputation.get_reputation() == 7
