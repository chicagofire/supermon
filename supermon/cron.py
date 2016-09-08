import argparse
import datetime
import os
import sys

from collections import namedtuple
from supervisor import childutils

Config = namedtuple('Config', ['programs', 'groups'])

def parse_range_list(spec, range_min, range_max, default=None):
    def validate(val):
        val = int(val)
        if val < range_min or val > range_max:
            raise ValueError('value (%s) out of range bounds [%s, %s]'%(val, range_min, range_max))
        return val

    if spec == '*':
        if default is not None:
            return set(default)
        else:
            return set(xrange(range_min, range_max + 1))

    ret = set([])
    for rng in spec.split(','):
        rng = rng.split('-')
        if len(rng) == 1:
            ret.add(validate(rng[0]))
        elif len(rng) == 2:
            ret.update(set(xrange(validate(rng[0]), validate(rng[1]) + 1)))
        else:
            raise ValueError('Invalid range in day_of_month spec: %s'%day_of_month)
    return ret

def parse_times(minute, hour):
    start_minute = end_minute = None
    start_hour = end_hour = None
    
    try:
        start_minute = end_minute = int(minute)
    except ValueError:
        if minute == '*':
            start_minute = end_minute = 0
        elif '-' in minute:
            s, e = minute.split('-')
            start_minute = int(s)
            end_minute = int(e)
        else:
            raise ValueError('Invalid minute range: %s. Expected single int or range'%minute)

    if '-' in hour:
        s, e = hour.split('-')
        start_hour = int(s)
        end_hour = int(e)
    else:
        raise ValueError('Invalid hour range: %s. Expected range.'%hour)

    return datetime.time(start_hour, start_minute), datetime.time(end_hour, end_minute)

class CronSpec(object):
    def __init__(self, minute, hour, day_of_month, month, day_of_week):
        self.starttime, self.endtime = parse_times(minute, hour)
        self.day_of_month = parse_range_list(day_of_month, 1, 31, default=[])
        self.month = parse_range_list(month, 1, 12)
        self.day_of_week = parse_range_list(day_of_week, 0, 7, default=[])
        if 0 in self.day_of_week:
            # internally, 7 == Sunday
            self.day_of_week.add(7)

    def __str__(self):
        return 'starttime: %s, endtime: %s, day of month: %s, month: %s, day of week: %s'%(
            self.starttime, self.endtime, self.day_of_month, self.month, self.day_of_week)

    def test(self, dt):
        '''
        .. method:: test(dt)

        Tests if the datetime argument passes the cron spec. Assumes the datetime argument
        and the cronspec times are equivalent timezones.

        :param datetime dt: The datetime to check.
        :return: True if the spec is met else false
        :rtype: bool
        '''
        return (dt.month in self.month and
                (dt.day in self.day_of_month or dt.weekday() + 1 in self.day_of_week) and
                (self.starttime <= dt.time() < self.endtime))

def check_processes(rpc, config, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, test=False):
    now = datetime.datetime.now()
    infos = rpc.supervisor.getAllProcessInfo()
    for info in infos:
        pid = info['pid']
        name = info['name']
        group = info['group']

        spec = None
        if name in config.programs:
            spec = config.programs[name]
        elif group in config.groups:
            spec = config.groups[name]
        else:
            stderr.write('IGNORING %s:%s\n'%(group, name))
            continue

        stderr.write('Testing %s:%s [%s] against %s\n'%(group, name, now, spec))
        if spec.test(now):
            if info['statename'] in ('STOPPED', 'EXITED'):
                stderr.write('Starting %s:%s\n'%(group, name))
                rpc.supervisor.startProcess(name)
        elif info['statename'] in ('STARTING', 'RUNNING', 'BACKOFF'):
            stderr.write('Stopping %s:%s\n'%(group, name))
            rpc.supervisor.stopProcess(name)

# pass in stdin / stdout so we can test
def runforever(config, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, test=False):
    rpc = childutils.getRPCInterface(os.environ)
	first_time = True
    while True:
        if not first_time:
            headers, payload = childutils.listener.wait(stdin, stdout)
            eventname = headers['eventname']
            if eventname.startswith('TICK'):
                check_processes(rpc, config, stdin=stdin, stdout=stdout, stderr=stderr, test=test)

            childutils.listener.ok(stdout)
        else:
            first_time = False
            check_processes(rpc, config, stdin=stdin, stdout=stdout, stderr=stderr, test=test)

        stderr.flush()
        if test:
            break

def main():
    parser = argparse.ArgumentParser(description='supermon.cron - event listener')
    parser.add_argument('-p', '--program', help='program to monitor', action='append')
    parser.add_argument('-g', '--group', help='group to monitor', action='append')
    args = parser.parse_args()

    config = Config({}, {})
    if args.program:
        for program_spec in args.program:
            program_name, crontab = program_spec.split(':')
            minute, hour, day_of_month, month, day_of_week = crontab.split()
            config.programs[program_name] = CronSpec(minute, hour, day_of_month, month, day_of_week)

    if args.group:
        for group_spec in args.group:
            group_name, crontab = program_spec.split(':')
            minute, hour, day_of_month, month, day_of_week = crontab.split()
            config.groups[group_name] = CronSpec(minute, hour, day_of_month, month, day_of_week)

    runforever(config)

if __name__ == '__main__':
    main()

