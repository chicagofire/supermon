from contextlib import contextmanager
from jinja2 import Environment, PackageLoader
import os

_env = Environment(trim_blocks=True, lstrip_blocks=True, loader=PackageLoader('supermon', 'templates'))
_tmpl = _env.get_template('config.ini.tmpl')

_ctx = None

class _Program(object):
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

@contextmanager
def configfile(filename):
    global _ctx
    if _ctx:
        raise RuntimeError("Already have an open config file")
    _ctx = []
    yield
    if _ctx:
        with open(filename, 'w') as fd:
            fd.write(_tmpl.render(programs=_ctx, env=os.environ))
    _ctx = None
