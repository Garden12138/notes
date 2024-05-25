#!/usr/bin/python3

import math
import random

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
print(abs(-5)) # 取绝对值
print(math.fabs(-5)) # 取绝对值，返回浮点型
print(math.ceil(3.14)) # 向上取整
print(math.floor(3.94)) # 向下取整
print(round(3.1415926, 2)) # 小数点四舍五入
print(math.log(100, 10)) # 计算以10为基数的100的对数
print(math.log10(100)) # 计算以10为基数的100的对数
print(max(1, 2, 3, 4, 5)) # 取最大值
print(min(1, 2, 3, 4, 5)) # 取最小值
print(math.pow(2, 3)) # 计算2的3次方
print(math.exp(2)) # 计算自然常数e的2次方
print(math.sqrt(16)) # 计算16的平方根
print(math.modf(3.14)) # 取整数部分和小数部分
print(random.random()) # 随机生成0-1之间的浮点数
print(random.uniform(1, 100)) # 随机生成1-100之间的浮点数
print(random.choice([1, 2, 3, 4, 5])) # 从列表中随机选择一个元素
print(random.randrange(1, 100, 2)) # 随机生成1-100间的奇数
print(random.shuffle([1, 2, 3, 4, 5])) # 随机打乱列表
print(random.seed(100)) # 设置随机数种子
print(math.sin(math.pi/2)) # 计算正弦值
print(math.cos(math.pi/2)) # 计算余弦值
print(math.tan(math.pi/4)) # 计算正切值
print(math.asin(1)) # 计算反正弦值
print(math.acos(1)) # 计算反余弦值      
print(math.atan(1)) # 计算反正切值
print(math.atan2(1, 1)) # 计算坐标x，y的反正切值
print(math.degrees(math.pi/2)) # 角度转换为弧度
print(math.radians(180)) # 弧度转换为角度
print(math.hypot(3, 4)) # 计算斜边长度
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
print("Hello\nWorld") # 换行符
print("Hello\rWorld~") # 回车符
print("My name is %s, %d years old. My favorite letter is %c." % ("garden", 18, "g")) # 格式化字符串
var_fname = "garden"
var_fage = 18
var_fletter = "g"
print(f"My name is {var_fname}, {var_fage} years old. My favorite letter is {var_fletter}.") # f-string格式化字符串
var_sentence = "my favorite letter is G"
print(var_sentence.capitalize()) # 首字母大写，其他字母小写
print(var_sentence.upper()) # 全部大写
print(var_sentence.lower()) # 全部小写
print(var_sentence.swapcase()) # 大小写互换
print(var_sentence.title()) # 每个单词的首字母大写，其他字母小写
print(var_sentence.center(40, "*")) # 字符串居中，包含字符串总宽度为40，填充字符为*
print(var_sentence.ljust(40, "*")) # 字符串左对齐，包含字符串总宽度为40，填充字符为*
print(var_sentence.rjust(40, "*")) # 字符串右对齐，包含字符串总宽度为40，填充字符为*
print(var_sentence.zfill(40)) # 字符串右边对齐，包含字符串总宽度为40，填充字符为0
print(len(var_sentence)) # 字符串长度
print(var_sentence.count("G", 22, 23)) # 统计字符串中指定范围内[22, 23)出现的字符G的次数
print(max(var_sentence)) # 字符串中最大字符
print(min(var_sentence)) # 字符串中最小字符
print(var_sentence.isalnum()) # 字符串是否全为字母或数字
print(var_sentence.isalpha()) # 字符串是否全为字母或中文
print("½:","½".isdigit()) # 字符串是否全为数字
print(var_sentence.islower()) # 字符串是否全为小写字母
print(var_sentence.isupper()) # 字符串是否全为大写字母
print(var_sentence.istitle()) # 字符串是否每个单词的首字母大写，其他字母小写
print("½:","½".isnumeric()) # 字符串是否全为数字（Unicode 数字，全角数字（双字节），罗马数字，汉字数字）
print(var_sentence.isspace()) # 字符串是否全为空白字符（包括空格、制表符、换行符等）
print(var_sentence.isdecimal()) # 字符串是否全为十进制数字
print(var_sentence.startswith("my", 0, 23)) # 字符串是否以指定字符串开头，[0, 23)指定范围
print(var_sentence.endswith("letter", 0, 23)) # 字符串是否以指定字符串结尾，[0, 23)指定范围
print(var_sentence.find("G", 0, 23)) # 字符串中第一个出现的字符G的索引，找不到返回-1，[0, 23)指定范围
print(var_sentence.index("G", 0, 23)) # 字符串中第一个出现的字符G的索引，找不到报错，[0, 23)指定范围
print(var_sentence.rfind("G", 0, 23)) # 字符串中最后一个出现的字符G的索引，找不到返回-1，[0, 23)指定范围
print(var_sentence.rindex("G", 0, 23)) # 字符串中最后一个出现的字符G的索引，找不到报错，[0, 23)指定范围
print(var_sentence.split(" ", 2)) # 字符串按照指定字符分割，分割次数为2，返回长度为3的列表
print("ab c\n\nde fg\rkl\r\n".splitlines(True)) # 字符串按照换行符（包括\r、\n、\r\n）分割，参数为True时保留换行符，返回列表
print(var_sentence.lstrip("my")) # 去除字符串左边空白字符或指定字符
print(var_sentence.rstrip("G")) # 去除字符串右边空白字符或指定字符
print(var_sentence.strip("my G")) # 去除字符串两边空白字符或指定字符
print(var_sentence.replace("G", "g", 1)) # 字符串替换指定字符, 最多替换一次
print("my\tfavorite\tletter \ts\tG".expandtabs(4)) # 字符串替换制表符为指定宽度（包含前置字符串长度）的空格
var_sentence_trans = var_sentence.maketrans("aeiou", "12345") # 创建字符映射表
print(var_sentence.translate(var_sentence_trans)) # 使用字符映射表转换字符串
print(var_sentence.join(("Hi! ", "!"))) # 指定序列由字符串连接成新的字符串
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
print("-- Tuple --")
  # 与列表类似，但元素写在小括号()之间且元素不能修改。
  # 构造 tuple 时，如果元素只有一个，则需要在元素后面添加逗号。
var_tuple = (1, 2, 3.0, "4", True)
print(var_tuple) # 完整元组
print(var_tuple[0]) # 截取元组第一个元素
print(var_tuple[-1]) # 截取元组最后一个元素
print(var_tuple[1:-1]) # 截取元组第二个到最后第二个元素
print(var_tuple[1:]) # 截取元组第二个到最后一个元素
print(var_tuple[1:3]) # 截取元组第二个到第三个元素
print(var_tuple * 3) # 复制元组三次
print(var_tuple + (6, 7, 8)) # 元组拼接
print(var_tuple[1:4:2]) # 步长为2元组
print(var_tuple[-1::-1]) # 逆序元组
print((20,)) # 只有一个元素的元组需要在元素后面添加逗号
# Set（可变）
print("-- Set --")
  # 用于存储无序不重复元素。
  # 元素写在花括号{}之间或使用set()函数构造，创建空集合必须使用set()函数。
  # 支持交集、并集、差集、对称差运算。
var_set1 = {"Google", "Taobao"}
var_set2 = set(["Facebook", "Baidu", "Google"])
print(var_set1)
print(var_set2)
print(var_set1 & var_set2) # 交集
print(var_set1 | var_set2) # 并集
print(var_set1 - var_set2) # 差集
print(var_set1 ^ var_set2) # 对称差
# Dictionary（可变）
print("-- Dictionary --")
  # 用于存储键值对，键必须是不可变类型，值可以是任意类型。
  # 字典写在花括号{}之间，键值对之间用冒号:隔开，键值对之间用逗号隔开或使用dict()函数构造。
  # 字典支持索引，索引值以键为开始值。
var_dict1 = {"name": "garden", "age": 18, "gender": "male", "score": 90.5}
var_dict2 = dict(name="garden", age=18, gender="male", score=90.5)
var_dict3 = dict([("name", "garden"), ("age", 18), ("gender", "male"), ("score", 90.5)])
print(var_dict1)
print(var_dict2)
print(var_dict3)
print(var_dict1.update({"name": "garden1"})) # 更新字典
print(var_dict1["name"]) # 索引字典
# bytes
print("-- bytes --")
  # 用于存储二进制数据。
  # 写在前缀b或B后面，后面跟着字符串表示的字节数据或使用bytes()函数构造。
  # bytes支持索引、切片、拼接、查找以及替换等操作。
var_bytes1 = b"hello, world!"
var_bytes2 = bytes("hello, world!", "utf-8")
print(var_bytes1)
print(var_bytes2)
print(var_bytes1[0]) # 索引字节(ascii码)
print(var_bytes1[1:5]) # 切片字节
print(var_bytes1 + var_bytes2) # 拼接字节
print(var_bytes1.find(b"l")) # 查找字节
print(var_bytes1.replace(b"l", b"L")) # 替换字节

# 数据类型转换
# 隐式转换，自动完成，由低数据类型自动转换到高数据类型
print("-- 隐式转换 --")
var_convert1 = 10
var_convert2 = 3.14
var_convert3 = var_convert1 + var_convert2
print(var_convert1, type(var_convert1))
print(var_convert2, type(var_convert2))
print(var_convert3, type(var_convert3))
# 显式转换
print("-- 显式转换 --")
print(int("123")) # 字符串转整数
print(float("3.14")) # 字符串转浮点数
print(complex("1+2j")) # 字符串转复数
print(str(123)) # 整数转字符串
print(repr(123)) # 整数转字符串，带有单引号
print(eval("1+2")) # 字符串转表达式并求值
print(tuple(["1", "2"])) # 列表转元组
print(list(("1", "2"))) # 元组转列表
print(set(["1", "2"])) # 列表转集合
print(dict([("name", "garden"), ("age", 18), ("gender", "male"), ("score", 90.5)])) # 列表转字典
print(frozenset(["1", "2"])) # 列表转不可变集合
print(chr(97)) # 整数转字符
print(ord("a")) # 字符转整数
print(hex(10)) # 整数转十六进制字符串
print(oct(10)) # 整数转八进制字符串

# 运算符
# 算术运算符：+、-、*、/、//、%、**
print("-- 算术运算符 --")
print(20 / 3)
print(20 // 3)
print(2 ** 3)
# 位运算符：&、|、^、~、<<、>>
print("-- 位运算符 --")
# 赋值运算符：=、+=、-=、*=、/=、//=、%=、**=、&=、|=、^=、<<=、>>=
print("-- 赋值运算符 --")
# print((var_hx := 10) > 1) 海象运算符，Python 3.8 新特性
# 关系运算符：==、!=、>、<、>=、<=
print("-- 关系运算符 --")
# 逻辑运算符：and、or、not
print("-- 逻辑运算符 --")
# 成员运算符：in、not in
print("-- 成员运算符 --")
print("g" in "hello, world!")
print("g" not in "hello, world!")
# 身份运算符：is、is not
print("-- 身份运算符 --")
print(var_convert1 is var_convert2)
print(var_convert1 is not var_convert2)
# 运算符优先级：**、~、*、/、//、%、+、-、<<、>>、&、^、|、<、<=、>、>=、==、!=、is、is not、in、not in、not、and、or
print("-- 运算符优先级 --")

