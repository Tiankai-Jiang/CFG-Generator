digits = [0, 1, 5]

for i in digits:
    a += i
    if i == 5:
        print("5 in list")
        break
else:
    print("out of the loop")

a += 1
b += 2