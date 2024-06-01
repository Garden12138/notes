#!/usr/bin/python3

import time

class Person:
    __weight = 50 # class variable
    def __init__(self, name, age): # constructor
        self.name = name # instance variable
        self.age = age
        self.__height = 170 # private instance variable
    def speak(self): # instance method
        t = time.localtime() 
        current_time = time.strftime("%H:%M:%S", t) # local variable
        print("%s: My name is %s and I am %d years old." % (current_time, self.name, self.age))

class Student(Person): # inheritance
    def __init__(self, name, age, grade):
        super().__init__(name, age) # call parent constructor
        self.grade = grade
    def speak(self): # override parent method
        super().speak() # call parent method
        print(" I am in grade %d." % (self.grade))

class Speaker:
    def __init__(self, name, language):
        self.name = name
        self.language = language
    def speak(self):
        print("%s speaks %s." % (self.name, self.language))

class StudentSpeaker(Speaker, Student): # multiple inheritance
    def __init__(self, name, language, age, grade):
        Speaker.__init__(self, name, language) # call parent constructor
        Student.__init__(self, name, age, grade) # call parent constructor
    def __str__(self, msg) -> str:  # overload __str__ method
        return super().__str__() + msg

s = Student("Garden", 26, 12)
s.speak()

ss = StudentSpeaker("Garden", "English", 18, 12)
ss.speak()
print(ss.__str__("重载😁"))