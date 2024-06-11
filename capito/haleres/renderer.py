import json
from pathlib import Path
from typing import Any, List

from capito.haleres.settings import Settings
from capito.haleres.utils import replace


class RendererFlag:
    """Class representing a renderer flag. 

    Attributes (in braces shows if attribute is needed in json renderer file and it's behaviour):
        name (mandatory): The nice name of the flag for gui representation.
        flag (mandatory): The flag including the hypen(s) (-f or --log-file).
        type (mandatory): The flag"int", "str", "bool" or "choice"
        choices (mandatory if type is choice): Contains the choices.
        protected (optional defaults to False): If True, the flag can be excluded from guis.
        mandatory (optional): Can be used to force actions on validating the settings.
        value (optional): The value of the flag.
                          If value is "None" it will not appear in json and flag will not be rendered.
                          Flags of type "bool" only will appear if value is set to "True".
    """
    def __init__(self):
        self.name: str = None
        self.flag: str = None
        self.type: str = None
        self.protected: bool = None
        self.mandatory: bool = None
        self.choices: List[Any] = None
        self.value: Any = None
    
    def as_dict(self) -> dict:
        """Returns the flag serialized as a dictionary.

        Returns:
            dict: Serialized values for all flag attributes.
        """
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def from_dict(self, dictionary:dict) -> "RendererFlag":
        """Fills all attributes according to the given flag dict.

        Args:
            dictionary (dict): A flag-dictionary as represented in a renderer config file.

        Returns:
            RendererFlag: The current RendererFlag instance (self).
        """
        for k, v in dictionary.items():
            setattr(self, k, v)
        return self
    
    def set_value(self, value:Any):
        """Sets the value attribute. Performs checks and conversions according to flag-type.

        Args:
            value (Any): The value to set.

        Raises:
            ValueError if flag type is "int" but value is not.
        """
        if self.type == "int":
            self.value = None if not value else int(value)
        elif self.type == "choice":
            if isinstance(self.choices[0], int):
                self.value = int(value)
            else:
                self.value = value
        elif self.type == "bool":
            self.value = True if value else False
        else:
            self.value = value

    def __str__(self):
        if not self.value:
            return ""
        if self.type == "bool":
            return self.flag
        return f"{self.flag} {self.value}"
    
    def __repr__(self):
        return f"{__class__.__name__}(name={self.flag}, value={self.value}, {self.name=}, {self.type=}, {self.protected=}, {self.mandatory=})"


class RendererEnvVar:
    """Minimal Class for Renderer env vars. Providing:
        - structured access
        - easy output 
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def as_dict(self):
        return self.__dict__

    def __str__(self):
        return f"export {self.name}={self.value}"

    def __repr__(self):
        return f"RendererEnvVar(name='{self.name}', value='{self.value}')"


class Renderer:
    """Class representing a renderer for rendering at HLRS.
    
    It's parts get configured via json file.
    It's current state also can be serialized to a json file.

    It consists of these main components:
        - templates for (render) job file creation
            - header_template
            - per_job_template
            - per_frame_template
        - environment variables for these jobs
            self.env_vars is a list of RendererEnvVar instances (see above).
        - flags for the renderer
            self.flags is a list of RendererFlag instances (see above)
    
    One hack atm is the parameter "single_frame_renderer" which indicates a
    special case of haleres renderjobs (e.g. Arnold kick jobs). Here the jobs 
    won't get created on basis of the provided framelist but on bases of 
    all the files in the "input/scenes" subfolder of a haleres jobfolder. 
    """
    def __init__(self):
        self.name = ""
        self.executable:str = None
        self.header_template: str = None
        self.per_job_template:str = None
        self.per_frame_template:str = None
        self.pre_render_template:str = None
        self.post_render_template:str = None
        self.combined_commands_template:str = None
        self.single_frame_renderer:bool = False
        self.env_vars: List[RendererEnvVar]
        self.flags: List[RendererFlag]
        self.flag_lookups: List[dict]
        self._exclude_from_serialization = [
            "flags", "env_vars", "exclude_from_serialization"
        ]
    
    def from_json(self, json_file:str):
        self._load_json(json_file)
        return self

    def _load_json(self, json_file:str):
        filepath = Path(json_file)
        renderer_config = json.loads(filepath.read_text())
        self.flags = [RendererFlag().from_dict(flag) for flag in renderer_config["flags"]]
        self.env_vars = [RendererEnvVar(**dv) for dv in renderer_config["env_vars"]]
        for key, val in renderer_config.items():
            if key not in self._exclude_from_serialization:
                setattr(self, key, val)
        self.name = self.name or filepath.stem

    def save_json(self, json_file:str):
        renderer_config = {
            key: val for key, val in self.__dict__.items()
            if key not in self._exclude_from_serialization
        }
        renderer_config["env_vars"] = [ev.as_dict() for ev in self.env_vars]
        renderer_config["flags"] = [flag.as_dict() for flag in self.flags]
        with Path(json_file).open("w") as f:
            json.dump(renderer_config, f, indent=4)

    def get_editable_flags(self):
        return [f for f in self.flags if not f.protected]

    def get_env_string(self):
        return "\n".join(str(env_var) for env_var in self.env_vars)

    def get_per_frame_string(self):
        return replace(self.per_frame_template, {"render_command": self.get_render_command()})
    
    def get_combined_commands_string(self):
        return replace(self.combined_commands_template, {"render_command": self.get_render_command()})

    def get_per_job_string(self):
        data = {
            "header": self.header_template,
            "env_vars": self.get_env_string(),
        }
        return replace(self.per_job_template, data)
        
    def get_flag_string(self):
        flag_strings = [str(f) for f in self.flags if str(f)]
        return " \\\n".join(flag_strings)
    
    def get_render_command(self):
        cmds = [
            f"$WS_BASE_PATH/renderers/{self.executable} \\",
            self.get_flag_string(),
        ]
        return "\n".join(cmds)
    
    def get_flag(self, flag: str):
        flags = [f for f in self.flags if f.flag == flag]
        if flags:
            return flags[0]

    def get_flag_lookup_dict(self):
        result_dict =  {}
        for flag_lookup in self.flag_lookups:
            flag = self.get_flag(flag_lookup["from_flag"])
            if flag:
                result_dict[flag_lookup["key"]] = flag_lookup["lookup"][flag.value]
        return result_dict


class RendererProvider:
    """Provides all the renderers defined via json-files
    found in a subfolder called "renderer_configs"
    either in the haleres module itself (default renderers)
    or located next to the haleres settings file (user renderers).
    User defined renderers will overwrite default renderers with the same name. 
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        settings_dir = Path(settings.settings_file).parent
        haleres_dir = Path(__file__).parent
        self.renderer_dirs = [haleres_dir / "renderer_configs", settings_dir / "renderer_configs"]
        self.renderers = {}
        for renderer_dir in self.renderer_dirs:
            for conf in renderer_dir.glob("*.json"):
                self.renderers[conf.stem] = Renderer().from_json(str(conf))