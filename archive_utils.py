
import glob
import os
import patoolib
import shutil
import tempfile

def unrar(filepath):
    print("Attempting unrar...")
    try:
        patoolib.extract_archive(filepath)
    except patoolib.util.PatoolError:
        pass


def unzip(filepath):
    print("Extracting zip.")
    with tempfile.TemporaryDirectory() as tempDir:
        download_dir = os.path.dirname(filepath)
        patoolib.extract_archive(filepath, outdir=tempDir)

        dest = os.path.join(download_dir, "searchresults.txt")

        f = glob.glob(os.path.join(tempDir, '*'))[0]
        shutil.move(f, dest)
        return dest