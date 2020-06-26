def test(temp) -> int:
    if temp > 1:
        pass
    else:
        pass


    try:
        return int(temp)
    except ValueError:
        print("Oops!  can not convert temp to int.  Try again...")
    except ZeroDivisionError:
        print("something happened")
    except:
        print("else")

