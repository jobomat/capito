"""Module for dealing with settings."""

class Settings:
    """Class for loading, managing and saving
    which are loaded from 3 different json files: 
      - 'site.settings.json' for global settings (company level)
      - 'project.settings.json' for project settings
      - 'user.settings.json' for user settings
    """
    def __init__(self, site, project, user):
        self.iter_dict = {}
        for k, v in site.items():
            v = project.get(k, v)
            v = user.get(k, v)
            self.set_attribute(k, v)

    def __iter__(self):
        self.iterator = iter(self.iter_dict)
        return self
        
    def __next__(self):
        return getattr(self, next(self.iterator))
        
    def set_attribute(self, key, value):
        val = value
        if isinstance(value, dict):
            val = Settings(value)
        elif isinstance(value, str):
            val = value.format(**self.__dict__)
        setattr(self, key, val)
        self.iter_dict[key] = val
    