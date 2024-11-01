from collections.abc import Iterable
import logging

import requests

from .base import BasicIO

class Telegram(BasicIO):
    def __init__(self, config: dict, name=''):
        ''' Initiates a bot. Config keys are token, target (int or list of int), and parse_mode.'''
        super().__init__(config, is_reader = True, is_writer = True,
                         main_name = 'telegram', user_name = name)
        self.token = config['token']
        
    def write(self, text, override = {}):
        config = self.local_config(override)
        target = config['target']

        if not isinstance(config['target'], Iterable):
            target = [config['target']]

        for target_ind in target:
            requests.post(
                f'https://api.telegram.org/bot{self.token}/sendMessage',
                json = {
                    'text': text,
                    'chat_id': target_ind,
                    'parse_mode': config.get('parse_mode', '')
                }
            )
            self.logger.debug(f'Write: Sent a message of length {len(text)} to {target_ind}')

    def updates(self, **params):
        self.logger.debug(f'Updates: With parameters {params}')
        return requests.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params=params).json()['result']

    def offset(self):
        u = self.updates(limit=1)
        if not u:
            self.logger.debug(f'Offset: No updates.')
            return -1
        offset = u[-1]['update_id'] + 1
        self.logger.debug(f'Offset: {offset}')
        return offset

    def clean(self):
        self.logger.debug(f'Cleaning bot slate.')
        self.updates(offset=self.offset(), limit=1)

    def read(self, prompt = '', override = {}, poll_timeout=300):
        config = self.local_config(override)
        offset = self.offset()
        
        assert isinstance(config['target'], int), 'Only single-user input is supported'
        if prompt:
            self.logger.debug(f'Read: Sending prompt.')
            self.write(prompt, override)

        while True:
            updates = self.updates(timeout=poll_timeout, limit=1, allowed_updates=['message'])
            out, sender = updates[0]['message']['text'], updates[0]['message']['from']['id']
            self.clean()
            if sender == config['target'] and updates[0]['update_id'] >= offset:
                return out
            else:
                self.logger.debug(f'Read: Discarded irrelevant message.')
