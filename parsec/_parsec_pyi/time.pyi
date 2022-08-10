class DateTime:
    """
    A class representing DateTime
    """

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None: ...
    def __repr__(self) -> str: ...
    def __lt__(self, other: DateTime) -> bool: ...
    def __gt__(self, other: DateTime) -> bool: ...
    def __le__(self, other: DateTime) -> bool: ...
    def __ge__(self, other: DateTime) -> bool: ...
    def __lt__(self, other: DateTime) -> bool: ...
    def __eq__(self, other: DateTime) -> bool: ...
    def __ne__(self, other: DateTime) -> bool: ...
    def __hash__(self) -> int: ...
    def __sub__(self, other: DateTime) -> int: ...
    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def day(self) -> int: ...
    @property
    def hour(self) -> int: ...
    @property
    def minute(self) -> int: ...
    @property
    def second(self) -> int: ...
    def now() -> DateTime: ...
    def from_timestamp(ts: float) -> DateTime: ...
    def timestamp(self) -> float: ...
    def add(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> DateTime: ...
    def subtract(
        self,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        microseconds: int = 0,
    ) -> DateTime: ...
    def to_local(self) -> LocalDateTime: ...

class LocalDateTime:
    """
    A class representing LocalDateTime
    """

    def __init__(
        self, year: int, month: int, day: int, hour: int, minute: int, second: int
    ) -> None: ...
    @property
    def year(self) -> int: ...
    @property
    def month(self) -> int: ...
    @property
    def day(self) -> int: ...
    @property
    def hour(self) -> int: ...
    @property
    def minute(self) -> int: ...
    @property
    def second(self) -> int: ...
    def from_timestamp(ts: float) -> LocalDateTime: ...
    def timestamp(self) -> float: ...
