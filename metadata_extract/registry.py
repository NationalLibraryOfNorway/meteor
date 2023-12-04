""" Authority Registry

This module contains all classes and methods related to the registry database.
"""


from typing import TypedDict, Optional, Union
import sqlite3
from mysql.connector import MySQLConnection


class DBCredentials(TypedDict):
    """Credentials for MySQL database"""
    host: str
    user: str
    database: str
    password: str


class RegistryType(TypedDict):
    """Data class for registry entries"""
    authId: int
    name: str


class PublisherRegistry:
    """Class handling connection and querying into the registry database"""

    def __init__(self,
                 registry_file: Optional[str] = None,
                 db_credentials: Optional[DBCredentials] = None):
        self.connection: Union[sqlite3.Connection, MySQLConnection]
        if registry_file:
            self.connection = sqlite3.connect(registry_file, check_same_thread=False)
            self.field = "LOWER(O1.name)"
        elif db_credentials:
            self.connection = MySQLConnection(host=db_credentials['host'],
                                              user=db_credentials['user'],
                                              database=db_credentials['database'],
                                              password=db_credentials['password'])
            self.field = "O1.lower_name"
        else:
            raise RuntimeError("Missing database settings for registry")
        self.cursor = self.connection.cursor()

    def search(self, pattern: str) -> list[RegistryType]:
        """Search the database for occurrences of pattern.

        The search is case insensitive. Returns a list of matching entities, with
        preferred name form of highest category at the top.
        """

        if isinstance(self.connection, MySQLConnection):
            self.connection.ping(reconnect=True)

        escaped_pattern = pattern.lower().replace("'", "''")
        self.cursor.execute(
            "SELECT DISTINCT O1.id, O2.name FROM " +
            "organizations O1 JOIN organizations O2 USING(id) " +
            f"WHERE {self.field} = '{escaped_pattern}' AND " +
            "O2.standard=1 ORDER BY O1.outdated, O1.standard DESC, O1.category DESC"
        )
        rows = self.cursor.fetchall()
        results: list[RegistryType] = []
        for auth_id, name in rows:
            if not isinstance(name, str):
                raise RuntimeError(f"Wrong type from db for name {type(name)}")
            if not isinstance(auth_id, str) and not isinstance(auth_id, int):
                raise RuntimeError(f"Wrong type from db for id {type(auth_id)}")
            results.append(
                RegistryType({
                    'authId': int(auth_id),
                    'name': name
                })
            )
        return results
