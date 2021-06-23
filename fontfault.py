#!/usr/bin/env python


import os, stat, errno
try:
    import _find_fuse_parts
except ImportError:
    pass
import fuse
from fuse import Fuse
from hyper import HTTPConnection

if not hasattr(fuse, '__version__'):
    raise RuntimeError("your fuse-py doesn't know of fuse.__version__, probably it's too old.")

fuse.fuse_python_api = (0, 2)

class MyStat(fuse.Stat):
    def __init__(self):
        self.st_mode = 0
        self.st_ino = 0
        self.st_dev = 0
        self.st_nlink = 0
        self.st_uid = 0
        self.st_gid = 0
        self.st_size = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0


FONT="/Roboto-Regular.ttf"
FONT_URL="/s/roboto/v27/KFOmCnqEu92Fr1Me5WZNCzc.ttf"
FONT_SIZE=81044

class FontFaultFS(Fuse):
    def __init__(self, version, usage, dash_s_do):
        super().__init__(version=version, usage=usage, dash_s_do=dash_s_do)
        self.c = HTTPConnection("fonts.gstatic.com")

    def getattr(self, path):
        st = MyStat()
        if path == '/':
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
        elif path == FONT:
            st.st_mode = stat.S_IFREG | 0o444
            st.st_nlink = 1
            st.st_size = FONT_SIZE
        else:
            return -errno.ENOENT
        return st

    def readdir(self, path, offset):
        for r in  '.', '..', FONT[1:]:
            yield fuse.Direntry(r)

    def open(self, path, flags):
        if path != FONT:
            return -errno.ENOENT
        accmode = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        if (flags & accmode) != os.O_RDONLY:
            return -errno.EACCES

    def read(self, path, size, offset):
        if path != FONT:
            return -errno.ENOENT

        self.c.request('GET',
                       FONT_URL,
                       headers={"Range":
                                "bytes=%s-%s" % (offset, offset + size)})
        resp = self.c.get_response()
        if (resp.status >= 300 or resp.status < 200):
            raise Error("HTTP request failed: %s" % resp.status)
        result = resp.read()
        return result[0:size]

def main():
    usage=Fuse.fusage
    server = FontFaultFS(version="%prog " + fuse.__version__,
                     usage=usage,
                     dash_s_do='setsingle')

    server.parse(errex=1)
    server.main()

if __name__ == '__main__':
    main()
