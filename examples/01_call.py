def func1(x, y=10):
    x += 1
    return x + 5


def func2(x=1, y=2, z=3, f=4):
    x += 1
    return x - 5


def fib(n):
    i = 1
    s = 0
    while i <= n:
        s += i
        i = i + 1
    return s


a = fib(10)
if a:
    b = func2(5)
else:
    func1(1)
