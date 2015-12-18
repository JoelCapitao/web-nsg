from inmemoryzip import InMemoryZip
import os


def zip_file(src, name):
    imz = InMemoryZip()
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            print('zipping %s as %s' % (os.path.join(dirname, filename), arcname))
            imz.append(absname, arcname)
    imz.writetofile(name)
    return imz
