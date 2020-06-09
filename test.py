import argparse
import os
from cfg import CFGVisitor
import _ast, ast, astor
import interpreter

# ToDo: open file from command line
'''
parser = argparse.ArgumentParser(description='Generate the control flow graph\
 of a Python program')
parser.add_argument('input_file', help='Path to a file containing a Python\
 program for which the CFG must be generated')
parser.add_argument('output_file', help='Path to a file where the produced\
 visualisation of the CFG must be saved')

args = parser.parse_args()
cfg_name = args.input_file.split('/')[-1]
'''

if __name__ == '__main__':
    current_path = os.path.abspath(os.getcwd()) + "/exampleCode.py"
    with open(current_path, 'r') as f:
        cfg = CFGVisitor().build("project", ast.parse(f.read()))
        cfg.show()