class CompanyNotFound(Exception):
    """Компания не найдена."""


class CompanyAlreadyExists(Exception):
    """Компания с таким именем уже существует у этого пользователя."""


class CompanyOwnerNotFound(Exception):
    """У компании не найден владелец (OWNER) в CompanyMembers."""


class TransferTargetNotMember(Exception):
    """Пользователь, которому передаётся владение, не является членом компании."""


class AlreadyOwner(Exception):
    """Пользователь уже является владельцем компании."""
