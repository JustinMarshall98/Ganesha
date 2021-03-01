###############################################################################
# Name: ed_editv.py                                                           #
# Purpose: Editor view notebook tab implementation                            #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
Text editor buffer view control for the main notebook

@summary: Editor view

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: ed_editv.py 60368 2009-04-26 00:48:29Z CJP $"
__revision__ = "$Revision: 60368 $"

#--------------------------------------------------------------------------#
# Imports
import wx
import os

# Editra Libraries
import ed_glob
import ed_menu
import ed_stc
import ed_tab
from doctools import DocPositionMgr
from profiler import Profile_Get
from util import Log, SetClipboardText
from ebmlib import GetFileModTime

#--------------------------------------------------------------------------#

_ = wx.GetTranslation

#--------------------------------------------------------------------------#

class EdEditorView(ed_stc.EditraStc, ed_tab.EdTabBase):
    """Tab editor view for main notebook control."""
    DOCMGR = DocPositionMgr()
    RCLICK_MENU = None

    def __init__(self, parent, id_=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0, use_dt=True):
        """Initialize the editor view"""
        ed_stc.EditraStc.__init__(self, parent, id_, pos, size, style, use_dt)
        ed_tab.EdTabBase.__init__(self)

        # Attributes
        self._ignore_del = False

        # Initialize the classes position manager for the first control
        # that is created only.
        if not EdEditorView.DOCMGR.IsInitialized():
            EdEditorView.DOCMGR.InitPositionCache(ed_glob.CONFIG['CACHE_DIR'] + \
                                                  os.sep + u'positions')

        # Context Menu Events
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

        # Need to relay the menu events from the context menu to the top level
        # window to be handled on gtk. Other platforms don't require this.
        if wx.Platform == '__WXGTK__':
            self.Bind(wx.EVT_MENU,
                      lambda evt: wx.PostEvent(self.GetTopLevelParent(), evt))

    #---- EdTab Methods ----#

    def DoDeactivateTab(self):
        """Deactivate any active popups when the tab is no longer
        the active tab.

        """
        if self.AutoCompActive():
            self.AutoCompCancel()

        if self.CallTipActive():
            self.CallTipCancel()

    def DoOnIdle(self):
        """Check if the file has been modified and prompt a warning"""
        # Don't check while the file is loading
        if self.IsLoading():
            return

        if Profile_Get('CHECKMOD'):
            cfile = self.GetFileName()
            lmod = GetFileModTime(cfile)
            mtime = self.GetModTime()
            if mtime and not lmod and not os.path.exists(cfile):
                # File was deleted since last check
                wx.CallAfter(self.PromptToReSave, cfile)
            elif mtime < lmod:
                # Check if we should automatically reload the file or not
                if Profile_Get('AUTO_RELOAD', default=False) and \
                   not self.GetModify():
                    wx.CallAfter(self.DoReloadFile)
                else:
                    wx.CallAfter(self.AskToReload, cfile)

            # Check for changes to permissions
            readonly = self._nb.ImageIsReadOnly(self.GetTabIndex())
            if self.File.IsReadOnly() != readonly:
                if readonly:
                    # File is no longer read only
                    self._nb.SetPageImage(self.GetTabIndex(),
                                          str(self.GetLangId()))
                else:
                    # File has changed to be readonly
                    self._nb.SetPageImage(self.GetTabIndex(),
                                          ed_glob.ID_READONLY)
            else:
                pass

    def DoReloadFile(self):
        """Reload the current file"""
        ret, rmsg = self.ReloadFile()
        if not ret:
            errmap = dict(filename=cfile, errmsg=rmsg)
            mdlg = wx.MessageDialog(self,
                                    _("Failed to reload %(filename)s:\n"
                                      "Error: %(errmsg)s") % errmap,
                                    _("Error"),
                                    wx.OK | wx.ICON_ERROR)
            mdlg.ShowModal()
            mdlg.Destroy()

    def DoTabClosing(self):
        """Save the current position in the buffer to reset on next load"""
        if len(self.GetFileName()) > 1:
            EdEditorView.DOCMGR.AddRecord([self.GetFileName(),
                                           self.GetCurrentPos()])

    def DoTabOpen(self, ):
        """Called to open a new tab"""
        pass

    def DoTabSelected(self):
        """Performs updates that need to happen when this tab is selected"""
        Log("[ed_editv][info] Tab has file: %s" % self.GetFileName())
        self.PostPositionEvent()

    def GetName(self):
        """Gets the unique name for this tab control.
        @return: (unicode) string

        """
        return u"EditraTextCtrl"

    def GetTabMenu(self):
        """Get the tab menu
        @return: wx.Menu
        @todo: move logic from notebook to here

        """
        ptxt = self.GetTabLabel()

        menu = ed_menu.EdMenu()
        menu.Append(ed_glob.ID_NEW, _("New Tab"))
        menu.Append(ed_glob.ID_MOVE_TAB, _("Move Tab to New Window"))
        menu.AppendSeparator()
        menu.Append(ed_glob.ID_SAVE, _("Save \"%s\"") % ptxt)
        menu.Append(ed_glob.ID_CLOSE, _("Close \"%s\"") % ptxt)
        menu.Append(ed_glob.ID_CLOSEALL, _("Close All"))
        menu.AppendSeparator()
        menu.Append(ed_glob.ID_COPY_PATH, _("Copy Full Path"))
        return menu

    def GetTitleString(self):
        """Get the title string to display in the MainWindows title bar
        @return: (unicode) string

        """
        fname = self.GetFileName()
        title = os.path.split(fname)[-1]

        # Its an unsaved buffer
        if not len(title):
            title = fname = self.GetTabLabel()

        if self.GetModify() and not title.startswith(u'*'):
            title = u"*" + title
        return u"%s - file://%s" % (title, fname)

    def CanCloseTab(self):
        """Called when checking if tab can be closed or not
        @return: bool

        """
        if self._ignore_del:
            return True

        result = True
        if self.GetModify():
            # TODO: Move this method down from the frame to here
            result = self.GetTopLevelParent().ModifySave()
            result = result in (wx.ID_OK, wx.ID_NO)

        return result

    def OnTabMenu(self, evt):
        """Tab menu event handler"""
        e_id = evt.GetId()
        if e_id == ed_glob.ID_COPY_PATH:
            path = self.GetFileName()
            if path is not None:
                SetClipboardText(path)
        elif e_id == ed_glob.ID_MOVE_TAB:
            t = self.GetTopLevelParent()
            frame = wx.GetApp().OpenNewWindow()
            nb = frame.GetNotebook()
            parent = self.GetParent()
            pg_txt = parent.GetRawPageText(parent.GetSelection())
            nb.OpenDocPointer(self.GetDocPointer(), self.GetDocument(), pg_txt)
            self._ignore_del = True
            wx.CallAfter(parent.ClosePage)
        elif wx.Platform == '__WXGTK__' and \
             e_id in (ed_glob.ID_CLOSE, ed_glob.ID_CLOSEALL):
            # Need to relay events up to toplevel window on GTK for them to
            # be processed. On other platforms the propagate by them selves.
            wx.PostEvent(self.GetTopLevelParent(), evt)
        else:
            evt.Skip()

    #---- End EdTab Methods ----#

    def OnContextMenu(self, evt):
        """Handle right click menu events in the buffer"""
        if EdEditorView.RCLICK_MENU is None:
            EdEditorView.RCLICK_MENU = MakeMenu()
        self.PopupMenu(EdEditorView.RCLICK_MENU)
        evt.Skip()

    def PromptToReSave(self, cfile):
        """Show a dialog prompting to resave the current file
        @param cfile: the file in question

        """
        mdlg = wx.MessageDialog(self,
                                _("%s has been deleted since its "
                                  "last save point.\n\nWould you "
                                  "like to save it again?") % cfile,
                                _("Resave File?"),
                                wx.YES_NO | wx.ICON_INFORMATION)
        mdlg.CenterOnParent()
        result = mdlg.ShowModal()
        mdlg.Destroy()
        if result == wx.ID_YES:
            result = self.SaveFile(cfile)
        else:
            self.SetModTime(0)

    def AskToReload(self, cfile):
        """Show a dialog asking if the file should be reloaded
        @param cfile: the file to prompt for a reload of

        """
        mdlg = wx.MessageDialog(self,
                                _("%s has been modified by another "
                                  "application.\n\nWould you like "
                                  "to reload it?") % cfile,
                                  _("Reload File?"),
                                  wx.YES_NO | wx.ICON_INFORMATION)
        mdlg.CenterOnParent()
        result = mdlg.ShowModal()
        mdlg.Destroy()
        if result == wx.ID_YES:
            self.DoReloadFile()
        else:
            self.SetModTime(GetFileModTime(cfile))

#-----------------------------------------------------------------------------#

def MakeMenu():
    """Make the buffers context menu"""
    menu = ed_menu.EdMenu()
    menu.Append(ed_glob.ID_UNDO, _("Undo"))
    menu.Append(ed_glob.ID_REDO, _("Redo"))
    menu.AppendSeparator()
    menu.Append(ed_glob.ID_CUT, _("Cut"))
    menu.Append(ed_glob.ID_COPY, _("Copy"))
    menu.Append(ed_glob.ID_PASTE, _("Paste"))
    menu.AppendSeparator()
    menu.Append(ed_glob.ID_TO_UPPER, _("To Uppercase"))
    menu.Append(ed_glob.ID_TO_LOWER, _("To Lowercase"))
    menu.AppendSeparator()
    menu.Append(ed_glob.ID_SELECTALL, _("Select All"))
    return menu
