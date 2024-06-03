#!/usr/bin/python3

print("This is the same_dir_repo.py file.")

def sum(x, y):
    return x + y

class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def say_hello(self):
        print("Hello, my name is " + self.name + " and I am " + str(self.age) + " years old. 芝士雪豹QAQ")

if __name__ == "__main__": # only run when this file is called directly
    print("repo run")
else:
    print("import run")