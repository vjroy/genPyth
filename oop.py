class Dog:
    def __init__(self, name):
        self.name = name
    
    def bark(self):
        return f"{self.name} says woof"

class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        self.count += 1 

#d = Dog("Spot")
#print(d.bark())

c = Counter()
c.increment()
print(c.count)