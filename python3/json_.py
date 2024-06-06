#!/usr/bin/python3

import json

stu = {"name": "Alice", "age": 20, "gender": "female"}
print("Original data:", repr(stu))
stu_json = json.dumps(stu) # python object to JSON string
print("JSON data: ", stu_json)

stu_new = json.loads(stu_json) # JSON string to python object
print("New data:", stu_new)

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/stu.json", "w") as f:
    stu["name"] = "Garden"
    stu["gender"] = "male"
    json.dump(stu, f) # python object to JSON file

with open("/Users/cengjiada/Documents/study/learn-note/python3/file/stu.json", "r") as f:
    stu_json = json.load(f) # JSON file to python object
    print("JSON data from file: ", stu_json)