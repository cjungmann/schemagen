#!/usr/bin/env python

class Curbed_Printer:
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
        self.indent = indent
        self.limit = limit
        self.separator = separator
        self.first_indent = first_indent

        self.len_separator = len(separator)
        self.text_length = limit - indent
        self.items_limit = items_per_line if items_per_line > 0 else 0xFFFFFF

    def print_ruler(self):
        for x in range(1, self.limit+1):
            val = x % 10
            if val == 0:
                print("[32;1m", end="")

            print("{}".format(val), end="")

            if val==0:
                print("[m", end="")

        print()
        
    def print_line(self, items, first=False, final=False):
        indent = self.indent
        if (first and self.first_indent != self.indent):
            indent = self.first_indent
        else:
            indent = self.indent

        print((indent * ' '), end='')
        print(self.separator.join(items), end = '' if final else ',\n')

    def print(self, items, end='\n'):
        line = []
        accrued = 0
        first_line = True
        item_count = 0

        for i, item in enumerate(items):
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

if __name__ == "__main__":
    items = [ "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
              "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
              "seventeen", "eighteen", "nineteen", "twenty", "twenty-one", "twenty-two",
              "twenth-three", "twenty-four", "twenty-five", "twenty-six", "twenty-seven",
              "twenty-eight", "twenty-nine", "thirty", "thirty-one", "thirty-two",
              "twenth-three", "thirty-four", "thirty-five", "thirty-six", "thirty-seven",
              "thirty-eight", "thirty-nine", "forty", "forty-one", "forty-two",
              "twenth-three", "forty-four", "forty-five", "forty-six", "forty-seven",
              "forty-eight", "forty-nine" ]

    indent = 12
    
    # Make a printer object
    printer = Curbed_Printer(indent, 80, items_per_line=5)

    # For confirming line length a position 'ruler'.
    printer.print_ruler()

    # Fake a line prefix
    print((indent-1) * '_' + "(", end='')
    printer.print(items)

    # Terminate the parenthetical group
    print(')')
        

    
        
