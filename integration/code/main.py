from streetrace_manager import StreetRaceManager


def run_cli() -> None:
    manager = StreetRaceManager(opening_cash=0)
    print("StreetRace Manager CLI")
    print("Type 'help' to see commands. Type 'exit' to quit.")

    while True:
        raw = input("srm> ").strip()
        if not raw:
            continue
        if raw == "exit":
            print("Exiting StreetRace Manager.")
            break
        if raw == "help":
            print("register <name>")
            print("assign <name> <role> <skill_level>")
            print("addcar <car_id> <model words...>")
            print("createrace <race_id> <driver_name> <car_id> <race name words...>")
            print("completerace <race_id> <position> <prize_money> <damaged:true|false>")
            print("mission <mission_id> <mission_type> <roles comma separated>")
            print("showcash")
            print("showrep")
            continue

        parts = raw.split()
        cmd = parts[0]

        try:
            if cmd == "register" and len(parts) == 2:
                manager.register_member(parts[1])
                print("Member registered")
            elif cmd == "assign" and len(parts) == 4:
                manager.assign_role(parts[1], parts[2], int(parts[3]))
                print("Role assigned")
            elif cmd == "addcar" and len(parts) >= 3:
                manager.add_car(parts[1], " ".join(parts[2:]))
                print("Car added")
            elif cmd == "createrace" and len(parts) >= 5:
                manager.create_race(parts[1], " ".join(parts[4:]), parts[2], parts[3])
                print("Race created")
            elif cmd == "completerace" and len(parts) == 5:
                manager.complete_race(parts[1], int(parts[2]), int(parts[3]), parts[4].lower() == "true")
                print("Race completed")
            elif cmd == "mission" and len(parts) == 4:
                roles = [role.strip() for role in parts[3].split(",") if role.strip()]
                manager.plan_and_start_mission(parts[1], parts[2], roles)
                print("Mission started")
            elif cmd == "showcash" and len(parts) == 1:
                print(f"Cash balance: {manager.inventory.get_cash_balance()}")
            elif cmd == "showrep" and len(parts) == 1:
                print(f"Reputation: {manager.reputation.get_reputation()}")
            else:
                print("Invalid command. Use 'help' for syntax.")
        except ValueError as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    run_cli()
