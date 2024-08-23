from typing import List, Generator

# Without generators
def first_n(n : int) -> List[int]:
    num, nums = 0, []
    while num < n:
        nums.append(num)
        num += 1
    return nums

sum_of_first_n = sum(first_n(100000))
print(f"Sum of first n numbers using return statement: {sum_of_first_n}")

# With generator pattern using class
class FirstNGeneratorPattern():

    def __init__(self, n: int):
        self.n = n
        self.num = 0

    def __iter__(self):
        return self

    def __next__(self) -> int:
        return self.next()

    def next(self) -> int:
        if self.num < self.n:
            current, self.num = self.num, self.num + 1
            return current
        raise StopIteration()
    
sum_first_n_generator_pattern = sum(FirstNGeneratorPattern(100000))
print(f"Sum of first n numbers using generator pattern through class: {sum_first_n_generator_pattern}")

# With generator functions
def first_n_generator(n: int) -> Generator[int, None, None]:
    num = 0
    while num < n:
        yield num
        num += 1

sum_first_n_generators = sum(first_n_generator(100000))
print(f"Sum of first n numbers using generator functions: {sum_first_n_generators}")
