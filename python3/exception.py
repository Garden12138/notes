#!/usr/bin/python3

print("-------- exception-base --------")
try:
    a = 10 / 0
    print(a)
except ZeroDivisionError:
    print("division by zero!")
except:
    print("unknown error!")
    raise
else:
    print("no error")
finally:
    print("clean up")

print("-------- exception-cus --------")
class CustError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "Custom error: " + str(self.value)

try:
    raise CustError("this is a custom error message")
except CustError as e:
    print(e)