from gi.repository import Gtk, Adw
from .preferences import UserPreferences

@Gtk.Template(resource_path='/moe/nyarchlinux/waifudownloader/../data/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'
    nsfw_switch = Gtk.Template.Child("nsfw")
    doh_switch = Gtk.Template.Child("doh")
    provider_dropdown = Gtk.Template.Child("provider")

    def __init__(self, window, **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.settings = UserPreferences()
        self.nsfw_switch.set_active(bool(self.settings.get_preference("nsfw")))
        self.doh_switch.set_active(bool(self.settings.get_preference("doh")))
        self.providers = ["Auto", "Waifu.im", "Danbooru", "yande.re"]
        self.provider_dropdown.set_model(Gtk.StringList.new(self.providers))
        selected_provider = self.settings.get_preference("provider") or "Auto"
        self.provider_dropdown.set_selected(
            self.providers.index(selected_provider) if selected_provider in self.providers else 0
        )
        self.nsfw_switch.connect('notify::active', self.toggle_nsfw)
        self.doh_switch.connect('notify::active', self.toggle_doh)
        self.provider_dropdown.connect('notify::selected', self.change_provider)

    def toggle_nsfw(self, switch, _active):
        pref = self.nsfw_switch.get_active()
        self.settings.set_preference("nsfw", pref)

    def toggle_doh(self, switch, _active):
        self.settings.set_preference("doh", self.doh_switch.get_active())

    def change_provider(self, dropdown, _property):
        index = dropdown.get_selected()
        provider = self.providers[index] if 0 <= index < len(self.providers) else "Auto"
        self.settings.set_preference("provider", provider)
        self.window.update_provider_selection(provider)
