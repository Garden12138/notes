#!/usr/bin/python3

print("--------only_read--------")
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_read.txt", "r") as f:
    print(f.read(4))
    print(f.read())

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_read.txt", "r") as f:
    print(f.readline(4))
    print(f.readline())

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_read.txt", "r") as f:
    print(f.readlines(32))
    print(f.readlines())


print("--------only_write--------")
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_write.txt", "w") as f:
    f.write("Hello, world1\n")
    f.writelines(["Hello, world2\n", "Hello, world3"])

print("--------only_append--------")
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_append.txt", "a") as f:
    f.write("Hello, world4\n")

print("--------read_write--------")
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/read_write_r+.txt", "r+") as f:
    f.write("H")
    print(f.read())

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/read_write_w+.txt", "w+") as f:
    f.write("Hello, world\n")
    print(f.read()) # empty

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/read_write_a+.txt", "a+") as f:
    f.write("Hello, world\n")
    print(f.read()) # empty

print("--------others--------")
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/others.txt", "rb+") as f:
    f.write(b'0123456789abcdef')
    print(f.tell())
    f.seek(1, 0)
    print(f.tell(), f.read(1))
    f.seek(1, 1)
    print(f.tell(), f.read(1))
    f.seek(-8, 2)
    print(f.tell(), f.read(1))
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/only_write.txt", "r+") as f:
    f.truncate(3)
    print(f.readlines())
with open("/Users/cengjiada/Documents/study/learn-note/python3/file/others.txt", "r+") as f:
    fid = f.fileno()
    print(fid)
    satty = f.isatty()
    print(satty)