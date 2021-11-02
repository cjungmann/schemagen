#!/usr/bin/env python

"""The resident class, CurbedPrinter, is a tool for printing text
   within right- and left-side restrictions, including right-justified
   text for SQL keywords in an SQL statement.
"""

class CurbedPrinter:
    """Class for restricted printing."""
    # saved constructor arguments:
    indent = 0
    limit = 0
    separator = ','
    first_indent = 0

    # derived values
    len_separator = 0
    text_length = 0
    items_limit = 0

    def __init__(self, indent, limit, separator=", ", first_indent=0, items_per_line=-1):
        """Constructor for CurbedPrinter

        Args:
           indent (integer):       spaces to position before which some text is right-justified,
                                   and after which other text will be printed, up to `limit`
                                   characters for the line
           limit (integer):        character position beyond which the class attempts to prevent
                                   printing
           separator (string):     text that will be inserted between list items
           first_indent (integer): indent value for first line, defaulting to 0 since the
                                   typical usage starts after introductory text on the same line
           items_per_line (integer): restriction of items per line, defaulting to -1 for
                                     unrestricted.  The other typical value would be 1 for
                                     singleton items for easier post-generation editing.

        Returns:
           None
        """
        #pylint: disable=redefined-outer-name
        self.indent = indent
        self.limit = limit
        self.separator = separator
        self.first_indent = first_indent

        self.len_separator = len(separator)
        self.text_length = limit - indent
        self.items_limit = items_per_line if items_per_line > 0 else 0xFFFFFF
        #pylint: enable=redefined-outer-name

    def print_ruler(self):
        """Visual aid for testing output (to confirm conformance to restrictions)."""
        for position in range(1, self.limit+1):
            val = position % 10
            if val == 0:
                print("[32;1m", end="")

            print(f"{val}", end="")

            if val==0:
                print("[m", end="")

        print()

    def print_line(self, items_subset, first=False, final=False):
        """Prints a line of text.

        Args:
           items_subset (list): list of items to print, precalculated to conform to
                                restrictions
           first (boolean):     flag if printing first line
           last  (boolean):     flag if printing last line

        Returns:
           None
        """
        spaces = self.indent
        if (first and self.first_indent != self.indent):
            spaces = self.first_indent
        else:
            spaces = self.indent

        print((spaces * ' '), end='')
        print(self.separator.join(items_subset), end = '' if final else ',\n')

    def print(self, items, end='\n'):
        """Main class method, prints all items with given restrictions.

        Args:
           items (list):    complete list of items to print
           end (string):    conform to python printing standard to allow
                            the omission of a terminating newline

        Returns:
           None
        """
        line = []
        accrued = 0
        first_line = True
        item_count = 0

        for item in items:
            itemlen = len(item) + self.len_separator
            newlen = accrued + itemlen

            if newlen <= self.text_length and item_count < self.items_limit:
                line.append(item)
                accrued = newlen
                item_count += 1
            else:
                self.print_line(line, first=first_line)
                first_line = False
                line = [item]
                accrued = itemlen
                item_count = 1

        if len(line) > 0:
            self.print_line(line, first=first_line, final = True)

        print(end, end="")


if __name__ == "__main__":
    # Testing section that is only active during standalone running of this script.
    test_items = [ "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                   "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
                   "seventeen", "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two",
                   "twenth-three", "twenty-four", "twenty-five", "twenty-six", "twenty-seven",
                   "twenty-eight", "twenty-nine", "thirty", "thirty-one", "thirty-two",
                   "twenth-three", "thirty-four", "thirty-five", "thirty-six", "thirty-seven",
                   "thirty-eight", "thirty-nine", "forty", "forty-one", "forty-two",
                   "twenth-three", "forty-four", "forty-five", "forty-six", "forty-seven",
                   "forty-eight", "forty-nine" ]

    TINDENT = 12

    # Make a printer object
    printer = CurbedPrinter(TINDENT, 80, items_per_line=5)

    # For confirming line length a position 'ruler'.
    printer.print_ruler()

    # Fake a line prefix
    print((TINDENT-1) * '_' + "(", end='')
    printer.print(test_items)

    # Terminate the parenthetical group
    print(')')
