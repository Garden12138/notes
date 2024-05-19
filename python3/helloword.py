#!/usr/bin/python3

print("hello, world!")

# 基本数据类型
# 变量无需声明类型，但使用前必须赋值，变量类型由赋值的对象决定。
print("-- 基本数据类型 --")
# 单个变量赋值
print("-- 单个变量赋值 --")
name = "garden"
print(name)
# 多个变量赋值
print("-- 多个变量赋值 --")
a = b = c = 10
print(a, b, c)
student_name, student_age, student_gender, student_score = "garden", 18, "male", 90.5
print(student_name, student_age, student_gender, student_score)
# Number（不可变）：int、float、bool、complex
print("-- Number --")
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
# String（不可变）：
print("-- String --")
  # 用单引号或双引号括起来，支持使用\转义字符（字符串前使用r表示不转义）。
  # 字符串支持索引，索引值以0为开始值，-1为末尾的开始值。
  # 字符串支持切片，语法为[start:end:step]，start为开始索引，end为结束索引，step为步长。
  # 字符串支持 * 运算符，表示复制字符串。
  # 字符串支持 + 运算符，表示拼接字符串。
  # 没有单独的字符类型，一个字符即为长度为1的字符串。
var_str = "garden"
print(var_str) # 完整字符串
print(var_str[0]) # 截取字符串第一个字符
print(var_str[-1]) # 截取字符串最后一个字符
print(var_str[1:-1]) # 截取字符串第二个到最后第二个字符
print(var_str[1:]) # 截取字符串第二个到最后一个字符
print(var_str[1:3]) # 截取字符串第二个到第三个字符
print(var_str * 3) # 复制字符串三次
print(var_str + " hello\n") # 字符串拼接包含转义符字符串
print(var_str + r" hello\n") # 字符串拼包含转义符但不转义字符串
# List（可变）
print("-- List --")
  # 列表写在括号之间，元素可以为不同类型，元素之间用逗号隔开。
  # 列表支持索引，索引值以0为开始值，-1为末尾的开始值。
  # 列表支持切片，语法为[start:end:step]，start为开始索引，end为结束索引，step为步长（步长为负数表示逆序）。
  # 列表支持 * 运算符，表示复制字符串。
  # 列表支持 + 运算符，表示拼接字符串。
  # 列表中的元素可修改。
var_list = [1, 2, 3.0, "4", True]
print(var_list) # 完整列表
print(var_list[0]) # 截取列表第一个元素
print(var_list[-1]) # 截取列表最后一个元素
print(var_list[1:-1]) # 截取列表第二个到最后第二个元素
print(var_list[1:]) # 截取列表第二个到最后一个元素
print(var_list[1:3]) # 截取列表第二个到第三个元素
print(var_list * 3) # 复制列表三次
print(var_list + [6, 7, 8]) # 列表拼接
var_list[0] = 100 # 修改列表第一个元素
print(var_list)
print(var_list[1:4:2]) # 步长为2列表
print(var_list[-1::-1]) # 逆序列表
# Tuple（不可变）

# Set（可变）

# Dictionary（可变）

# bytes

