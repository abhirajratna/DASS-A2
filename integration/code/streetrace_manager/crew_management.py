from .models import CrewMember
from .registration import RegistrationModule


class CrewManagementModule:
    def __init__(self, registration: RegistrationModule) -> None:
        self._registration = registration

    def assign_role_and_skill(self, name: str, role: str, skill_level: int) -> CrewMember:
        if not self._registration.is_registered(name):
            raise ValueError(f"Cannot assign role: member '{name}' is not registered")
        if skill_level < 1 or skill_level > 10:
            raise ValueError("Skill level must be between 1 and 10")
        member = self._registration.get_member(name)
        member.role = role
        member.skill_level = skill_level
        return member

    def has_role_available(self, role: str) -> bool:
        return any(member.role == role for member in self._registration.list_members())

    def member_has_role(self, name: str, role: str) -> bool:
        member = self._registration.get_member(name)
        return member.role == role

    def find_member_by_role(self, role: str) -> CrewMember:
        for member in self._registration.list_members():
            if member.role == role:
                return member
        raise ValueError(f"No member available with role '{role}'")
