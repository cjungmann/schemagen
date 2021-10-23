#!/usr/bin/env python

import pymysql
import pymysql.cursors

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
    global arg_dict
    return pymysql.connect(host = host,
                           user = user,
                           password = password,
                           database = "information_schema",
                           cursorclass = pymysql.cursors.DictCursor)

def generate_table_columns_query(conn, database, table):
    """ Generates an SQL expression for collecting table field data.
    Args:
       conn (object): Open MySQL connection
    Returns:
       string query
    """
    global arg_dict
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

def generate_database_tables_list_query(conn, database):
    """ Generate an SQL expression for collecting table names in database.
    Args:
       conn (object): Open MySQL connection
    Returns:
       string query
    """
    global arg_dict

    qtemplate="""
SELECT TABLE_NAME
  FROM information_schema.TABLES
 WHERE TABLE_SCHEMA = '{}' """

    return qtemplate.format(database)

    
def collect_table_columns(conn, database, table):
    """ Collect table fields into a reusable structure.
    Args:
       conn (object): open mysql connection

    Returns:
       List of dictionaries describing the columns
    """
    query = generate_table_columns_query(conn, database, table)

    table_def=[]

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                table_def.append(row)

            return table_def;

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

def display_tables(conn):
    print("We should be printing table names right now.")

def display_procs(conn):
    print("We should be printing procedure names right now.")

def show_table_names(conn, database):
    """ Display list of tables for given database.
        This function is called if no table name was given.

    Args:
       conn (object): open mysql connection

    Returns:
       None
    """
    global arg_dict
    print("[32;1mTables in database '{}'[m".format(database) )
    query = generate_database_tables_list_query(conn, database)
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                print(row["TABLE_NAME"]);

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise

def show_database_names(conn):
    """ Display list of databases in the host
        This function is called if neither table nor database name given.
    Args:
       conn (object): open mysql connection

    Returns:
       None
    """
    query = "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA"
    print("[32;1mDatabase Names[m")
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                print(row["SCHEMA_NAME"]);

    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise
