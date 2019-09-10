class ProofListKey:
    def __init__(self, height, index):
        self.height = height
        self.index = index

    @staticmethod
    def leaf(index):
        return ProofListKey(0, index)

    def left(self):
        return ProofListKey(self.height - 1, self.index << 1)

    def right(self):
        return ProofListKey(self.height - 1, (self.index << 1) + 1)
