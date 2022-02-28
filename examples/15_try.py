try:
    b = b + 5
    c = c + 1
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
