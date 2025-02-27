from dataclasses import dataclass
from driver.enums import CHANNEL, RANGE
import re
import configparser

@dataclass
class Channel:
    name:str = ""
    active:bool = False
    range: RANGE = RANGE.RANGE_10V
    offset: float = 0
    resolution: int = 12
    buffer = []
    max_adc = 32767.

    @property
    def flag(self):
        return getattr(CHANNEL, self.name)

    @property
    def unit(self):
        return 1e-3 if 'MV' in self.range.name else 1.
    
    @property
    def scale(self):
        value = int(re.findall(r'\d+', self.range.name)[0])
        return value*self.unit

    @property
    def scale_mv(self):
        return self.scale*1e3

    def next_range(self):
        new_value = self.range.value + 1
        new_range = RANGE(new_value) if new_value in RANGE._value2member_map_ else None
        if new_range is None: return False
        self.range = new_range        
        return (self.range.value == max(item.value for item in RANGE)) 

    def prv_range(self):
        new_value = self.range.value - 1
        new_range = RANGE(new_value) if new_value in RANGE._value2member_map_ else None
        if new_range is None: return False
        self.range = new_range
        return (self.range.value == min(item.value for item in RANGE))
    
    def save_channel(self):
       return {
            "name": self.name,
            "active": self.active,
            "range": self.range.value,
            "offset": self.offset,        
            }
    
    @classmethod
    def from_dict(cls, name:str, *args, **kwargs):
        try:
            config = configparser.ConfigParser()
            config.read("config.ini")
            settings = dict(config.items(name))
            settings['active'] = settings['active'] == 'True'
            settings['range'] = RANGE(int(settings['range']))
            settings['offset'] = float(settings['offset'])
            return cls(**settings)
        except Exception as e:
            print(f"Configuration, for channel {name} not found. Using default values.")
            return cls(name=name, *args, **kwargs)

