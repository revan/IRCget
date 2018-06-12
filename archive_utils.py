
import os


def unrar(filepath):
    print("Attempting unrar...")
    os.system("unrar e \"%s\"" % filepath)


def unzip(filepath):
    # TODO: make this cross-platform by removing system calls.
    print("Extracting zip")
    download_dir = os.path.dirname(filepath)
    os.system("mkdir -p " + os.path.join(download_dir, "search"))
    os.system("unzip \"" + filepath + "\" -d "
              + os.path.join(download_dir, "search"))
    os.system("mv " + os.path.join(download_dir, "search", "* ")
              + os.path.join(download_dir, "searchresults.txt"))
    return os.path.join(download_dir, "searchresults.txt")
