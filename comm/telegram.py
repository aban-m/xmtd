import requests

import logging
logger = logging.getLogger('telegram-io')


class Bot:
    def __init__(self, config):
        self.token = config['token']
        self.parse_mode = config['parse_mode']
        self.audience = config['audience']
        self._config = config
        
    def send(self, text, user_id):
        requests.post(
            f'https://api.telegram.org/bot{self.token}/sendMessage',
            json = {
                'chat_id': user_id,
                'text': text,
                'parse_mode': self.parse_mode
            }
        )
        logger.debug(f'Sent a message of length {len(text)} to {user_id}')


    def broadcast(self, text):
       logger.info(f'Received BROADCAST request.')
       for user_id in self.audience:
           self.send(text, user_id)


