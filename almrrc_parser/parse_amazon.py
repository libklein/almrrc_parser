# coding=utf-8
import datetime
import json
from pathlib import Path
from typing import Optional, Tuple

from .models import Package, Dimensions, Route, Stop, StopType, StopID, RouteID


def parse_dimensions(dimension_data: dict[str, float]) -> Dimensions:
    return Dimensions(width=dimension_data['width_cm'], height=dimension_data['height_cm'],
                      depth=dimension_data['depth_cm'])


def parse_time(time: float | str) -> Optional[datetime.datetime]:
    if isinstance(time, float):
        return None
    return datetime.datetime.fromisoformat(time)


def parse_time_window(time_window_data: dict[str, float]) -> Optional[Tuple[datetime.datetime, datetime.datetime]]:
    start_time, end_time = parse_time(time_window_data['start_time_utc']), parse_time(time_window_data['end_time_utc'])
    return (start_time, end_time) if start_time is not None and end_time is not None else None


def parse_package(package_id: str, package_data: dict) -> Package:
    package_dimensions = parse_dimensions(package_data['dimensions'])

    return Package(id=package_id, dimensions=package_dimensions,
                   service_time=package_data['planned_service_time_seconds'],
                   time_window=parse_time_window(package_data['time_window']))


def parse_route_packages(route_package_data: dict) -> dict[str, list[Package]]:
    route_packages: dict[str, list[Package]] = {}
    for stop_id, stop_package_data in route_package_data.items():
        route_packages[stop_id] = []
        for package_id, package_data in stop_package_data.items():
            route_packages[stop_id].append(parse_package(package_id, package_data))
    return dict(route_packages)


def parse_stop(stop_id: str, route_id: str, stop_packages: list[Package],
               stop_data: dict) -> Stop:
    stop_type = StopType.STATION if stop_data['type'] != 'Dropoff' else StopType.DROPOFF
    return Stop(id=stop_id, route_id=route_id, type=stop_type,
                lat=stop_data['lat'], lon=stop_data['lng'],
                requested_parcel=stop_packages)


def parse_stops(route_id: str, stops_data: dict,
                route_packages: dict[str, list[Package]]) -> dict[StopID, Stop]:
    return {
        stop_id: parse_stop(stop_id=stop_id, route_id=route_id, stop_packages=route_packages[stop_id], stop_data=stop_data)
        for stop_id, stop_data in stops_data.items()
    }


def parse_route_stops(route_id: RouteID, route_data: dict,
                      route_packages: dict[StopID, list[Package]],
                      route_sequence: list[StopID]) -> Route:
    start_date = datetime.datetime.fromisoformat(f'{route_data["date_YYYY_MM_DD"]} {route_data["departure_time_utc"]}')
    capacity = route_data["executor_capacity_cm3"]
    stops = parse_stops(route_id=route_id,
                        stops_data=route_data['stops'],
                        route_packages=route_packages)
    station = next(x for x in stops.values() if x.is_station)
    del stops[station.id]
    return Route(id=route_id, start_time=start_date, vehicle_capacity=capacity, station=station, stops=stops,
                 original_order=route_sequence)


def parse_routes(routes_data: dict,
                 route_packages: dict[RouteID, dict[StopID, list[Package]]],
                 route_sequences: dict[RouteID, list[StopID]]) -> list[Route]:
    return [
        parse_route_stops(route_id=route_id, route_data=route_data,
                          route_packages=route_packages[route_id],
                          route_sequence=route_sequences[route_id])
        for route_id, route_data in routes_data.items()
    ]


def parse_packages(route_packages_data: dict) -> dict[str, dict[str, list[Package]]]:
    return {
        route_id: parse_route_packages(route_package_data=route_package_data)
        for route_id, route_package_data in route_packages_data.items()
    }


def parse_route_sequence(route_sequence_data: dict[StopID, int]) -> list[StopID]:
    return [stop[0] for stop in sorted(route_sequence_data.items(), key=lambda x: x[1])]


def parse_sequences(route_sequences_data: dict) -> dict[RouteID, list[StopID]]:
    route_sequences = dict()
    for route_id, route_sequence_data in route_sequences_data.items():
        route_sequences[route_id] = parse_route_sequence(route_sequence_data['actual'])
    return route_sequences


def parse(route_data_path: Path, package_data_path: Path, travel_time_data_path: Path, sequence_data_path: Path):
    with package_data_path.open() as package_data_file:
        package_data = parse_packages(json.load(package_data_file))

    with sequence_data_path.open() as sequence_data_file:
        route_sequences = parse_sequences(json.load(sequence_data_file))

    for route_id in package_data:
        assert route_id in route_sequences

    with route_data_path.open() as route_data_file:
        routes_data = parse_routes(routes_data=json.load(route_data_file), route_packages=package_data,
                                   route_sequences=route_sequences)

    with travel_time_data_path.open() as route_travel_time_file:
        route_travel_times = json.load(route_travel_time_file)

    return routes_data, route_travel_times
