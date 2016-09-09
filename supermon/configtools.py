from collections import defaultdict
from contextlib import contextmanager
from jinja2 import Environment, PackageLoader
import os

_env = Environment(trim_blocks=True, lstrip_blocks=True, loader=PackageLoader('supermon', 'templates'))
_tmpl = _env.get_template('config.ini.tmpl')

_ctx = None

class Descriptor(object):
    def __init__(self, name, main_attr, attrs=[]):
        self.name = name
        self.main_attr = main_attr
        self.attrs = attrs
        self.type = type(self.name, (), {key: None for key in [main_attr] + attrs})
        self.value = None

    def __set__(self, obj, value):
        if self.value is not None:
            raise ValueError("%s.%s is already set"%(self.name, self.main_attr))

        self.value = self.type()
        setattr(self.value, self.main_attr, value)

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        return self.value

    def __del__(self, obj):
        self.value = None

class _Program(object):
    httpok = Descriptor("httpok", "url", ['email', 'subject'])
    schedule = Descriptor("schedule", "crontab", ['email', 'subject'])

    def __init__(self, name, command=None):
        self.programname = name
        if command:
            self.command = command

    def __str__(self):
        return _tmpl.render(programs=[self], env=os.environ)

@contextmanager
def program(name, command=None):
    pgm = _Program(name, command=command)
    if _ctx is not None:
        _ctx.append(pgm)
    yield pgm

def cronblocks(programs):
    blocks = defaultdict(list)
    for program in programs:
        if program.schedule:
            blocks[(program.schedule.email, program.schedule.subject)].append(program)

    return blocks

@contextmanager
def configfile(filename):
    global _ctx
    if _ctx:
        raise RuntimeError("Already have an open config file")
    _ctx = []
    yield
    if _ctx:
        with open(filename, 'w') as fd:
            fd.write(_tmpl.render(programs=_ctx, env=os.environ, cronblocks=cronblocks(_ctx)))
    _ctx = None
