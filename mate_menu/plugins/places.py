# -*- coding: utf-8 -*-

# Copyright (C) 2007-2014 Clement Lefebvre <root@linuxmint.com>
# Copyright (C) 2015 Martin Wimpress <code@ubuntu-mate.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.

import gettext
import os
import shutil
import subprocess
from gi.repository import GLib, Gio, Gtk
from mate_menu.easybuttons import *
from mate_menu.easygsettings import EasyGSettings
from mate_menu.execute import Execute
from urllib import unquote

# i18n
gettext.install("mate-menu", "/usr/share/locale")

class pluginclass( object ):

    def __init__(self, mateMenuWin, toggleButton):

        self.mateMenuWin = mateMenuWin
        self.toggleButton = toggleButton

        # Read UI file
        builder = Gtk.Builder()
        builder.add_from_file( os.path.join( '/', 'usr', 'share', 'mate-menu',  'plugins', 'places.glade' ))

        self.placesBtnHolder    = builder.get_object( "places_button_holder" )
        self.editableBtnHolder  = builder.get_object( "editable_button_holder" )
        self.scrolledWindow=builder.get_object("scrolledwindow2")
        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window = builder.get_object( "mainWindow" )

        # Set 'heading' property for plugin
        self.heading = _("Places")

        # This should be the first item added to the window in glade
        self.content_holder = builder.get_object( "Places" )

        # Items to get custom colors
        self.itemstocolor = [ builder.get_object( "viewport2" ) ]

        # Settings
        self.settings = EasyGSettings("org.mate.mate-menu.plugins.places")

        self.settings.notifyAdd( "icon-size", self.RegenPlugin )
        self.settings.notifyAdd( "show-computer", self.RegenPlugin )
        self.settings.notifyAdd( "show-desktop", self.RegenPlugin )
        self.settings.notifyAdd( "show-home_folder", self.RegenPlugin )
        self.settings.notifyAdd( "show-network", self.RegenPlugin )
        self.settings.notifyAdd( "show-trash", self.RegenPlugin )
        self.settings.notifyAdd( "custom-names", self.RegenPlugin )
        self.settings.notifyAdd( "allow-scrollbar", self.RegenPlugin )
        self.settings.notifyAdd( "show-gtk-bookmarks", self.RegenPlugin )
        self.settings.notifyAdd( "height", self.changePluginSize )
        self.settings.notifyAdd( "width", self.changePluginSize )

        self.loadSettings()

        self.content_holder.set_size_request( self.width, self.height )

    def wake (self) :
        if ( self.showtrash == True ):
            self.refreshTrash()

    def destroy( self ):
        self.settings.notifyRemoveAll()

    def changePluginSize( self, settings, key, args = None):
        self.allowScrollbar = self.settings.get( "bool", "allow-scrollbar" )
        self.width = self.settings.get( "int", "width" )
        if (self.allowScrollbar == False):
            self.height = -1
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER )
        else:
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )
            self.height = self.settings.get( "int", "height" )
        self.content_holder.set_size_request( self.width, self.height )

    def RegenPlugin( self, *args, **kargs ):
        self.loadSettings()
        self.ClearAll()
        self.do_standard_places()
        self.do_custom_places()
        self.do_gtk_bookmarks()

    def loadSettings( self ):
        self.width = self.settings.get( "int", "width" )
        self.allowScrollbar = self.settings.get( "bool", "allow-scrollbar" )
        self.showGtkBookmarks = self.settings.get( "bool", "show-gtk-bookmarks" )
        self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )
        self.height = self.settings.get( "int", "height" )
        self.content_holder.set_size_request( self.width, self.height )
        if (self.allowScrollbar == False):
            self.height = -1
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER )
        self.content_holder.set_size_request( self.width, self.height )
        self.iconsize = self.settings.get( "int", "icon-size" )

        # Check default items

        self.showcomputer = self.settings.get( "bool", "show-computer" )
        self.showhomefolder = self.settings.get( "bool", "show-home-folder" )
        self.shownetwork = self.settings.get( "bool", "show-network" )
        self.showdesktop = self.settings.get( "bool", "show-desktop" )
        self.showtrash = self.settings.get( "bool", "show-trash" )

        # Get paths for custom items
        self.custompaths = self.settings.get( "list-string", "custom-paths" )

        # Get names for custom items
        self.customnames = self.settings.get( "list-string", "custom-names" )

        # Plugin icon
        self.icon = self.settings.get( "string", "icon" )
        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.settings.get( "bool", "sticky")
        self.minimized = self.settings.get( "bool", "minimized")

    def ClearAll(self):
        for child in self.placesBtnHolder.get_children():
            child.destroy()
        for child in self.editableBtnHolder.get_children():
            child.destroy()

    #Add standard places
    def do_standard_places( self ):

        if ( self.showcomputer == True ):
            Button1 = easyButton( "computer", self.iconsize, [_("Computer")], -1, -1 )
            Button1.connect("clicked", self.ButtonClicked, "xdg-open computer:")
            Button1.show()
            self.placesBtnHolder.pack_start( Button1, False, False, 0)
            self.mateMenuWin.setTooltip( Button1, _("Browse all local and remote disks and folders accessible from this computer") )

        if ( self.showhomefolder == True ):
            Button2 = easyButton( "user-home", self.iconsize, [_("Home Folder")], -1, -1 )
            Button2.connect( "clicked", self.ButtonClicked, "xdg-open %s " % os.environ["HOME"])
            Button2.show()
            self.placesBtnHolder.pack_start( Button2, False, False, 0)
            self.mateMenuWin.setTooltip( Button2, _("Open your personal folder") )

        if ( self.shownetwork == True):
            mate_settings = Gio.Settings.new("org.mate.interface")
            icon_theme = mate_settings.get_string( "icon-theme" )
            Button3 = easyButton( "network-workgroup", self.iconsize, [_("Network")], -1, -1)
            Button3.connect("clicked", self.ButtonClicked, "xdg-open network:")
            Button3.show()
            self.placesBtnHolder.pack_start( Button3, False, False, 0)
            self.mateMenuWin.setTooltip( Button3, _("Browse bookmarked and local network locations") )

        if ( self.showdesktop == True ):
            # Determine where the Desktop folder is (could be localized)
            desktopDir = os.path.join(os.environ["HOME"] + "Desktop")
            try:
                from configobj import ConfigObj
                configPath = os.environ.get("XDG_CONFIG_HOME",
                                            os.path.join( os.environ["HOME"], ".config"))
                config = ConfigObj(os.path.join(configPath, "user-dirs.dirs"))
                tmpdesktopDir = os.path.expandvars(config['XDG_DESKTOP_DIR'])
                if os.path.exists(tmpdesktopDir):
                    desktopDir = tmpdesktopDir
            except Exception, detail:
                print detail
            Button4 = easyButton( "desktop", self.iconsize, [_("Desktop")], -1, -1 )
            Button4.connect("clicked", self.ButtonClicked, "xdg-open \"" + desktopDir + "\"")
            Button4.show()
            self.placesBtnHolder.pack_start( Button4, False, False, 0)
            self.mateMenuWin.setTooltip( Button4, _("Browse items placed on the desktop") )

        if ( self.showtrash == True ):
            self.trashButton = easyButton( "user-trash", self.iconsize, [_("Trash")], -1, -1 )
            self.trashButton.connect("clicked", self.ButtonClicked, "xdg-open trash:")
            self.trashButton.show()
            self.trashButton.connect( "button-release-event", self.trashPopup )
            self.refreshTrash()
            self.placesBtnHolder.pack_start( self.trashButton, False, False, 0)
            self.mateMenuWin.setTooltip( self.trashButton, _("Browse deleted files") )

    def do_custom_places( self ):
        for index in range( len(self.custompaths) ):
            path = self.custompaths[index]
            path = path.replace("~", os.environ["HOME"])
            command = ("xdg-open \"" + path + "\"")
            currentbutton = easyButton( "folder", self.iconsize, [self.customnames[index]], -1, -1 )
            currentbutton.connect( "clicked", self.ButtonClicked, command )
            currentbutton.show()
            self.placesBtnHolder.pack_start( currentbutton, False, False, 0)

    def do_gtk_bookmarks( self ):
        if self.showGtkBookmarks:
            bookmarksFile = os.path.join(GLib.get_user_config_dir(), "gtk-3.0", "bookmarks")
            if not os.path.exists(bookmarksFile):
                bookmarksFile = os.path.join(GLib.get_home_dir(), ".gtk-bookmarks")
            if not os.path.exists(bookmarksFile):
                return
            bookmarks = []
            with open(bookmarksFile, "r") as f:
                for line in f:
                    #line = line.replace('file://', '')
                    line = line.rstrip()
                    if not line:
                        continue
                    parts = line.split(' ', 1)

                    if len(parts) == 2:
                        path, name = parts
                    elif len(parts) == 1:
                        path = parts[0]
                        name = os.path.basename(os.path.normpath(path))
                    bookmarks.append((name, path))

            for name, path in bookmarks:
                name = unquote(name)
                currentbutton = easyButton( "folder", self.iconsize, [name], -1, -1 )
                currentbutton.connect( "clicked", self.launch_gtk_bookmark, path )
                currentbutton.show()
                self.placesBtnHolder.pack_start( currentbutton, False, False, 0)

    def launch_gtk_bookmark (self, widget, path):
        self.mateMenuWin.hide()
        subprocess.Popen(['xdg-open', path])

    def trashPopup( self, widget, event ):
        if event.button == 3:
            trashMenu = Gtk.Menu()
            emptyTrashMenuItem = Gtk.MenuItem(_("Empty trash"))
            trashMenu.append(emptyTrashMenuItem)
            trashMenu.show_all()
            emptyTrashMenuItem.connect ( "activate", self.emptyTrash, widget )
            self.mateMenuWin.stopHiding()
            trashMenu.attach_to_widget(widget, None)
            trashMenu.popup(None, None, None, None, 3, 0)

    def emptyTrash( self, menu, widget):
        trash_info = os.path.join(os.path.expanduser('~'), '.local','share','Trash','info')
        trash_files = os.path.join(os.path.expanduser('~'), '.local','share','Trash','files')
        shutil.rmtree(trash_info)
        shutil.rmtree(trash_files)
        self.trashButton.setIcon('user-trash')

    def ButtonClicked( self, widget, Exec ):
        self.mateMenuWin.hide()
        if Exec:
            Execute( Exec )

    def do_plugin( self ):
        self.do_standard_places()
        self.do_custom_places()
        self.do_gtk_bookmarks()

    def refreshTrash (self):
        iconName = 'user-trash'
        trash_info = os.path.join(os.path.expanduser('~'), '.local','share','Trash','info')
        if os.path.exists(trash_info) and os.listdir(trash_info):
            iconName = 'user-trash-full'

        self.trashButton.setIcon(iconName)
