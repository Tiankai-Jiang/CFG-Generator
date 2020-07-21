import argparse
import os
from cfg import CFGVisitor
import _ast, ast, astor
from astpretty import pprint
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
    file_names = ["test_emptyclass.py", "example2.py", "example3.py", "example4.py"]
    example_path = os.path.abspath(os.getcwd()) + "/test_emptyclass.py"
    with open(example_path, 'r') as f:
        a = f.read()
        print(type(a))
        tree = ast.parse(a)
        # pprint(tree)
        cfg = CFGVisitor().build("Project", tree)
        cfg.show()

