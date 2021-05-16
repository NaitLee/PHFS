import sys
from tplLib import TplInterpreter
from classesLib import MacroParams

itp = TplInterpreter()
print(itp.parse_text(sys.argv[1], {}, MacroParams([])).content)
