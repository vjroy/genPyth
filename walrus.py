user_input: str = "Hello World!"

if (text := len(user_input)) > 5:
    print(text, ":)")
else:
    print(text, ":(")

def get_value():
    return None

if var := get_value():
    print(var)
else:
    print('None')

if (text := len("Hi")) > 5:
    print(f"Length is {text}")
else:
    print(f"Length is less than 5 :(")