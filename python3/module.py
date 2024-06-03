#!/usr/bin/python3

import sys
print("命令行参数如下：")
for i in sys.argv:
    print(i)
print("\n\nPython 路径为：", sys.path, "\n")

print("导入同一目录下的模块：")
import same_dir_repo
print(same_dir_repo.sum(1, 5))
stu = same_dir_repo.Student("丁真", 15)
stu.say_hello()

print("导入同一目录下的模块的指定别名：")
from same_dir_repo import sum
print(sum(1, 5))
from same_dir_repo import Student
stu = Student("丁真", 15)
stu.say_hello()

print("导入同一目录下的模块的所有内容：")
from same_dir_repo import *
print(sum(1, 5))
stu = Student("丁真", 15)
stu.say_hello()

print("查看模块内容：")
print(dir(same_dir_repo)) # 查看指定模块内容
print(dir()) # 查看当前模块内容

# print("导入其他目录下的指定模块：")
# import dependency.diff_dir_repo1
# print(dependency.diff_dir_repo1.sqrt(49))

# print("导入其他目录下的指定模块的指定别名：")
# from dependency import diff_dir_repo2
# print(diff_dir_repo2.square(7))
# from dependency.diff_dir_repo2 import square
# print(square(7))

print("导入其他目录下的模块的所有内容：")
from dependency import *
print(diff_dir_repo1.sqrt(49))
print(diff_dir_repo2.square(7))