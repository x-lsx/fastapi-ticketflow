class EventNotFound(Exception):
    """Мероприятие не найдено."""


class CapacityRequiredForStanding(Exception):
    """Для standing-зоны необходимо передать capacity."""


class SeatedZoneHasNoSeats(Exception):
    """У seated-зоны площадки нет мест — сначала запустите generate_seats."""
