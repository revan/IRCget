
import tqdm
import os


class Downloader:
    def __init__(self, filename, filesize):
        self.received_bytes = 0
        self._filename = filename
        self.download_dir = 'downloads'
        self.filepath = os.path.join(self.download_dir, filename)

        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        if os.path.exists(self.filepath):
            print("A file named", filename, "already exists. Deleting.")
            os.remove(self.filepath)

        self.file = open(self.filepath, "wb")
        self.progress = tqdm.tqdm(total=filesize)

    def write(self, data):
        self.file.write(data)
        newBytes = len(data)
        self.received_bytes += newBytes
        self.progress.update(newBytes)

    def close(self):
        try:
            self.file.close()
        except:
            pass
        finally:
            self.progress.close()

        print("Received file %s (%d bytes)." % (self._filename, self.received_bytes))
