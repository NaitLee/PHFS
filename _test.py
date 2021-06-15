#!/usr/bin/python3
import os
from tplLib import Interpreter
from classesLib import UniParam

os.chdir(os.path.dirname(__file__) or '.')

itp = Interpreter()
print(itp.parse_text('{.time.}', UniParam([])).content)
