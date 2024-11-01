import win32gui
import win32con as W
import logging

from threading import Thread
try: from .base import BasicIO
except: from base import BasicIO

ID_TO_TEXT = {
    6: 'YES',
    7: 'NO'
}

class Win(BasicIO):
    def __init__(self, config: dict, name=''):
        ''' Initiates a simply MessageBox output.
        Config: Has keys 'caption' (str) and 'type' (int). '''
        super().__init__(config,
                         is_reader = False, is_writer = True,
                         main_name = 'win-msgbox', user_name = name)
        if not 'type' in config: config['type'] = W.MB_ICONINFORMATION | W.MB_SYSTEMMODAL
        if not 'caption' in config: config['caption'] = 'XMT'
        
    def _write(self, text, override):
        config = self.local_config(override)
        out = win32gui.MessageBox(0, text, config['caption'], config['type'])
        self.logger.debug('User confirmed.', out)
        
    def write(self, text, override = {}):
        Thread(target=self._write, args=(text, override)).start()
        self.logger.debug('Started message box thread.')

    def read(self, prompt, override = {}):
        config = self.local_config(override)
        return ID_TO_TEXT[win32gui.MessageBox(0, prompt, config['caption'], config['type'] | W.MB_YESNO)]

