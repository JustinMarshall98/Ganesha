class Texture:
    def __init__(self):
        self.file_path = None
        self.data = None

    def read(self, files):
        """TODO: This seems wrong to only get the first path and bail."""
        for path in files:
            self.file_path = path
            with open(path, "rb") as file:
                self.data = file.read()
            break

    def write(self, data):
        with open(self.file_path, "wb") as file:
            print("Writing", self.file_path)
            file.write(data)
