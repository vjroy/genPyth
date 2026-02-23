class Fruit:
    def __init__(self, name: str) -> None:
        self.name = name

    def __mul__(self, other: int) -> str:
        return self.name * other
    
    def __len__(self) -> int:
        return len(self.name)
    
    def __str__(self) -> str:
        return self.name

banana: Fruit = Fruit("Banana") 
print(banana * 4) #Equivalent to print(banana.__mul__(4))
print(len(banana))
print(banana)