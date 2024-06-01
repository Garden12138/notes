#!/usr/bin/python3

num = 10 # global variable

def func1(a1, a2):
    num = 20 # local variable
    print("Inside func1, num =", num)

print("Before calling func1, num =", num)
func1(1, 2)
print("After calling func1, num =", num)

def func2():
    global num
    num = 30 # global variable
    print("Inside func2, num =", num)

print("Before calling func2, num =", num)
func2()
print("After calling func2, num =", num)

def func3():
    num = 40 # local variable
    print("Inside func3, num =", num)
    def func4():
        num = 50 # local variable
        print("Inside func4, num =", num)
    func4()
    print("After calling func4, num =", num)

print("Before calling func3, num =", num)
func3()
print("After calling func3, num =", num)

def func5():
    num = 60 # local variable
    print("Inside func5, num =", num)
    def func6():
        nonlocal num
        num = 70 # nonlocal variable
        print("Inside func6, num =", num)
    func6()
    print("After calling func6, num =", num)

print("Before calling func5, num =", num)
func5()
print("After calling func5, num =", num)
