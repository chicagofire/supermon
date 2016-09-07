# supermon

A basic collection of supervisord utilities.

- cron : an eventlistener which allows the user to specify a cron-like time specification for the time-range during which a process should be running. The time fields differ from normal cron as follows:
    * The hour field is expected to be a range where the first number is the starting hour and the second number is the ending hour. 
    * The minute field can be a range, a single value, or an asterisk. 
      * If a range, then, the first number goes with the first number in the hour field to form the start time of the program/group. The second number with the second hour number to form the stop time of the program/group.
      * If a single value, then, that number forms with both the first and second hour values to form the start and stop times of the program/group.
      * If an asterisk, then, that's equivalent to putting zero in the field.
    * The rest of the fields (day of month, month, day of week) impact the behavior in the same way as cron.
  Should be set up like:
  ```
  [eventlistener:foo-cron]
  command=supervisor_cron -p "foo:* 3-16 * * 1-7"
  events=TICK_60
  ```

- configtools : a small utility to allow converting a python script into a supervisor config
```python
# foo-config.py
from supermon import configtools

with configtools.program('foo', command='/path/to/foo -a argument1 -b argument 2') as pgm:
    pgm.exitcodes=[1,2,3]
```
```python
# parser.py
from supermon import configtools

def main():
    with configtools.configfile('foo.conf'):
        execfile('foo-config.py')

if __name__ == '__main__':
    main()
```

This is very specific to my needs. I want to generate small config files per program which can be included from the general supervisord.conf file.
