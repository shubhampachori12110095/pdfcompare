import os,subprocess
from pprint import pprint

class Hunspell():
    def __init__(self, dicts=['en_US']):
        self.cmd = ['hunspell', '-i', 'utf-8', '-a', '-d', ','.join(dicts)]
        self.proc = None
        self.buffer = ''

    def _start(self):
        try:
          self.proc = subprocess.Popen(self.cmd, shell=False, 
                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except OSError as e:
            self.proc = "%s failed: errno=%d %s" % (self.cmd, e.errno, e.strerror)
            raise OSError(self.proc)
        header = ''
        while True:
            more = self.proc.stdout.readline().rstrip()
            if len(more) > 5 and more[0:5] == '@(#) ':    # version line with -a
                self.version = more[5:]
                break
            elif len(more) > 9 and more[0:9] == 'Hunspell ': # version line w/o -a
                self.version = more
                break
            else:
                header += more  # stderr should be collected here. It does not work
        if len(header): self.header = header
        self.buffer = ''
        
    def _readline(self):
        # python readline() is horribly stupid on this pipe. It reads single
        # byte, just like java did in the 1980ies. Sorry, this is not
        # acceptable in 2013.
        if self.proc is None:
            raise Error("Hunspell_readline before _start")
        while True:
            idx = self.buffer.find('\n')
            if idx < 0:
                more = self.proc.stdout.read()
                if not len(more):
                    r = self.buffer
                    self.buffer = ''
                    return r
                self.buffer += more
            else:
                break
        r = self.buffer[0:idx+1]
        self.buffer = self.buffer[idx+1:]
        return r
 
    def check_words(self, words):
        if self.proc is None:
            self._start()
        childpid = os.fork()
        if childpid == 0:
            for w in words:
                self.proc.stdin.write(("^"+w+"\n").encode('utf8'))
            os._exit(0)
        self.proc.stdin.close()
        bad_words = {}
 
        while True:
            line = self._readline()
            if len(line) == 0:
                break
            line = line.rstrip()
            if not len(line) or line[0] in '*+-': continue

            if line[0] == '#': 
                car = line.split(' ')
                bad_words[car[1]] = []          # no suggestions
            elif line[0] != '&': 
                print "hunspell protocoll error: '%s'" % line
                continue        # unknown stuff
            # '& Radae 7 0: Radar, Ramada, Estrada, Prada, Rad, Roadie, Readable\n'
            a = line.split(': ')
            car = a[0].split(' ')
            cdr = a[1].split(', ')
            bad_words[car[1]] = cdr
        self.proc = None
        return bad_words

 
h = Hunspell()
pprint(h.check_words(["ppppp", '123', '', 'gorkicht', 'gemank', 'haus', '']))
pprint(h.check_words(["Radae", 'blood', 'mensch', 'green', 'blea', 'fork']))
pprint(dir(h))
pprint(h.version)
pprint(h.header)
