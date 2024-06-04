#!/usr/bin/python3

import math

print("--------input--------")
name = input("Please enter your name: ")
age = input("Please enter your age: ")
print("Your name is " + name + ", and your age is " + age + ".")


print("--------output--------")
print("--------str and repr--------")
s = "hello"
print(str(s)) # 返回用户易读的字符串表示
print(repr(s)) # 返回解释器易读的字符串表示

print("--------str.format()--------")
print("My name is {}, and I'm {} years old.".format(name, age))
print("My name is {1}, and I'm {0} years old.".format(age, name))
print("My name is {n}, and I'm {a} years old.".format(n=name, a=age))
print("this is !a usage: {!a}".format("A")) # 格式化字符串，用!a表示使用ascii()函数进行格式化
print("this is !s usage: {!s}".format("hello")) # 格式化字符串，用!s表示使用str()函数进行格式化
print("this is !r usage: {!r}".format("hello")) # 格式化字符串，用!r表示使用repr()函数进行格式化
print("PI的近似值: {:.2f}".format(math.pi)) # 格式化字符串，用.2f表示保留两位小数
param = {"name": name, "age": age}
print("My name is {0[name]}, and I'm {0[age]} years old.".format(param)) # 使用字典参数
print("My name is {name}, and I'm {age} years old.".format(**param)) # 使用**字典参数

print("--------f-string--------")
print(f"My name is {name}, and I'm {age} years old.")

print("--------%s--------")
print("My name is %s, and I'm %d years old." % (name, int(age)))