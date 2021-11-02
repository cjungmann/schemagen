#!/usr/bin/env python

""" SGScripter class, uses table columns information to generate
stored procedure code for CRUD operations: List, Add (Create), Read, Update,
and Delete.
"""

# This non-error error is reported because we're not
# in the same directory as the main source file.
#pylint: disable=import-error
from curbedprinter import CurbedPrinter
#pylint: enable=import-error


def print_to_indent(indent_len, indented_string, start="", end='\n'):
    """Prints `indented_string` right-aligned to `indent_len`.
    Args:
       indent_len (integer):     column position on which to justify `indented_string`
       indented_string (string): string to left-justify
       start (string, optional): string to begin string, default empty string
       end (string, optional):   string to end string, default to newline
    Returns:
       None
"""
    space_count = indent_len - len(indented_string)
    print ( start + (' ' * space_count) + indented_string, end=end)

def field_prohibits_nulls(field):
    """Test function indicates if the field is nullable."""
    return field["IS_NULLABLE"] == "NO"

def field_is_primary_key(field):
    """Test function indicating if the field is a primary key."""
    return "PRI" in field["COLUMN_KEY"]

def field_is_unsigned(field):
    """Test function indicating if the field is unsigned (integer)."""
    return 'unsigned' in field["COLUMN_TYPE"]

def field_is_auto_increment(field):
    """Test function indicating if the field is auto-incrementing."""
    return 'auto_increment' in field["EXTRA"]

def field_is_autonumber_primary_key(field):
    """Test function indicating if the field is a auto-numbering primary key."""
    return (field_is_primary_key(field)
            and field_is_auto_increment(field))

def get_autonumber_primary_key(fields):
    """ Find the integer primary key field for a list of fields.
    """
    for field in fields:
        if field_is_autonumber_primary_key(field):
            return field

    return None

def get_field_list_without_autonumber_primary_fields(fields):
    """Return a sublist of fields that does not include autonumber primary key fields."""
    new_fields = []
    for field in fields:
        if not field_is_autonumber_primary_key(field):
            new_fields.append(field)

    return new_fields

def get_type_string_from_field(field, keep_not_null=False, enum_as_varchar=False):
    """ Generate a procedure parameter appropriate type string.

    The string returned from this function is appropriate for describing
    the data type of a parameter of a stored procedure.  A procedure
    parameter has no need for AUTO_INCREMENT or key attributes, and these
    will not be included in the output string.

    Args:
       field (dictionary): A information_schema.COLUMNS record that describes
                           a field of a table.
       keep_not_null (boolean, optional): Include `NOT NULL` in output if field
                           has a `NOT NULL` description.  Defaults to False.
       enum_as_varchar (boolean, optional): False by default, which results in
                           the entire ENUM declaration for the parameter.  If
                           `enum_as_varchar` is True, the parameter type will
                           be converted to a VARCHAR of sufficient length to
                           contain the longest ENUM value.

    Returns:
       A parameter data type string.
    """
    stype = []

    data_type = field["DATA_TYPE"].upper()

    # autoinc = 'auto_increment' in field["EXTRA"]
    # prikey = 'PRI' in field["COLUMN_KEY"]

    char_max_len = field["CHARACTER_MAXIMUM_LENGTH"]

    if 'INT' in data_type:
        stype.append(data_type)
        if field_is_unsigned(field):
            stype.append("UNSIGNED")
    elif 'CHAR' in data_type:
        stype.append(f"{data_type}({char_max_len})")
    elif data_type in ['NUMERIC', 'DECIMAL']:
        precision = field["NUMERIC_PRECISION"]
        scale = field["NUMERIC_SCALE"]
        stype.append(f"NUMERIC({precision},{scale})")
    elif data_type == "ENUM":
        if enum_as_varchar:
            stype.append(f"VARCHAR({char_max_len})")
        else:
            stype.append(field["COLUMN_TYPE"].replace('enum', 'ENUM', 1))
    elif data_type == "SET":
        stype.append(field["COLUMN_TYPE"].replace('set', 'SET', 1))
    else:
        stype.append(data_type)

    if keep_not_null and field["IS_NULLABLE"] == "NO":
        stype.append("NOT NULL")

    return " ".join(stype)

def print_proc_and_confirm_fields(indent_len, table_prefix, confirm_fields, start="\n", end=""):
    """Print AND clauses for the confirm fields in the statment conditional.

    The fields in `confirm_fields` have a 'confirm_' prefix, and for each
    item in the `confirm_field` list, this function generates an AND clause
    comparing the field name with the variable with the same name without the
    prefix.

    The assumed preference is to prepend a newline rather than end with a
    newline so the terminating `;` can be easily added after the last
    subcondition.

    Args:
       indent_len (integer):     character position for right-justify for query
       table_prefix (string):    table alias + period in use for query
       confirm_fields (list):    'confirm_' prefixed fields which will be processed
       start (string):           text before indent, default is `\n`
       end (string):             text after output for python consistency,
                                 defaulting to an empty string

    Return:
       None

    """
    for field in confirm_fields:
        confirm_name = field["COLUMN_NAME"]
        colname = confirm_name.split("confirm_",1)[1]
        print_to_indent(indent_len,
                        "AND ",
                        start = start,
                        end = f"{table_prefix}{colname} = {confirm_name}{end}")

class SGScripter:
    """" Uses table columns to generate stored procedure code. """
    tabstop = 4
    delimiter = "$$"
    printer_limit = 80
    printer_items_per_line = -1

    def __init__(self, tabstop=4, delimiter="$$", printer_limit=80,
                 printer_items_per_line=-1):
        """Constructor with arguments that control formatting.
        Args:
           tabstop (integer, default=4):   number of characters for each tab stop
           delimiter (string, default=$$): delimiter that terminates stored
                                           procedure statements.
           printer_limit (integer, default=80): right-side character soft-limit,
                                           only when an item is too long to fit
                                           alone on the line will it pass this limit.
           printer_items_per_line (integer, default=-1): number of procedure
                                           parameters, add, select, or set fields
                                           per line (restricted by printer_limit).
                                           A value of -1 puts as many as fit per
                                           line.
        """
        self.tabstop = tabstop
        self.delimiter = delimiter
        self.printer_limit = printer_limit
        self.printer_items_per_line = printer_items_per_line

    def print_proc_top(self, proc_name):
        """ Print the conditional procedure delete, followed by the
        CREATE PROCEDURE statement with formatted parameters taken
        from the fields parameter.

        Args:
           proc_name (string):   Full name of the procedure

        Returns:
           Number of characters to open parenthesis of proc declaration
        """
        declare_text = f"CREATE PROCEDURE {proc_name} ("
        declare_len = len(declare_text)

        print(f"DROP PROCEDURE IF EXISTS {proc_name} {self.delimiter}")
        print(declare_text, end="")

        return declare_len


    def print_list_param_names(self, indent_len, fields, prefix='', end='\n'):
        """Print a list of field names (without type info) for a SQL statement."""
        items = []
        for field in fields:
            items.append( prefix + field["COLUMN_NAME"] )

        printer = CurbedPrinter(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(end, end="")

    def print_list_sets(self, indent_len, fields, prefix='', end='\n'):
        """Print the contents of a set data field."""
        items = []
        for field in fields:
            if not field_is_autonumber_primary_key(field):
                field_name = field["COLUMN_NAME"]
                items.append(f"{prefix}{field_name} = {field_name}")

        printer = CurbedPrinter(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(end, end="")

    def print_proc_params(self, indent_len, fields):
        """Print parameter list (field name + type info) for stored procedure declaration."""
        items = []
        for field in fields:
            keep_not_null = not field_is_autonumber_primary_key(field)

            param_type = get_type_string_from_field(field, keep_not_null=keep_not_null)
            item = f"{field['COLUMN_NAME']} {param_type}"
            items.append(item)

        printer = CurbedPrinter(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(")")

    def print_proc_list(self, fields, table_name, proc_name):
        """Print the stored procedure code for a LIST operation."""
        autonumber_field = get_autonumber_primary_key(fields)

        if autonumber_field is None:
            print("-- Can't generate list procedure without autonumber primary key field.")
            print()
        else:
            tab1 = ' ' * self.tabstop

            autonumber_list = [ autonumber_field ]
            autonumber_name = autonumber_field["COLUMN_NAME"]
            table_alias = table_name[0:1]
            table_prefix = table_alias + "."

            # Print procedure declaration
            params_indent_len = self.print_proc_top(proc_name)
            self.print_proc_params(params_indent_len, autonumber_list)
            print("BEGIN")

            select_string = tab1 + "SELECT "
            select_indent_len = len(select_string)
            print(select_string, end='')

            self.print_list_param_names(select_indent_len, fields, prefix=table_prefix)

            print_to_indent(select_indent_len,
                            "FROM ",
                            end = table_name + " " + table_alias + "\n")

            print_to_indent(select_indent_len,
                            "WHERE ",
                            end = autonumber_name + " IS NULL\n")

            print_to_indent(select_indent_len,
                            "OR ",
                            end = table_prefix + autonumber_name + " = " + autonumber_name + ";\n")

            print("END " + self.delimiter)


    def print_proc_add(self, fields, table_name, proc_name, confirm_proc_name=None):
        """ Print out conventional Proc_Add procedure that adds
        a new record and if `confirm_proc_name` is not None,
        a call to `confirm_proc_name` with the INSERT_ID() value.

        Args:
           fields    (array):          Collection of field description dictionaries
           table_name (string):        Name of table for which procedure is created
           proc_name (string):         Full name of the procedure
           confirm_proc_name (string): Name of procedure to call upon successful
                                       appending of a new record

        Returns:
           None
        """

        tab1 = ' ' * self.tabstop

        # Print procedure declaration
        params_indent_len = self.print_proc_top(proc_name)
        add_fields = get_field_list_without_autonumber_primary_fields(fields)
        self.print_proc_params(params_indent_len, add_fields)
        print("BEGIN")

        # Insert statement:
        insert_string = tab1 + f"INSERT INTO {table_name} ("
        names_indent_len = len(insert_string)
        print(insert_string, end='')
        self.print_list_param_names(names_indent_len, add_fields, end=")\n")
        # Indent VALUES(... enough to line up value names with parameter names
        values_string = "VALUES ("
        print(' ' * (names_indent_len - len(values_string)) + values_string, end='')
        self.print_list_param_names(names_indent_len, add_fields, end=");\n")

        if confirm_proc_name is not None:
            print()
            print(tab1 + "IF ROW_COUNT() > 0 THEN")
            print( (tab1 * 2) + f"CALL {confirm_proc_name}(LAST_INSERT_ID());")
            print(tab1 + "END IF;")

        print("END " + self.delimiter)

    def print_proc_read(self, fields, table_name, proc_name, confirm_fields):
        """Print stored procedure code to a READ operation."""
        autonumber_field = get_autonumber_primary_key(fields)

        if autonumber_field is None:
            print("-- Can't generate read procedure without autonumber primary key field.")
            print()
        else:
            tab1 = ' ' * self.tabstop

            autonumber_list = [ autonumber_field ]
            autonumber_name = autonumber_field["COLUMN_NAME"]
            table_alias = table_name[0:1]
            table_prefix = table_alias + "."

            params_indent_len = self.print_proc_top(proc_name)
            self.print_proc_params(params_indent_len, autonumber_list)
            print("BEGIN")

            select_string = tab1 + "SELECT ("
            select_indent_len = len(select_string)
            print(select_string, end='')

            select_list = fields.copy()
            select_list[1:1] = confirm_fields
            self.print_list_param_names(select_indent_len,
                                        select_list,
                                        prefix=table_prefix,
                                        end=")\n")

            print_to_indent(select_indent_len,
                            "FROM ",
                            end = table_name + " " + table_alias + "\n")

            print_to_indent(select_indent_len,
                            "WHERE ",
                            end = f"{table_prefix}{autonumber_name} = {autonumber_name};\n")

            print("END " + self.delimiter)

    def print_proc_update(self, fields, table_name, proc_name,
                          confirm_proc_name, confirm_fields):
        """Print the stored procedure code for an UPDATE operation."""
        autonumber_field = get_autonumber_primary_key(fields)

        if autonumber_field is None:
            print("-- Can't generate update procedure without autonumber primary key field.")
            print()
        else:
            tab1 = ' ' * self.tabstop

            autonumber_name = autonumber_field["COLUMN_NAME"]
            table_alias = table_name[0:1]
            table_prefix = table_alias + "."

            params_indent_len = self.print_proc_top(proc_name)
            self.print_proc_params(params_indent_len, fields)
            print("BEGIN")

            update_string = tab1 + "UPDATE "
            update_table = table_name + " " + table_alias
            fields_indent_len = len(update_string)
            print(update_string, end=update_table + "\n")

            # SETs
            print_to_indent(fields_indent_len, "SET ", end="")
            self.print_list_sets(fields_indent_len, fields, prefix=table_prefix)

            # Conditions
            print_to_indent(fields_indent_len,
                            "WHERE ",
                            end = f"{table_prefix}{autonumber_name} = {autonumber_name}")

            if len(confirm_fields) > 0:
                print_proc_and_confirm_fields(fields_indent_len, table_prefix, confirm_fields)

            # Require final newline since each condition line ends without one:
            print(";")

            if confirm_proc_name is not None:
                print()
                print(tab1 + "IF ROW_COUNT() > 0 THEN")
                print(tab1 * 2 + "CALL " + confirm_proc_name + "(" + autonumber_name + ");")
                print(tab1 + "END IF;")

            print("END " + self.delimiter)

    def print_proc_delete(self, fields, table_name, proc_name, confirm_fields):
        """Print the stored procedure code for a DELETE operation."""
        autonumber_field = get_autonumber_primary_key(fields)

        if autonumber_field is None:
            print("-- Can't generate update procedure without autonumber primary key field.")
            print()
        else:
            tab1 = ' ' * self.tabstop

            param_fields = [autonumber_field] + confirm_fields

            autonumber_name = autonumber_field["COLUMN_NAME"]
            table_alias = table_name[0:1]
            table_prefix = table_alias + "."

            params_indent_len = self.print_proc_top(proc_name)
            self.print_proc_params(params_indent_len, param_fields)
            print("BEGIN")

            delete_str = tab1 + "DELETE FROM "
            indent_len = len(delete_str)

            delete_target = f"{table_alias} USING {table_name} AS {table_alias}\n"

            print(delete_str, end=delete_target)

            # Conditions
            print_to_indent(indent_len,
                            "WHERE ",
                            end = f"{table_alias}.{autonumber_name} = {autonumber_name}")

            if len(confirm_fields) > 0:
                print_proc_and_confirm_fields(indent_len, table_prefix, confirm_fields)

            # Require final newline since each condition line ends without one:
            print(";\n")

            # Report outcome
            print(tab1 + "SELECT ROW_COUNT() AS deleted;")
            print("END " + self.delimiter)

    def get_calling_dictionary(self, table, name_prefix, confirm_fields):
        """Generate a dictionary of lists for indirect generation of basic scripts.
        Args:
           table (string):        Name of table
           name_prefix(string):   Prefix of procedure names to be generated
           confirm_fields (list): names of fields used to confirm writing operations
                                  that otherwise would procede with only a record id,
                                  those being update and delete.

        Returns:
           (dictionary): Mapping of procedure types to list of
                         values to be used to call a procedure to generate
                         the type's procedure code.
        """
        proc_types = [ "list", "add", "read", "update", "delete" ]
        procs_dict = {}

        for proc_type in proc_types:
            method_name = "print_proc_" + proc_type
            method_reference = getattr(self, method_name)
            proc_name = name_prefix + proc_type.capitalize()

            # add and update type procedures always generate the
            # target record after a successful operation so the client
            # can update its representation of said record with the
            # most current version
            args = [method_reference, table, proc_name]
            if proc_type in [ "add", "update" ]:
                args.append(name_prefix + "List")

            if proc_type in [ "read", "update", "delete" ]:
                args.append(confirm_fields)

            procs_dict[proc_type] = args

        return procs_dict
