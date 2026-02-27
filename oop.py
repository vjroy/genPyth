class Dog:
    def __init__(self, name):
        self.name = name
    
    def bark(self):
        return f"{self.name} says woof"

d = Dog("Spot")

print(d.bark())
