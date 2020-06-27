# b = {print(x) for x in y if x > 5 for y in [1,2,3,4] if y==3}
# a = [2*x for x in y if x > 0 ]
# c += 1
# for x in y:
#     v += 1
# a = [(m, n) for n in range(2) for m in range(3, 5)]
# b = {s for s in [1, 2, 3] if s % 2} # trigger binary op!

# celsius = {3*k:2*print(v) for (k,v) in fahrenheit.items()}

a = (print(x) for x in y if x > 4 for y in [1,2,3,4])