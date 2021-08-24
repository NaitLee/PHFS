#!/usr/bin/python3
import os
from tplLib import Interpreter
from classesLib import UniParam

os.chdir(os.path.dirname(__file__) or '.')

itp = Interpreter()
print(itp.parse_text('{.save|1.txt|1.}', UniParam([], interpreter=itp)).content)
