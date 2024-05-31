#!/usr/bin/python3

# list derivation：[表达式 for 变量 in 列表 if 条件]
list_deri = [x**2 for x in range(1, 10) if x % 2 == 0]
print(list_deri)
# tuple derivation：(表达式 for 变量 in 列表 if 条件)
tuple_deri = (x**2 for x in range(1, 10) if x % 2 == 0)
print(tuple(tuple_deri))
# set derivation：{表达式 for 变量 in 列表 if 条件}
set_deri = {x**2 for x in range(1, 10) if x % 2 == 0}
print(set_deri)
# dict derivation：{键表达式:值表达式 for 变量 in 列表 if 条件}
dict_deri = {x:x**2 for x in range(1, 10) if x % 2 == 0}
print(dict_deri)