from .models import CrewMember


class RegistrationModule:
    def __init__(self) -> None:
        self._members: dict[str, CrewMember] = {}

    def register_member(self, name: str) -> CrewMember:
        if name in self._members:
            raise ValueError(f"Member '{name}' is already registered")
        member = CrewMember(name=name)
        self._members[name] = member
        return member

    def is_registered(self, name: str) -> bool:
        return name in self._members

    def get_member(self, name: str) -> CrewMember:
        if name not in self._members:
            raise ValueError(f"Member '{name}' is not registered")
        return self._members[name]

    def list_members(self) -> list[CrewMember]:
        return list(self._members.values())
