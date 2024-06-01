#!/usr/bin/python3

from functools import reduce

print("--------lambda with map function--------")
sqrt = lambda x: x ** 0.5
print(list(map(sqrt, [4, 16, 49, 64, 81])))

print("--------lambda with filter function--------")
is_even = lambda x: x % 2 == 0
print(list(filter(is_even, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])))

print("--------lambda with reduce function--------")
incr = lambda x, y: x + y
print(reduce(incr, [1, 2, 3, 4, 5]))