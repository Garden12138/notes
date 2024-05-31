#!/usr/bin/python3

# iter
print("--------- iter-base --------")
list = [1, 2, 3, 4, 5]
it = iter(list)
print(next(it))
print(next(it))

print("--------- iter-for --------")
for x in it:
    print(x)
    if x == 4:
        break

print("--------- iter-while --------")
while True:
    try:
        print(next(it))
    except StopIteration:
        break
print("--------- iter-cus --------")
class cusIter:
    num = 0
    def __init__(self, num):
        self.num = num
    def __iter__(self):
        return self
    def __next__(self):
        x = self.num
        self.num += 2
        return x
myIter = iter(cusIter(10))
print(next(myIter))
print(next(myIter))
print(next(myIter))

# gener
print("--------- gener-base --------")
def countDown(n):
    while n > 0:
        yield n
        n -= 1
gener = countDown(10)
print(next(gener))
print(next(gener))
for x in gener:
    print(x)

# dec
print("--------- dec with param func --------")
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # dec logic
            for i in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator
@repeat(3)
def greet(name):
    print("Hello, " + name)
greet("Garden")

print("--------- dec with class --------")
class Repeat:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        # dec logic
        result = self.func(*args, **kwargs)
        return result

@Repeat
def Greet(name):
    print("Hello, " + name)
Greet("Deamon")