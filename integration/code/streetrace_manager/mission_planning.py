from .crew_management import CrewManagementModule
from .models import Mission


class MissionPlanningModule:
    def __init__(self, crew_management: CrewManagementModule) -> None:
        self._crew_management = crew_management
        self._missions: dict[str, Mission] = {}

    def plan_mission(self, mission_id: str, mission_type: str, required_roles: list[str]) -> Mission:
        if mission_id in self._missions:
            raise ValueError(f"Mission '{mission_id}' already exists")
        mission = Mission(mission_id=mission_id, mission_type=mission_type, required_roles=required_roles)
        self._missions[mission_id] = mission
        return mission

    def start_mission(self, mission_id: str) -> Mission:
        if mission_id not in self._missions:
            raise ValueError(f"Mission '{mission_id}' not found")

        mission = self._missions[mission_id]
        for role in mission.required_roles:
            if not self._crew_management.has_role_available(role):
                raise ValueError(f"Mission cannot start: required role '{role}' unavailable")

        assigned_members: dict[str, str] = {}
        for role in mission.required_roles:
            member = self._crew_management.find_member_by_role(role)
            assigned_members[role] = member.name

        mission.assigned_members = assigned_members
        mission.status = "in_progress"
        return mission
