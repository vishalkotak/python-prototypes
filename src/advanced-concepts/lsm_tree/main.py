import os

class LSMTree:

    def __init__(self, threshold):
        self.mapping = {}
        self.threshold = threshold
        self.current_dir = os.getcwd()
        self.file_path = f"{self.current_dir}/data.txt"
        self.flush_index = 0
        self.flush_metadata = []
        self.flush_merged_index = 0
        self.flush_merged_metadata = []
        if not os.path.exists(self.file_path):
            with open(self.file_path, "a") as file:
                pass
            print(f"File created {self.file_path}")
        else:
            with open(self.file_path, "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    self.mapping[int(key)] = value
            print(f"File exists: {self.file_path}")
        self.file_reference = open(self.file_path, "a")

    def insert(self, key, value):
        if len(self.mapping) >= self.threshold:
            self.flush_to_disk(self.mapping)
            self.mapping.clear()
        self.mapping[key] = value
        self.file_reference.write(f"{key}={value}\n")

    def flush_to_disk(self, temp_dict):
        sorted_by_keys = dict(sorted(temp_dict.items()))
        with open(f"{self.current_dir}/sstable-{self.flush_index}.txt", "w") as file:
            for key, value in sorted_by_keys.items():
                file.write(f"{key}={value}\n")
            self.flush_metadata.append((self.flush_index,
                                        f"sstable-{self.flush_index}.txt",
                                        min(sorted_by_keys.keys()),
                                        max(sorted_by_keys.keys())))
            self.flush_index += 1
        if self.flush_index >= 3 * self.threshold:
            self.compact()

    def compact(self):
        merged_sstable_dict = {}
        for item in self.flush_metadata:
            sst_table_file_path = item[1]
            with open(sst_table_file_path, "r") as file:
                for line in file:
                    k, v = line.split("=")
                    merged_sstable_dict[int(k)] = v
            os.remove(sst_table_file_path)
        self.flush_metadata = []
        self.flush_index = 0
        sorted_by_keys = dict(sorted(merged_sstable_dict.items()))
        with open(f"{self.current_dir}/sstable-merged-{self.flush_merged_index}.txt", "w") as file:
            for key, value in sorted_by_keys.items():
                file.write(f"{key}={value}")
            self.flush_merged_metadata.append((self.flush_merged_index,
                                        f"sstable-merged-{self.flush_merged_index}.txt",
                                        min(sorted_by_keys.keys()),
                                        max(sorted_by_keys.keys())))
            self.flush_merged_index += 1
            

    def lookup(self, key):
        if key in self.mapping:
            return self.mapping[key]
        for i in range(len(self.flush_metadata) - 1, -1, -1):
            index, _, min_key, max_key = self.flush_metadata[i]
            if key >= min_key and key <= max_key:
                with open(f"sstable-{index}.txt", "r") as file:
                    for line in file:
                        k, v = line.split("=")
                        if int(k) == key:
                            return v
        for i in range(len(self.flush_merged_metadata) - 1, -1, -1):
            index, _, min_key, max_key = self.flush_merged_metadata[i]
            if key >= min_key and key <= max_key:
                with open(f"sstable-merged-{index}.txt", "r") as file:
                    for line in file:
                        if line:
                            k, v = line.strip().split("=")
                            if int(k) == key:
                                return v
        return None
    


if __name__ == "__main__":
    lsmtree = LSMTree(3)
    lsmtree.insert(1, "a")
    lsmtree.insert(2, "b")
    lsmtree.insert(3, "c")
    lsmtree.insert(4, "d")
    lsmtree.insert(5, "e")
    lsmtree.insert(6, "f")
    lsmtree.insert(7, "g")
    lsmtree.insert(8, "h")
    lsmtree.insert(9, "i")
    print(f"Value for key 1: {lsmtree.lookup(1)}")
    print(f"Value for key 10: {lsmtree.lookup(10)}")
    lsmtree.insert(1, "aa")
    lsmtree.insert(2, "bb")
    lsmtree.insert(3, "cc")
    lsmtree.insert(4, "dd")
    lsmtree.insert(5, "ee")
    lsmtree.insert(6, "ff")
    lsmtree.insert(7, "gg")
    lsmtree.insert(8, "hh")
    lsmtree.insert(9, "ii")
    print(f"Value for key 1: {lsmtree.lookup(1)}")
    print(f"Value for key 2: {lsmtree.lookup(2)}")
    
    