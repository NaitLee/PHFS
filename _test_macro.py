#!/usr/bin/python3

import sys
from tplLib import Interpreter
from classesLib import UniParam

itp = Interpreter()
print(itp.parse_text(sys.argv[1], UniParam([], interpreter=itp)).content)
