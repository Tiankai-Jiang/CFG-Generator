# ECE653-Project

A project to generate control flow graph for Python, written in Python3. The file cfg_orig.py is derived from [staticfg](https://github.com/coetaur0/staticfg) and is for comparison. cfg_orig.py has the exact same function as staticfg. cfg.py added support for 

- exception handling

- lambda expression

- generator expression

- list/set/dict comprehension

- for-else/while-else

- ... 

It also fixed some minor bugs in the original code.

# Dependencies

- Python3

- autopep8

- graphviz

- astor

# Usage

```python3 cfg.py code.py```

# Demo
```
try:
    b = b + 5
except KeyError:
    a += 1
except ZeroDivisionError:
    a += 2
else:
    a += 3
finally:
    b += 1
    a = a - b
    print('finish')
```
![tryExcept](report/img/try_after.png)