import pathlib
import os

import sys
sys.path.insert(0, '../xmtlib')

from xmt.recipes.storage import FileStorage
from comm.telegram import Bot
from yaml import safe_load as load_yaml

import time
from datetime import datetime
from threading import Thread, Event


from croniter import croniter
import pytz
tz = pytz.FixedOffset(3)

import logging
logger = logging.getLogger('cronjob')


class Profile:
    @classmethod
    def from_file(cls, path):
        spec, cwd = load_yaml(open(path)), str(pathlib.Path(path).parent.absolute())
        return cls(spec, cwd)
    
    def __init__(self, spec: dict, cwd = '.'):
        if cwd is None: cwd = os.getcwd()
        self.cwd = pathlib.Path(cwd).absolute()
        self.io = spec['io']
        self.recipes = spec['recipes']
        self.recipe_names = tuple(self.recipes.keys())
        self.name = spec['name']
        
        if 'path' in spec or not 'recipes' in spec['path']:
            spec['path'] = {
                'recipes': os.path.join(self.cwd, '../recipes')
            }

        self.env = FileStorage(spec['path']['recipes'])

        self.bot = Bot(self.io['telegram'])
        self.show = self.bot.broadcast

class Cron:
    def __init__(self, name, cron_expr, func, *args, **kwargs):
        self.running = False
        self.cron_expr = cron_expr
        self.croniter = croniter(self.cron_expr, tz.localize(datetime.now()))

        self.name = name
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def time_to_sleep(self):  
        delta = (self.croniter.get_next(datetime)-tz.localize(datetime.now())).total_seconds()
        self._last_delta = delta
        if delta < 0:
            return self.time_to_sleep() # will get accustomed.
        return delta

    def _loop(self):
        while self.running:
            delta = self.time_to_sleep()
            logger.debug(f'{self.name}: Must sleep for {int(delta)} seconds.')
            for _ in range(int(delta)+1):
                try: time.sleep(1)
                except KeyboardInterrupt: self.running = False; return
                if not self.running:
                    return
            if self.running:
                self.func(*self.args, **self.kwargs)
                logger.debug(f'{self.name}: Finished execution.')
            else:
                return

    def start(self):
        self.running = True
        Thread(target=self._loop).start()

    def stop(self):
        self.running = False

    
