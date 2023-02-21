# coding=utf-8
import datetime
from enum import IntEnum, auto
from typing import Optional, Tuple, List
from dataclasses import dataclass

CM = float
CM3 = float

StopID = str
RouteID = str
PackageID = str

class StopType(IntEnum):
    STATION = auto()
    DROPOFF = auto()

@dataclass(slots=True)
class Dimensions:
    width: CM
    height: CM
    depth: CM

    def __post_init__(self):
        assert self.width >= 0 and self.height >= 0 and self.depth >= 0

    @property
    def volume(self) -> CM3:
        return self.width * self.height * self.depth

@dataclass(slots=True)
class Package:
    id: PackageID
    dimensions: Dimensions
    service_time: float
    time_window: Optional[Tuple[datetime.datetime, datetime.datetime]]

    def __hash__(self):
        return hash(self.id)

    def __post_init__(self):
        assert self.service_time > 0
        assert self.time_window is None or self.time_window[0] < self.time_window[1]

    @property
    def volume(self) -> CM3:
        return self.dimensions.volume

    @property
    def earliest_start_of_service(self) -> datetime.datetime:
        return self.time_window[0]

    @property
    def latest_start_of_service(self) -> datetime.datetime:
        return self.time_window[1]

@dataclass(slots=True)
class Stop:
    id: StopID
    route_id: RouteID
    type: StopType
    lat: float
    lon: float
    requested_parcel: List[Package]

    def __hash__(self):
        return hash((self.route_id, self.id))

    def __post_init__(self):
        if self.is_station:
            assert len(self.requested_parcel) == 0
        else:
            assert len(self.requested_parcel) > 0

    @property
    def is_station(self):
        return self.type == StopType.STATION

@dataclass(slots=True)
class Route:
    id: RouteID
    start_time: datetime.datetime
    vehicle_capacity: CM3
    station: Stop
    stops: dict[StopID, Stop]
    original_order: Optional[List[StopID]]

    def __hash__(self):
        return hash(self.id)

    def __post_init__(self):
        assert self.station.is_station
        assert self.station.id not in self.stops
        if self.original_order is not None:
            assert self.original_order[0] == self.station.id

TravelTimeMatrix = dict[tuple[StopID, StopID], float]