from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict


@dataclass(frozen=True)
class Connection:
    """A single unidirectional connection:  from_fmu.var  →  to_fmu.var"""
    from_fmu: str
    from_var: str
    to_fmu: str
    to_var: str

    @staticmethod
    def _split(endpoint: str) -> tuple[str, str]:
        """
        Split an endpoint of the form 'FMU_NAME.variable_name'
        into ('FMU_NAME', 'variable_name').

        Raises ValueError if the endpoint is malformed.
        """
        try:
            fmu, var = endpoint.split(".", maxsplit=1)
        except ValueError:        # no dot or too many dots ?
            raise ValueError(
                f"Endpoint '{endpoint}' must be of the form <FMU>.<variable>"
            ) from None
        if not fmu or not var:
            raise ValueError(f"Endpoint '{endpoint}' is missing FMU or variable name")
        return fmu, var

    @classmethod
    def from_raw(cls, raw: Dict[str, str]) -> "Connection":
        """Create a Connection from a raw dict with keys 'from' and 'to'."""
        from_fmu, from_var = cls._split(raw["from"])
        to_fmu,   to_var   = cls._split(raw["to"])
        return cls(from_fmu, from_var, to_fmu, to_var)


def parse_connections(raw_connections: Iterable[Dict[str, str]]) -> List[Connection]:
    """
    Convert a list of raw dicts (e.g. loaded from YAML) into Connection objects.

    >>> raw = [
    ...   {"from": "LOC_SYSTEM.OUTPUT_temperature_cold_circuit_outlet",
    ...    "to":   "LOC_CNTRL_v2_customPI.INPUT_temperature_lube_oil"},
    ...   {"from": "LOC_CNTRL_v2_customPI.OUTPUT_control_valve_position",
    ...    "to":   "LOC_SYSTEM.INPUT_control_valve_position"},
    ... ]
    >>> conns = parse_connections(raw)
    >>> conns[0].from_fmu, conns[0].from_var
    ('LOC_SYSTEM', 'OUTPUT_temperature_cold_circuit_outlet')
    """
    return [Connection.from_raw(item) for item in raw_connections]
