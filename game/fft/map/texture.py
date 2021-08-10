class Texture(object):
    def __init__(self):
        self.file_path = None
        self.data = None

    def read(self, files):
        """This currently only ever get a files len of 1 due to how Resource.read() and
        Resource.get_texture_files() handles situations.

        Asserting this for now until we fix on the other side.

        """
        assert len(files) == 1
        self.file_path = files[0]

        with open(self.file_path, "rb") as file:
            self.data = file.read()

    def write(self, data):
        with open(self.file_path, "wb") as file:
            print("Writing", self.file_path)
            file.write(data)
