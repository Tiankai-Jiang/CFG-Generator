def func():
    try:
        while n > 1:
            n -= 1
    except TypeError as te:
        if x > 1:
            d += 1
        else:
            e += 1
    except ValueError as ve:
        b += 1
    except ZeroDivisionError as ze:
        raise ZeroDivisionError
    else:
        c += 1
    finally:
        d += 1

    n += 1
    for i in range(10):
        print(1)