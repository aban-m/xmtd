import logging
import time

class BasicIO:
    def __init__(self, config: dict, is_reader: bool, is_writer: bool, main_name, user_name):
        self.config = config
        if user_name: user_name = ':'+user_name
        self.logger = logging.getLogger(f'io:{main_name}{user_name}')
        self.is_reader = is_reader
        self.is_writer = is_writer

        self.logger.info(f'Initiated instance.')

    def local_config(self, override):
        config = self.config.copy()
        config.update(override)
        return config

    def write(self, *args, **kwargs):
        raise NotImplementedError('Writing has not been implemented.')

    def read(self, *args, **kwargs):
        raise NotImplementedError('Reading has not been implemented.')

    def read_with_delay(self, *args, **kwargs):
        t = time.time()
        out = self.read(*args, **kwargs)
        return out, time.time() - t
