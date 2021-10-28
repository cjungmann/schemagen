#!/usr/bin/env python

"""This module includes several functions for accessing MySQL/MariaDB."""

import pymysql
import pymysql.cursors

import re
import socket   # For resolving host names

reip = re.compile("\d{1,3}(\.\d{1,3}){3}")

def resolve_host(host):
    """Attempt to resolve an IP address from a host name.

    Args:
       host (string):  host string, may be IP address or host name, for which will be resolved

    Returns:
       (string): An IP address or None if a hostname cannot be resolved
    """
    if reip.match(host):
        return host
    else:
        try:
            return socket.gethostbyname(host)
        except socket.gaierror as error:
            print(f"Failed to resolve an ip address for {host} ({error.str()})")

    return None

def make_connection(host, user, password):
    """ Uses values in global arg_dict to open a MySql connection.

    For the purposes of this application, the only database we
    need is 'information_schema', which contains table and
    procedure definitions we will use to generate scripts.

    Args:
       host (string):     IP address of MySQL host
       user (string):     MySQL user name
       password (string): MySQL password

    Returns:
      None
    """
    return pymysql.connect(host = resolve_host(host),
                           user = user,
                           password = password,
                           database = "information_schema",
                           cursorclass = pymysql.cursors.DictCursor)

def prep_query_table_columns(database, table):
    """ Generates an SQL expression for collecting table field data.
    Args:
       database (string):  Name of the database
       table (string):     Name of the table
    Returns:
       string query
    """
    colnames=[
        "COLUMN_NAME",
        "DATA_TYPE",
        "CHARACTER_MAXIMUM_LENGTH",
        "NUMERIC_PRECISION",
        "NUMERIC_SCALE",
        "IS_NULLABLE",
        "COLUMN_KEY",
#        "DATATIME_PRECISION",
        "COLUMN_TYPE",
        "EXTRA"
    ]

    qtemplate="""
SELECT {}
  FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA = '{}'
   AND TABLE_NAME = '{}'"""

    return qtemplate.format(", ".join(colnames), database, table)

def prep_query_tables_list(database):
    """ Generate an SQL expression for collecting table names in database.
    Args:
       database (string):  Name of the database
    Returns:
       string query
    """
    qtemplate="""
SELECT TABLE_NAME
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = '{}' """

    return qtemplate.format(database)

def prep_query_procedures_list(database):
    """Generate an SQL expression for collecting procedure names in database.
    Args:
       database (string): Name of the databse
    Returns:
       string query
    """
    qtemplate="""
SELECT ROUTINE_NAME
  FROM information_schema.ROUTINES
 WHERE ROUTINE_SCHEMA = '{}' """

    return qtemplate.format(database)
    

def collect_table_columns(conn, database, table):
    """ Collect table fields into a reusable structure.
    Args:
       conn (object): open mysql connection

    Returns:
       List of dictionaries describing the columns
    """
    query = prep_query_table_columns(database, table)

    table_def=[]

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                table_def.append(row)

            return table_def

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

def get_list_of_table_names(conn, database):
    """ Returns a list of tables for given database.

    Args:
       conn (object):     open mysql connection
       database (string): Name of database

    Returns:
       list of table names
    """
    query = prep_query_tables_list(database)
    list = None
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            list = []
            rows = cur.fetchall()
            for row in rows:
                list.append(row["TABLE_NAME"])

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return list

def get_list_of_procedure_names(conn, database):
    """Returns a list of procedures for given database.

    Args:
       conn (object):     open mysql connection
       database (string): Name of database

    Returns:
       list of procedure names
    """
    print("[32;1mProcedures in database '{}'[m".format(database) )
    list = None
    query = prep_query_procedures_list(database)
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            list = []
            rows = cur.fetchall()
            for row in rows:
                list.append(row["ROUTINE_NAME"])

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return list

def get_list_of_database_names(conn):
    """ Returns a list of database names for the connection's host
    Args:
       conn (object): open mysql connection

    Returns:
       list of database names
    """
    list = None
    query = "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA"
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            list = []
            rows = cur.fetchall()
            for row in rows:
                list.append(row["SCHEMA_NAME"])

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

    return list
