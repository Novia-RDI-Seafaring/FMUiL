# connections.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Dict


# @dataclass(frozen=True)
class Connection:
    """A single unidirectional connection:  from_fmu.var  →  to_fmu.var"""
    source:   str
    operator: str
    value:    str

    def __init__(self, raw_connection):
        self._parse_connection(raw_connection)
        
    def _parse_connection(self, raw_connection):
        self.source, self.operator, self.value = raw_connection.split(" ")
        # print(raw_connection.split(" "))



def parse_connections(raw_connections):
    connection_dict = {}
    for connection in raw_connections:
        connection_dict[connection] = Connection(raw_connections[connection])    
    return connection_dict




