from bitarray import bitarray
import mmh3

class BloomFilter:

    def __init__(self, array_size, hash_function_count):
        self.array_size = array_size
        self.hash_function_count = hash_function_count
        self.bit_array = bitarray(self.array_size)
        self.bit_array.setall(0)

    def add(self, item):

        for i in range(self.hash_function_count):
            index = mmh3.hash(item, i) % self.array_size
            self.bit_array[index] = 1

    def check(self, item):
        for i in range(self.hash_function_count):
            index = mmh3.hash(item, i) % self.array_size
            if self.bit_array[index] == 0:
                return False
        return True
    

if __name__ == "__main__":
    bloom_filter = BloomFilter(1000, 10)
    bloom_filter.add("Jack")
    bloom_filter.add("Jill")
    bloom_filter.add("David")
    print(f"Is Jack present {bloom_filter.check("Jack")}")
    print(f"Is Sam present {bloom_filter.check('Sam')}")
    

    
