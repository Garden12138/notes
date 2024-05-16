#!/usr/bin/python3

print("hello, world!")

# 基本数据类型
# 变量无需声明类型，但使用前必须赋值，变量类型由赋值的对象决定。
# 单个变量赋值
name = "garden"
print(name)
# 多个变量赋值
a = b = c = 10
print(a, b, c)
student_name, student_age, student_gender, student_score = "garden", 18, "male", 90.5
print(student_name, student_age, student_gender, student_score)
# Number（不可变）：int、float、bool、complex
var_int, var_float, var_bool, var_complex = 10, 3.14, True, 3+4j
print(type(var_bool) == int)
print(isinstance(var_bool, int))
print(issubclass(bool, int))
print(var_bool == 1, var_bool + 1)
print(5 + 4) # 加法
print(5 - 4) # 减法
print(5 * 4) # 乘法
print(5 / 4) # 除法
print(5 // 4) # 整除
print(5 % 4) # 取余
print(5 ** 4) # 乘方
print(5 ^ 4) # 按位异或，二进制位上不同时为1则为1，否则为0
print(5 | 4) # 按位或，二进制位上为1则为1，否则为0
print(5 & 4) # 按位与，二进制位上都为1则为1，否则为0
print(5 >> 1) # 右移，二进制位向右移动一位，符号位不变
print(5 << 1) # 左移，二进制位向左移动一位，符号位不变
# String（不可变）

# List（可变）

# Tuple（不可变）

# Set（可变）

# Dictionary（可变）

# bytes

