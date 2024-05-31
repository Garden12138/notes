#!/usr/bin/python3

# while statement
i = 0
while i < 10:
    print(i)
    i += 1
else:  # executed if the loop completes without encountering a break statement
    print(f"The while loop is over, i = {i}")

i = 0
while i < 10:
    if i == 5:
        i += 1
        continue  # skip the rest of the loop and go back to the top
    elif i == 8:
        break  # exit the loop
    else:
        print(i)
        i += 1
else:  # executed if the loop completes without encountering a break statement
    print(f"The while loop is over, i = {i}")

# for statement
list = ["a", "b", "c", "d", "e"]
for item in list:
    print(item)
else:  # executed if the loop completes without encountering a break statement
    print("The for loop is over")

for i in range(len(list)):
    print(i, list[i])
else:  # executed if the loop completes without encountering a break statement
    print("The for loop is over")