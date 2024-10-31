import os
import logging
import time

import sys
sys.path.insert(0, '../xmtlib')

from models import Cron, Profile, logger as cron_logger
from xmt.recipes.dynamic.core import DynamicRecipe

logger = logging.getLogger('xmtd')

def shower(profile, recipe):
    profile.show(recipe.execute()[1])

class Runtime:
    def __init__(self, path):
        logger.info(f'Initializing XMTD. Working directory: {path}')
        self.path = path
        self.profiles = {}
        self.cronjobs = {}
        for profile_path in os.listdir(os.path.join(path, 'profiles')):
            profile_path = os.path.join(path, 'profiles', profile_path)
            logger.info(f'Processing profile: {profile_path}')
            profile = Profile.from_file(profile_path)
            self.cronjobs[profile.name] = []
            self.profiles[profile.name] = profile
            
            for recipe_name, cron_exprs in profile.recipes.items():
                logger.info(f'Processing recipe: {recipe_name}.')
                if isinstance(cron_exprs, str): cron_exprs = [cron_exprs]
                actual_recipe = DynamicRecipe(profile.env.load_recipe(recipe_name), profile.env)
                do = lambda: profile.show(actual_recipe.execute()[1])

                for i, cron_expr in enumerate(cron_exprs):
                    self.cronjobs[profile.name].append(Cron(f'{profile.name}-{recipe_name}-#{i}',
                                                            cron_expr, shower, profile, actual_recipe))
                    logger.debug(f'Cronjob for {recipe_name} initiated -- pattern {cron_expr}')
                
    def boot(self):
        logger.info(f'Starting XMTD booting sequence.')
        for _, rlist in self.cronjobs.items():
            logger.debug(f'Processing cronjobs for {_}.')
            for i, cronjob in enumerate(rlist):
                cronjob.start()

    def _stop(self, who):
        for i, cronjob in enumerate(self.cronjobs.get(who, [])):
            cronjob.stop()

    def stop(self, who=None):
        logger.debug(f'Stopping all cronjobs.')
        if who is None:
            for name in self.cronjobs:
                logger.info(f'Stopping cronjobs for {name}.')
                self._stop(name)
        else: self._stop(who)


