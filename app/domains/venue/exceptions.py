class VenueNotFound(Exception):
    """Площадка не найдена."""


class VenueArchiveBlocked(Exception):
    """Нельзя архивировать площадку: есть опубликованные мероприятия."""


class VenueDeleteBlocked(Exception):
    """Нельзя удалить площадку со статусом active."""


class VenueZoneNotFound(Exception):
    """Зона площадки не найдена."""


class ZoneTypeChangeBlocked(Exception):
    """Нельзя менять тип зоны: у зоны уже есть места."""


class VenueZoneSeatNotFound(Exception):
    """Место в зоне не найдено."""


class SeatedSeatMissingNumber(Exception):
    """Для seated-зоны хотя бы одно из полей row / seat_number обязательно."""


class ZoneNotSeated(Exception):
    """Генерация мест по layout доступна только для зон типа seated."""


class SeatsAlreadyExist(Exception):
    """Для этой зоны уже существуют места. Используйте replace=True для замены."""


class LayoutExceedsCapacity(Exception):
    """Суммарное количество мест в layout превышает capacity зоны."""
