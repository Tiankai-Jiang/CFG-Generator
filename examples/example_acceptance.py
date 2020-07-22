def comprehensive_showcase(v1, v2):
    if (v1 == 'for else'):
        if (v2 == "for else"):
            digits = [0, 1, 5]
            for i in digits:
                print(i)
            else:
                print("No items left.")
        elif (v2 == "while else"):
            counter = 0
            while counter < 3:
                counter = counter + 1
                a = 5
            else:
                a = 10
            c += 1
    elif (v1 == 'lambda'):
        if (v2 == "lamb1"):
            a = lambda x: 2 * x + 5  # cannot handle if else
        elif (v2 == "lamb2"):
            a = (lambda x, y: x + y)(1, 2)
    elif (v1 == 'try catch'):
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
    elif (v1 == 'comprehension'):
        if (v2 == "list"):
            a = [2 * x for x in y if x > 0 for y in z if len(y) < 3]
        elif (v2 == "set"):
            a = {6-x for x in y if x > 5 for y in [1,2,3,4] if y==3}
        elif (v2 == "dict"):
            a = {3 * k : 2*v for (k,v) in b.items() if k > 0 if v > 0}
    return "Finish"
