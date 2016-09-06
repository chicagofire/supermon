from contextlib import contextmanager
from jinja2 import Environment, PackageLoader

class _Program(object):
    def __init__(self, name, command=None):
        self.programname = name
        if command:
            self.command = command

    def __str__(self):
        env = Environment(trim_blocks=True, lstrip_blocks=True, loader=PackageLoader('supermon', 'templates'))
        tmpl = env.get_template('config.ini.tmpl')
        return tmpl.render(self.__dict__)

@contextmanager
def program(name, command=None):
    yield _Program(name, command=command)
