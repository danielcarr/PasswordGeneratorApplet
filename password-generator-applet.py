#! /usr/bin/env python3

import base64
import hmac
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('MatePanelApplet', '4.0')
from gi.repository import Gtk, Gdk, MatePanelApplet

class AppletContents(Gtk.Box):

    def __init__(self, applet, default_length=8):
        Gtk.Box.__init__(self)

        self.length_selector_is_open = False
        self.applet = applet
        self.selected_length = default_length
        self.parameter_entry = Gtk.Entry()
        self.parameter_entry.set_placeholder_text('Parameter')
        self.parameter_entry.connect('activate', self.enter_clicked)
        self.parameter_entry.connect('key-press-event', self.key_press_received)
        self.parameter_entry.connect('button-press-event', self.capture_focus)
        self.secret_entry = Gtk.Entry(visibility=False)
        self.secret_entry.set_placeholder_text('Master Password')
        self.secret_entry.connect('activate', self.enter_clicked)
        self.secret_entry.connect('key-press-event', self.key_press_received)
        self.secret_entry.connect('button-press-event', self.capture_focus)
        self.length_button = Gtk.Button('{:d}'.format(self.selected_length))
        self.length_button.connect('clicked', self.open_length_slider)
        self.length_button.connect('key-press-event', self.key_press_received)
        self.pack_start(self.parameter_entry, True, True, 0)
        self.pack_start(self.secret_entry, True, True, 0)
        self.pack_start(self.length_button, False, False, 0)

    def capture_focus(self, widget, event):
        self.applet.request_focus(event.time)

    def key_press_received(self, widget, event):
        if event.keyval == Gdk.KEY_Tab:
            if widget is self.parameter_entry:
                self.secret_entry.grab_focus()
                return True
            elif widget is self.secret_entry:
                self.open_length_slider(self.length_button)
                self.set_focus_child(None)
                return True
        return False

    def enter_clicked(self, widget):
        parameter = self.parameter_entry.get_text()
        secret = self.secret_entry.get_text()
        if len(parameter) < 1:
            self.parameter_entry.grab_focus()
        elif len(secret) < 1:
            self.secret_entry.grab_focus()
        else:
            generated_password = generate_password(parameter, secret, self.selected_length)
            Gtk.Clipboard().get(Gdk.SELECTION_CLIPBOARD).set_text(generated_password, -1)
            self.parameter_entry.set_text('')
            self.secret_entry.set_text('')

    def open_length_slider(self, widget):
        if not self.length_selector_is_open:
            self.length_popup = Gtk.Window.new(Gtk.WindowType.POPUP)
            length_slider = Gtk.Scale.new_with_range(Gtk.Orientation.VERTICAL, 6, 32, 1)
            length_slider.set_draw_value(False)
            length_slider.set_round_digits(0)
            length_slider.set_inverted(True)
            length_slider.set_value(self.selected_length)
            length_slider.connect('value_changed', self.length_changed)
            applet_origin = Gdk.Window.get_origin(self.length_button.get_window())
            button_allocation = self.length_button.get_allocation()
            origin_x = applet_origin.x + button_allocation.x
            origin_y = applet_origin.y + button_allocation.height
            self.length_popup.move(origin_x, origin_y)
            h = 100 # TODO: make height a function of the size of the range
            w = self.length_button.get_allocated_width()
            self.length_popup.add(length_slider)
            self.length_popup.set_size_request(w, -1)
            self.length_popup.set_default_size(w, h)
            self.length_popup.connect('destroy', self.closed_length_selector)
            self.length_popup.show_all()
            self.length_selector_is_open = True
        else:
            self.length_popup.destroy()

    def length_changed(self, widget):
        self.selected_length = int(widget.get_value())
        self.update_length(self.selected_length)

    def closed_length_selector(self, window):
        self.length_selector_is_open = False
        self.parameter_entry.grab_focus()

    def update_length(self, new_length):
        self.length_button.set_label('{:d}'.format(new_length))

def applet_fill(applet):
    # you can use this path with gio/gsettings
    settings_path = applet.get_preferences_path()
    # TODO: get default length from settings
    default_length = 10

    applet.add(AppletContents(applet))
    applet.set_background_widget(applet)
    applet.show_all()
    applet.set_tooltip_text('Enter parameter and secret and press enter to generate password of selected length in the clipboard')

def applet_factory(applet, iid, data):
    if iid != 'PasswordGeneratorApplet':
        return False
    applet_fill(applet)
    return True

def generate_password(parameter, secret, length=10):
    key = bytes(secret, 'utf-8')
    param = parameter.encode('utf-8')
    digest = hmac.new(key, msg=param, digestmod='sha1').digest()
    return str(base64.b64encode(digest)[:length], 'utf-8')

MatePanelApplet.Applet.factory_main('PasswordGeneratorAppletFactory', True,
                                    MatePanelApplet.Applet.__gtype__,
                                    applet_factory, None)
