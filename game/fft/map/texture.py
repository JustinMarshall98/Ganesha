class Texture(object):
    def __init__(self):
        self.file_path = None
        self.file = None
        self.data = None

    def read(self, files):
        for file_path in files:
            self.file_path = file_path
            self.file = open(self.file_path, "rb")
            self.data = self.file.read()
            break
        print("tex", self.file_path)
        self.file.close()

    def write(self, data):
        self.file = open(self.file_path, "wb")
        print("Writing", self.file_path)
        self.file.write(data)
        self.file.close()
