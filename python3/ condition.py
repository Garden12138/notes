#!/usr/bin/python3

# if-else statement
a, b = 10, 20
if a > b:
    print("a is greater than b")
elif a < b: 
    print("a is less than b")
else:
    print("a is equal to b")

# match case statement
status = 201
match status:
    case 200 | 201:
        print("OK")
    case 404:
        print("Not Found")
    case 500:
        print("Internal Server Error")
    case _:
        print("Unknown Error")