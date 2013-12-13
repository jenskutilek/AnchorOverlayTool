from extensionID import extensionID
from grtools.SettingsWindow import SettingsWindow

my_settings = SettingsWindow(extensionID, "Anchor Overlay Tool Settings")

my_settings.column = 10
my_settings.width = 200

my_settings.add("preview", True, "Show in preview mode")
my_settings.add("lockOutlines", True, "Lock outlines")

my_settings.show()