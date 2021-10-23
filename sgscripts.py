#!/usr/bin/env python

class SGScripter:
    tabstop = 4
    delimiter = "$$"

    def __init__(self, tabstop=4):
        self.tabstop = tabstop

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
    

    def get_type_string_from_field(self, field):
        """
        
        """
        stype = []
        notnull = field["IS_NULLABLE"] == "NO"

        autoinc = 'auto_increment' in field["EXTRA"]
        prikey = 'PRI' in field["COLUMN_KEY"]
        unsigned = 'unsigned' in field["COLUMN_TYPE"]

        data_type = field["DATA_TYPE"].upper()
        

        if ( 'INT' in data_type ):
            stype.append(data_type)
            if ( self.field_is_unsigned(field) ):
                stype.append("UNSIGNED")
        elif ( 'CHAR' in data_type ):
            stype.append("{}({})".format(data_type,
                                         field["CHARACTER_MAXIMUM_LENGTH"]))
        else:
            stype.append(data_type)

        return " ".join(stype)

    def get_autonumber_primary_key(self, fields):
        for field in fields:
            if (self.field_is_autonumber_primary_key(field)):
                return field

        return None


    def print_proc_params(self, indent_len, fields):
        params_indent = ""
        for field in fields:
            if (params_indent == ""):
                params_indent = ' ' * indent_len
            else:
                print(",\n" + params_indent, end='')
                
            print ("{} {}".format(field["COLUMN_NAME"],
                                  self.get_type_string_from_field(field)),
                   end='')

        print(")")

    def print_list_param_names(self, indent_len, fields, prefix='', end='\n'):
        params_indent = ""
        for field in fields:
            if (params_indent == ""):
                params_indent = ' ' * indent_len
            else:
                print(",\n" + params_indent, end='')
                
            print (prefix + field["COLUMN_NAME"], end='')

        print(end, end='')

    def print_to_indent(self, indent_len, indented_string, end='\n'):
        space_count = indent_len - len(indented_string)
        print ( (' ' * space_count) + indented_string, end=end)

    def print_proc_list(self, table_name, proc_name, fields):

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
        
        
    def print_proc_add(self, table_name, proc_name, fields, confirm_proc_name=None):
        """ Print out conventional Proc_Add procedure that adds
        a new record and if `confirm_proc_name` is not None,
        a call to `confirm_proc_name` with the INSERT_ID() value.

        Args:
           proc_name (string):         Full name of the procedure
           fields    (array):          Collection of field description dictionaries
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
        self.print_list_param_names(names_indent_len, fields, end=")\n")

        if (confirm_proc_name is not None):
            print()
            print(tab1 + "IF ROW_COUNT() > 0 THEN")
            print( (tab1 * 2) + "CALL {}(LAST_INSERT_ID());".format(confirm_proc_name))
            print(tab1 + "END IF;")
            
        print("END " + self.delimiter)

    def print_proc_read(self, table_name, proc_name, fields):
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

    def print_proc_update(self, table_name, proc_name, fields, confirm_proc_name=None):
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
            next_indent = 0
            for field in fields:
                if (field != autonumber_field):
                    field_name = field["COLUMN_NAME"]
                    print( ' ' * next_indent + table_prefix + field_name + " = " + field_name)
                    if (next_indent == 0):
                        next_indent = fields_indent_len
                        
            where_string = table_prefix + autonumber_name + " = " + autonumber_name
            self.print_to_indent(fields_indent_len, "WHERE ", end=where_string + ";\n")

            if (confirm_proc_name is not None):
                print()
                print(tab1 + "IF ROW_COUNT() > 0 THEN")
                print(tab1 * 2 + "CALL " + confirm_proc_name + "(" + autonumber_name + ");")
                print(tab1 + "END IF;")
            
            print("END " + self.delimiter)

