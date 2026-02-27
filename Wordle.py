# valid_letters = ["W", "Y", "I", "P", "D", "F", "G", "H", "J", "K", "V"]
# #valid_letters = ["Q", "W", "Y", "I", "P", "D", "F", "G", "H", "J", "K", "Z", "X", "V"]
# s = "DI"
# counter = 0
# for i in range(len(valid_letters)):
#     for j in range(len(valid_letters)):
#         for k in range(len(valid_letters)):
#             s += valid_letters[i]
#             s += valid_letters[j]
#             s += valid_letters[k]
#             print(f"{counter}: {s}")
#             s = "DI"
#             counter += 1

valid_letters = ["Q", "W", "Y", "I", "P", "F", "G", "H", "J", "K", "V", "X", "Z"]
s = "DI"
counter = 0
for i in range(len(valid_letters)):
    for j in range(len(valid_letters)):
        s += valid_letters[i]
        s += valid_letters[j]
        s += "Y"
        print(f"{counter}: {s}")
        counter += 1
        s = "DI"


