#!/usr/bin/env python

from curbed_printer import Curbed_Printer

class SGScripter:
    tabstop = 4
    delimiter = "$$"
    printer_limit = 80
    printer_items_per_line = -1

    def __init__(self, tabstop=4, delimiter="$$", printer_limit=80, printer_items_per_line=-1):
        self.tabstop = tabstop
        self.printer_limit = printer_limit
        self.printer_items_per_line = printer_items_per_line

    def field_prohibits_nulls(self, field):
        return field["IS_NULLABLE"] == "NO"

    def field_is_primary_key(self, field):
        return "PRI" in field["COLUMN_KEY"]

    def field_is_unsigned(self, field):
        return 'unsigned' in field["COLUMN_TYPE"]

    def field_is_auto_increment(self, field):
        return 'auto_increment' in field["EXTRA"]

    def field_is_autonumber_primary_key(self, field):
        return (self.field_is_primary_key(field)
                and self.field_is_auto_increment(field))
    
    def get_autonumber_primary_key(self, fields):
        """ Find the integer primary key field for a list of fields.
        """
        for field in fields:
            if (self.field_is_autonumber_primary_key(field)):
                return field

        return None

    def print_proc_top(self, proc_name):
        """ Print the conditional procedure delete, followed by the
        CREATE PROCEDURE statement with formatted parameters taken
        from the fields parameter.

        Args:
           proc_name (string):   Full name of the procedure

        Returns:
           Number of characters to open parenthesis of proc declaration
        """
        declare_text = "CREATE PROCEDURE {} (".format(proc_name)
        declare_len = len(declare_text)

        print("DROP PROCEDURE IF EXISTS {} {}".format(proc_name, self.delimiter))
        print(declare_text, end="")

        return declare_len


    def get_type_string_from_field(self, field, keep_null=False, enum_as_varchar=False):
        """ Generate a procedure parameter appropriate type string.

        The string returned from this function is appropriate for describing
        the data type of a parameter of a stored procedure.  A procedure
        parameter has no need for AUTO_INCREMENT or key attributes, and these
        will not be included in the output string.

        Args:
           field (dictionary): A information_schema.COLUMNS record that describes
                               a field of a table.
           keep_null (boolean, optional): Include `NOT NULL` in output if field
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
        unsigned = 'unsigned' in field["COLUMN_TYPE"]

        notnull = field["IS_NULLABLE"] == "NO"

        # autoinc = 'auto_increment' in field["EXTRA"]
        # prikey = 'PRI' in field["COLUMN_KEY"]

        char_max_len = field["CHARACTER_MAXIMUM_LENGTH"]
        

        if 'INT' in data_type:
            stype.append(data_type)
            if self.field_is_unsigned(field):
                stype.append("UNSIGNED")
        elif 'CHAR' in data_type:
            stype.append("{}({})".format(data_type, char_max_len))
        elif data_type == 'NUMERIC' or data_type == 'DECIMAL':
            precision = field["NUMERIC_PRECISION"]
            scale = field["NUMERIC_SCALE"]
            stype.append("NUMERIC({},{})".format(precision, scale))
        elif data_type == "ENUM":
            if enum_as_varchar:
                stype.append("VARCHAR({})".format(char_max_len))
            else:
                stype.append(field["COLUMN_TYPE"].replace('enum', 'ENUM', 1))
        elif data_type == "SET":
            stype.append(field["COLUMN_TYPE"].replace('set', 'SET', 1))
        else:
            stype.append(data_type)

        return " ".join(stype)

    def print_proc_params(self, indent_len, fields):
        items = []
        for field in fields:
            item = "{} {}".format(field["COLUMN_NAME"],
                                  self.get_type_string_from_field(field))
            items.append(item)

        printer = Curbed_Printer(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(")")
        
    def print_list_param_names(self, indent_len, fields, prefix='', end='\n'):
        items = []
        for field in fields:
            items.append( prefix + field["COLUMN_NAME"] )

        printer = Curbed_Printer(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(end, end="")

    def print_list_sets(self, indent_len, fields, autonumber_field, prefix='', end='\n'):
        items = []
        for field in fields:
            if (field != autonumber_field):
                fname = field["COLUMN_NAME"]
                items.append("{}{} = {}".format(prefix, fname, fname))
            
        printer = Curbed_Printer(indent_len,
                                 self.printer_limit,
                                 items_per_line = self.printer_items_per_line)

        printer.print(items)
        print(end, end="")

    def print_to_indent(self, indent_len, indented_string, end='\n'):
        space_count = indent_len - len(indented_string)
        print ( (' ' * space_count) + indented_string, end=end)

    def print_proc_list(self, fields, table_name, proc_name):

        autonumber_field = self.get_autonumber_primary_key(fields)
        
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

            from_string = table_name + " " + table_alias
            self.print_to_indent(select_indent_len, "FROM ", end=from_string + "\n")

            where_string = autonumber_name + " IS NULL"
            self.print_to_indent(select_indent_len, "WHERE ", end=where_string + "\n")

            or_string = table_prefix + autonumber_name + " = " + autonumber_name
            self.print_to_indent(select_indent_len, "OR ", end=or_string + ";\n")

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
        self.print_proc_params(params_indent_len, fields)
        print("BEGIN")

        # Insert statement:
        insert_string = tab1 + "INSERT INTO {} (".format(table_name)
        names_indent_len = len(insert_string)
        print(insert_string, end='')
        self.print_list_param_names(names_indent_len, fields, end=")\n")
        # Indent VALUES(... enough to line up value names with parameter names
        values_string = "VALUES ("
        print(' ' * (names_indent_len - len(values_string)) + values_string, end='')
        self.print_list_param_names(names_indent_len, fields, end=");\n")

        if (confirm_proc_name is not None):
            print()
            print(tab1 + "IF ROW_COUNT() > 0 THEN")
            print( (tab1 * 2) + "CALL {}(LAST_INSERT_ID());".format(confirm_proc_name))
            print(tab1 + "END IF;")
            
        print("END " + self.delimiter)

    def print_proc_read(self, fields, table_name, proc_name):
        autonumber_field = self.get_autonumber_primary_key(fields)
        
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
            self.print_list_param_names(select_indent_len, fields, prefix=table_prefix, end=")\n")

            from_string = table_name + " " + table_alias
            self.print_to_indent(select_indent_len, "FROM ", end=from_string + "\n")
            
            where_string = table_prefix + autonumber_name + " = " + autonumber_name
            self.print_to_indent(select_indent_len, "WHERE ", end=where_string + ";\n")
        
            print("END " + self.delimiter)

    def print_proc_update(self, fields, table_name, proc_name, confirm_proc_name=None):
        autonumber_field = self.get_autonumber_primary_key(fields)
        
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
            self.print_to_indent(fields_indent_len, "SET ", end="")
            self.print_list_sets(fields_indent_len, fields, autonumber_field, prefix=table_prefix)
                        
            where_string = table_prefix + autonumber_name + " = " + autonumber_name
            self.print_to_indent(fields_indent_len, "WHERE ", end=where_string + ";\n")

            if (confirm_proc_name is not None):
                print()
                print(tab1 + "IF ROW_COUNT() > 0 THEN")
                print(tab1 * 2 + "CALL " + confirm_proc_name + "(" + autonumber_name + ");")
                print(tab1 + "END IF;")
            
            print("END " + self.delimiter)

    def print_proc_delete(self, fields, table_name, proc_name):
            autonumber_field = self.get_autonumber_primary_key(fields)
            
            if autonumber_field is None:
                print("-- Can't generate update procedure without autonumber primary key field.")
                print()
            else:
                tab1 = ' ' * self.tabstop

                param_fields = [autonumber_field]

                autonumber_name = autonumber_field["COLUMN_NAME"]
                table_alias = table_name[0:1]
                table_prefix = table_alias + "."

                params_indent_len = self.print_proc_top(proc_name)
                self.print_proc_params(params_indent_len, param_fields)
                print("BEGIN")

                delete_str = tab1 + "DELETE FROM "
                indent_len = len(delete_str)

                delete_target = "{} USING {} AS {}\n".format(table_alias,
                                                             table_name,
                                                             table_alias)
                
                print(delete_str, end=delete_target)

                # WHERE
                where_clause = table_alias + "." + autonumber_name + " = " + autonumber_name + ";\n"
                self.print_to_indent(indent_len, "WHERE ", end=where_clause)
                print()

                # Report outcome
                print(tab1 + "SELECT ROW_COUNT() AS deleted;")
                print("END " + self.delimiter)

    def get_calling_dictionary(self, table, name_prefix):
        """Generate a dictionary of lists for indirect generation of basic scripts.
        Args:
           table (string):      Name of table
           name_prefix(string): Prefix of procedure names to be generated

        Returns:
           (dictionary): Mapping of procedure types to list of
                         values to be used to call a procedure to generate
                         the type's procedure code.
        """
        types = [ "list", "add", "read", "update", "delete" ];
        dict = {}

        for type in types:
            method_name = "print_proc_" + type
            method_reference = getattr(self, method_name)
            proc_name = name_prefix + "_" + type.capitalize()

            # add and update type procedures always generate the
            # target record after a successful operation so the client
            # can update its representation of said record with the
            # most current version
            args = [method_reference, table, proc_name]
            if type == "add" or type == "update":
                args.append(name_prefix + "_List")

            dict[type] = args

        return dict
        
