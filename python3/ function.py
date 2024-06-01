#!/usr/bin/python3

print("----------function----------")
def area(width, height):
    return width * height
print(area(5, 10))

print("----------function with unchanged parameter----------")
def unchanged_parameter(a):
    a = 10
    print(id(a), a)
a = 1
unchanged_parameter(a)
print(id(a), a)

print("----------function with changed parameter----------")
def changed_parameter(b):
    b[0] = 10
    print(id(b), b)
b = [1, 2, 3]
changed_parameter(b)
print(id(b), b)

print("----------function with keyword parameter----------")
def key_parameter(c, d):
    print(c, d)
key_parameter(d=10, c=20)

print("----------function with default parameter----------")
def default_parameter(e, f=10):
    print(e, f)
default_parameter(20)

print("----------function with variable parameter(tuple)----------")
def variable_parameter(*args):
    print(args)
variable_parameter(1, 2, 3)

print("----------function with variable parameter(dict)----------")
def variable_key_parameter(**kwargs):
    print(kwargs)
variable_key_parameter(a=1, b=2, c=3)

print("----------function with lambda expression----------")
sum = lambda x, y: x + y
print(sum(10, 20))

print ("----------function with forced location parameter----------")
def forced_location_parameter(a, b, /, c, d, *, e, f):
    print(a, b, c, d, e, f)
forced_location_parameter(1, 2, 3, 4, e=5, f=6)