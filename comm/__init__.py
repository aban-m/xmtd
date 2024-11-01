from .telegram import Telegram
from .win import Win

REGISTRY = {
    'telegram': Telegram,
    'win': Win
}

def bootstrap(iname, config, name):
    return REGISTRY[iname](config, name)
