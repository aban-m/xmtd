import os
import logging
import time

import sys
sys.path.insert(0, '../xmtlib')

from models import Cron, Profile
from xmt.recipes.dynamic.core import DynamicRecipe
from xmt.recipes.storage import FileStorage


def shower(profile, recipe):
    profile.show(recipe.execute()[1])

def nop(*args, **kwargs): pass

class Runtime:
    def __init__(self, path, lifeline_cron = '* * * * *', name=''):
        self.logger = logging.getLogger('xmtd' + (':'+name) if name else '')
        self.logger.info(f'Initializing XMTD. Working directory: {path}')
        
        self.path = path
        self.profiles = {}
        self.recipes = {}
        self.cronjobs = {}
        self.env = FileStorage(os.path.join(path, 'recipes'))
        self.cronjobs[0] = [Cron('SYSTEM', lifeline_cron, nop)]
        
        for profile_path in os.listdir(os.path.join(path, 'profiles')):
            profile_path = os.path.join(path, 'profiles', profile_path)
            profile = Profile.from_file(profile_path)
            name = profile.name
            self.profiles[name] = profile
            if name in self.cronjobs:
                self.logger.critical('Found name conflict.')
                raise ValueError(f'{name} was duplicated.')
            
            self.logger.debug(f'Loaded profile {name} from {profile_path}.')

            self.cronjobs[name] = []

                
            for pack in profile.recipes:
                rname, rdec = list(pack.items())[0]
                if not rname in self.recipes:
                    spec = self.env.load_recipe(rname)
                    self.recipes[rname] = DynamicRecipe(spec, self.env)
                    self.logger.debug(f'Loaded new recipe: {rname}.')
                for i, cron_expr in enumerate(rdec['cron']):
                    cron = Cron(f'{name}:{rname}'+('*'*i),
                                 cron_expr,
                                 self.write,
                                 name, rname, rdec)
                    self.cronjobs[name].append(cron)
                    self.logger.debug(f'Defined cronjob for {name}\'s {rname}. Pattern: {cron_expr}.')

    def write(self, profile_name, recipe_name, iparams):
        recipe = self.recipes[recipe_name]
        _, text = recipe.execute(poststate = iparams['with'])
        self.profiles[profile_name].write(iparams['where'], text, iparams['recon'])

             
    def boot(self):
        self.logger.info(f'Starting XMTD booting sequence.')
        for _, rlist in self.cronjobs.items():
            self.logger.debug(f'Processing cronjobs for {_}.')
            for i, cronjob in enumerate(rlist):
                cronjob.start()

    def _stop(self, who):
        for i, cronjob in enumerate(self.cronjobs.get(who, [])):
            cronjob.stop()

    def stop(self, who=None):
        self.logger.debug(f'Stopping all cronjobs.')
        if who is None:
            for name in self.cronjobs:
                self.logger.info(f'Stopping cronjobs for {name if name else "<SYSTEM>"}.')
                self._stop(name)
        else: self._stop(who)


