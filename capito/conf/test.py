from capito.core.decorators import layered_settings

@layered_settings(layers=["default", "project", "projectuser", "user"])
class LayeredSettingsTest:
    def __init__(self):
        self.add_layered_settings()