def func1(x, y = 10):
    return x + 5


def func2(x):
    return x - 5


def fib():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

a = fib(10)
b = func2(5)
