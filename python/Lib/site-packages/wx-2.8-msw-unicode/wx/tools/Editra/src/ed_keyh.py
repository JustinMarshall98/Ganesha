###############################################################################
# Name: ed_keyh.py                                                            #
# Purpose: Editra's Vi Emulation Key Handler                                  #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2008 Cody Precord <staff@editra.org>                         #
# License: wxWindows License                                                  #
###############################################################################

"""
This is the Vi Emulation key handler. When vi emulation is turned on in the
preferences, it intercepts all keypresses in the ed_stc.EditraStc and interprets
them accordingly. In the future other key handlers may be added.

@summary: Custom keyhandler interface

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__svnid__ = "$Id: ed_keyh.py 60431 2009-04-28 22:03:48Z CJP $"
__revision__ = "$Revision: 60431 $"

#-------------------------------------------------------------------------#
# Imports
import re
import wx, wx.stc

# Editra Libraries
import ed_event
import ed_glob
import ed_basestc
import ed_stc
import string

# Vi command regex patterns
VI_DCMD_RIGHT = '[bBcdeEGhHlLMwWy|{}$<>]'
VI_DOUBLE_P1 = re.compile('[cdy<>][0-9]*' + VI_DCMD_RIGHT)
VI_DOUBLE_P2 = re.compile('[0-9]*[cdy<>]' + VI_DCMD_RIGHT)
VI_SINGLE_REPEAT = re.compile('[0-9]*[bBCDeEGhjJkloOpPsuwWxX{}~|+-]')
VI_GCMDS = re.compile('g[fg]')
VI_FCMDS = re.compile(u'[0-9]*[ftFT].')
VI_BM = re.compile(u'[m`].')
VI_IDENT = re.compile(u'\*|\#')
NUM_PAT = re.compile('[0-9]*')
REPEAT_RE = re.compile("([0-9]*)(.*)")

#commands that operator on motions
VI_CMD_MOTIONS = re.compile(u'[0-9]*[cyd].*')

VI_FIND_FORWARD = 1
VI_FIND_REVERSE = -1

#-------------------------------------------------------------------------#
# Use this base class to derive any new keyhandlers from. The keyhandler is
# called upon by the active buffer when ever a key press event happens. The
# handler then has the responsibility of deciding what to do with the key.
#
class KeyHandler:
    """KeyHandler base class"""
    def __init__(self, stc):
        self.stc = stc

    def ClearMode(self):
        """Clear any key input modes to normal input mode"""
        evt = ed_event.StatusEvent(ed_event.edEVT_STATUS, self.stc.GetId(),
                                   '', ed_glob.SB_BUFF)
        wx.PostEvent(self.stc.GetTopLevelParent(), evt)

    def GetHandlerName(self):
        """Get the name of this handler
        @return: string

        """
        return u'NULL'

    def PreProcessKey(self, key_code, ctrldown=False,
                      cmddown=False, shiftdown=False, altdown=False):
        """Pre process any keys before they get to the char handler
        @param key_code: Raw keycode
        @keyword ctrldown: Is the control key down
        @keyword cmddown: Is the Command key down (Mac osx)
        @keyword shiftdown: Is the Shift key down
        @keyword altdown: Is the Alt key down
        @return: bool

        """
        return False

    def ProcessKey(self, key_code, ctrldown=False,
                   cmddown=False, shiftdown=False, altdown=False):
        """Process the key and return True if it was processed and
        false if it was not. The key is recieved at EVT_CHAR.
        @param key_code: Raw keycode
        @keyword ctrldown: Is the control key down
        @keyword cmddown: Is the Command key down (Mac osx)
        @keyword shiftdown: Is the Shift key down
        @keyword altdown: Is the Alt key down
        @return: bool

        """
        return False

#-------------------------------------------------------------------------#

class ViKeyHandler(KeyHandler):
    """Defines a key handler for Vi emulation
    @summary: Handles keypresses according to Vi emulation.

    """

    # Vi Mode declarations
    NORMAL, \
    INSERT \
        = range(2)

    def __init__(self, stc):
        KeyHandler.__init__(self, stc)

        # Attributes
        self.mode = 0
        self.last = u''
        self.last_find = u''
        self.cmdcache = u''
        self.bookmarks = {}

        # Use Insert mode by default
        self.SetMode(ViKeyHandler.INSERT)

    def ClearMode(self):
        """Clear the mode back to default input mode"""
        self.stc.SetCaretWidth(1)
        self.last = self.cmdcache = u''
        KeyHandler.ClearMode(self)

    def GetHandlerName(self):
        """Get the name of this handler"""
        return u'VI'

    def SetMode(self, newmode):
        """Set the keyhandlers mode
        @param newmode: New mode name to change to

        """
        self.mode = newmode
        self.last = self.cmdcache = u'' # Clear any partially procesed keys
        if self.mode == ViKeyHandler.NORMAL:
            self.stc.SetCaretWidth(10)
            msg = u'NORMAL'
        elif self.mode == ViKeyHandler.INSERT:
            self.stc.SetCaretWidth(1)
            msg = u'INSERT'

        # Update status bar
        evt = ed_event.StatusEvent(ed_event.edEVT_STATUS, self.stc.GetId(),
                                   msg, ed_glob.SB_BUFF)
        wx.PostEvent(self.stc.GetTopLevelParent(), evt)

    def PreProcessKey(self, key_code, ctrldown=False,
                      cmddown=False, shiftdown=False, altdown=False):
        """Pre process any keys before they get to the char handler
        @param key_code: Raw keycode
        @keyword ctrldown: Is the control key down
        @keyword cmddown: Is the Command key down (Mac osx)
        @keyword shiftdown: Is the Shift key down
        @keyword altdown: Is the Alt key down
        @return: bool

        """
        if not shiftdown and key_code == wx.WXK_ESCAPE:
            # If Vi emulation is active go into Normal mode and
            # pass the key event to the char handler by not processing
            # the key.
            self.SetMode(ViKeyHandler.NORMAL)
            return False
        elif (ctrldown or cmddown) and key_code == ord('['):
            self.SetMode(ViKeyHandler.NORMAL)
            return True
        else:
            return False

    def ProcessKey(self, key_code, ctrldown=False,
                   cmddown=False, shiftdown=False, altdown=False):
        """Processes vi commands
        @param key_code: Raw key code
        @keyword cmddown: Command/Ctrl key is down
        @keyword shiftdown: Shift Key is down
        @keyword altdown : Alt key is down
        @todo: complete rewrite, this was initially intended as a quick hack
               put together for testing but now has implemented everything.

        """
        if self.mode == ViKeyHandler.INSERT or ctrldown or cmddown or altdown:
            return False

        # Add key to cache
        self.cmdcache = self.cmdcache + unichr(key_code)

        # Don't process key if the cache is empty
        if not len(self.cmdcache):
            return False

        # Check for repeat last action command
        if self.cmdcache == u'.':
            cmd = self.last
        else:
            cmd = self.cmdcache

        # Gather common needed data
        cpos = self.stc.GetCurrentPos()
        cline = self.stc.LineFromPosition(cpos)
        ccol = self.stc.GetColumn(cpos)
        mw = self.stc.GetTopLevelParent()
        mpane = mw.GetEditPane()

        # Check for change from NORMAL mode to Command mode
        if u':' in cmd:
            self.cmdcache = u''
            mpane.ShowCommandControl(ed_glob.ID_COMMAND)

        # Single key commands
        if len(cmd) == 1 and (cmd in 'AHILM0^$nia/?:'):
            if  cmd in u'A$': # Insert at EOL
                self.stc.GotoPos(self.stc.GetLineEndPosition(cline))
            elif cmd == u'H': # Go first visible line # todo allow num
                self.stc.GotoIndentPos(self.stc.GetFirstVisibleLine())
            elif cmd in u'I^': # Insert at line start / Jump line start
                self.stc.GotoIndentPos(cline)
            elif cmd == u'0': # Jump to line start column 0
                self.stc.GotoPos(self.stc.PositionFromLine(cline))
            elif cmd == u'L': # Goto start of last visible line # todo allow num
                self.stc.GotoIndentPos(self.stc.GetLastVisibleLine())
            elif cmd == u'M': # Goto middle line of display
                self.stc.GotoIndentPos(self.stc.GetMiddleVisibleLine())
            elif cmd == u'a': # insert mode after current pos
                self.stc.GotoPos(cpos + 1)
            elif cmd in u'/?':
                if mw is not None:
                    mpane.ShowCommandControl(ed_glob.ID_QUICK_FIND)

            # Return to insert mode
            if cmd in u'aAiI':
                self.SetMode(ViKeyHandler.INSERT)

            # Save last command and clear cache
            self.last = cmd
            self.cmdcache = u''

        # Repeatable 1 key commands
        elif re.match(VI_SINGLE_REPEAT, cmd):
            rcmd = cmd[-1]
            repeat = cmd[0:-1]
            if repeat == u'':
                repeat = 1
            else:
                repeat = int(repeat)

            args = list()
            kargs = dict()
            cmd_map = { u'b' : self.stc.WordPartLeft,
                       u'B' : self.stc.WordLeft,
                       u'e' : self.stc.WordPartRightEnd,
                       u'E' : self.stc.WordRightEnd,
                       u'h' : self.stc.CharLeft,
                       u'j' : self.stc.LineDown,
                       u'k' : self.stc.LineUp,
                       u'l' : self.stc.CharRight,
                       u'o' : self.stc.AddLine,
                       u'O' : self.stc.AddLine,
                       u'p' : self.stc.Paste,
                       u'P' : self.stc.Paste,
                       u's' : self.stc.Cut,
                       u'u' : self.stc.Undo,
                       u'w' : self.stc.WordPartRight,
                       u'W' : self.stc.WordRight,
                       u'x' : self.stc.Cut,
                       u'X' : self.stc.Cut,
                       u'{' : self.stc.ParaUp,
                       u'}' : self.stc.ParaDown,
                       u'~' : self.stc.InvertCase }

            # Command is a Put command
            if rcmd in u'pP':
                success = False
                newline = False
                # Check the clipboard
                if wx.TheClipboard.Open():
                    td = wx.TextDataObject()
                    success = wx.TheClipboard.GetData(td)
                    wx.TheClipboard.Close()

                # We got the text from the clipboard so put it in the buffer
                if success:
                    text = td.GetText()
                    if text[-1] == '\n':
                        if cline == self.stc.GetLineCount() - 1 and rcmd == u'p':
                            self.stc.NewLine()
                        else:
                            if rcmd == u'P':
                                self.stc.GotoLine(cline)
                            else:
                                self.stc.GotoLine(cline + 1)
                        newline = True
                    elif rcmd == u'p' and \
                         self.stc.LineFromPosition(cpos + 1) == cline:
                        self.stc.CharRight()
            elif rcmd in u'sxX~':
                if rcmd in u'sx~':
                    tmp = self.stc.GetTextRange(cpos, cpos + repeat)
                    tmp = tmp.split(self.stc.GetEOLChar())
                    end = cpos + len(tmp[0])
                else:
                    tmp = self.stc.GetTextRange(cpos - repeat, cpos)
                    tmp = tmp.split(self.stc.GetEOLChar())
                    end = cpos - len(tmp[-1])
                    tmp = end
                    end = cpos
                    cpos = tmp

                if cpos == self.stc.GetLineEndPosition(cline):
                    self.stc.SetSelection(cpos - 1, cpos)
                else:
                    self.stc.SetSelection(cpos, end)
                repeat = 1
            elif rcmd == u'O':
                kargs['before'] = True
                kargs['indent'] = True
            elif rcmd == u'o':
                kargs['indent'] = True

            # Start an undo action so all changes can be rolled back at once
            self.stc.BeginUndoAction()
            if rcmd in u'CD': # Cut line right
                self.stc.SetSelection(cpos,
                                  self.stc.GetLineEndPosition(cline + (repeat - 1)))
                self.stc.Cut()
            elif rcmd == u'J':
                self.stc.SetTargetStart(cpos)
                if repeat == 1:
                    repeat = 2
                self.stc.SetTargetEnd(self.stc.PositionFromLine(cline + repeat - 1))
                self.stc.LinesJoin()
            elif rcmd == u'G':
                # Goto line or to end depending on context
                if repeat == 1 and '1' not in cmd:
                    repeat = self.stc.GetLineCount()
                self.stc.GotoLine(repeat - 1)
            elif rcmd == u'+':
                # Goto indent position at x lines from current line
                self.stc.GotoIndentPos(cline + repeat)
            elif rcmd == u'-':
                # Goto indent position at x lines before current line
                self.stc.GotoIndentPos(cline - repeat)
            elif rcmd == u'|':
                # Goto column number at current line
                self.stc.GotoColumn(repeat - 1)
            else:
                if rcmd not in cmd_map:
                    return True
                run = cmd_map[rcmd]
                for count in xrange(repeat):
                    run(*args, **kargs)

            # Do a Put command that is to be repeated
            if rcmd == u'p':
                if newline:
                    self.stc.GotoIndentPos(cline + repeat)
                else:
                    self.stc.GotoPos(cpos + 1)
            elif rcmd == u'P':
                if newline:
                    self.stc.GotoIndentPos(cline)
                else:
                    self.stc.GotoPos(cpos)
#             elif rcmd == u'u':
#                 self.GotoPos(cpos)
            elif rcmd in u'CoOs':
                self.SetMode(ViKeyHandler.INSERT)
            self.stc.EndUndoAction()

            # Save this action and clear command cache
            self.last = cmd
            self.cmdcache = u''

        # 2 key commands
        elif re.match(VI_DOUBLE_P1, cmd) or \
             re.match(VI_DOUBLE_P2, cmd) or \
             re.match(re.compile('[cdy]0'), cmd):

            # Handle repetitions
            if re.match(re.compile('[cdy]0'), cmd):
                rcmd = cmd
            else:
                rcmd = re.sub(NUM_PAT, u'', cmd)

            # Get the number of repetitions from the command string
            repeat = re.subn(re.compile(VI_DCMD_RIGHT), u'', cmd, 2)[0]
            if repeat == u'':
                repeat = 1
            else:
                repeat = int(repeat)

            if rcmd[-1] not in u'bBeEGhHlLMwW$|{}0':
                # Go to start of line
                self.stc.SetCurrentPos(self.stc.GetLineStartPosition(cline))
                if repeat != 1 or rcmd not in u'>><<':
                    self.stc.SetSelectionStart(self.stc.GetCurrentPos())
                    self.stc.SetSelectionEnd(self.stc.PositionFromLine(cline + repeat))
            else:
                self.stc.SetAnchor(self.stc.GetCurrentPos())
                mcmd = { u'b' : self.stc.WordPartLeftExtend,
                         u'B' : self.stc.WordLeftExtend,
                         u'e' : self.stc.WordPartRightEndExtend,
                         u'E' : self.stc.WordRightEndExtend,
                         u'h' : self.stc.CharLeftExtend,
                         u'l' : self.stc.CharRightExtend,
                         u'w' : self.stc.WordPartRightExtend,
                         u'W' : self.stc.WordRightExtend,
                         u'{' : self.stc.ParaUpExtend,
                         u'}' : self.stc.ParaDownExtend}

                # Select to end of line
                if u'$' in rcmd:
                    pos = self.stc.GetLineEndPosition(cline + repeat - \
                                                  len(self.stc.GetEOLChar()))
                    self.stc.SetCurrentPos(pos)
                elif u'G' in rcmd:
                    # Check if command is valid
                    if repeat == 0:
                        self.cmdcache = u''
                        return True

                    # Select to end of file
                    if repeat == 1 and u'1' not in cmd: # Default eof
                        self.stc.SetAnchor(self.stc.GetLineEndPosition(cline - 1))
                        repeat = self.stc.GetLength()
                    elif repeat < cline + 1:
                        self.stc.SetAnchor(self.stc.PositionFromLine(cline + 1))
                        repeat = self.stc.PositionFromLine(repeat - 1)
                        cline = self.stc.LineFromPosition(repeat) - 1
                    elif repeat > cline:
                        self.stc.SetAnchor(self.stc.GetLineEndPosition(cline - 1))
                        if cline == 0:
                            repeat = self.stc.PositionFromLine(repeat)
                        else:
                            repeat = self.stc.GetLineEndPosition(repeat - 1)
                    else:
                        self.stc.SetAnchor(self.stc.PositionFromLine(cline))
                        repeat = self.stc.PositionFromLine(cline + 1)
                    self.stc.SetCurrentPos(repeat)
                elif rcmd[-1] in u'HM':
                    fline = self.stc.GetFirstVisibleLine()
                    lline = self.stc.GetLastVisibleLine()

                    if u'M' in rcmd:
                        # Get the line in middle of visible lines
                        repeat = self.stc.GetMiddleVisibleLine() + 1
                    elif fline + repeat > lline:
                        repeat = lline
                    else:
                        repeat = fline + repeat

                    if repeat > cline:
                        # Move selection lines after middle line
                        self.stc.SetAnchor(self.stc.PositionFromLine(cline))
                        self.stc.SetCurrentPos(self.stc.PositionFromLine(repeat))
                    else:
                        # Move select lines before middle line
                        self.stc.SetAnchor(self.stc.PositionFromLine(repeat - 1))
                        self.stc.SetCurrentPos(self.stc.PositionFromLine(cline + 1))
                elif u'L' in rcmd:
                    fline = self.stc.GetFirstVisibleLine()
                    lline = self.stc.GetLastVisibleLine()
                    if lline - repeat < fline:
                        repeat = fline
                    else:
                        repeat = lline - repeat

                    if repeat < cline:
                        self.stc.SetAnchor(self.stc.PositionFromLine(cline))
                        self.stc.SetCurrentPos(self.stc.PositionFromLine(repeat))
                    else:
                        self.stc.SetAnchor(self.stc.PositionFromLine(cline))
                        self.stc.SetCurrentPos(self.stc.PositionFromLine(repeat + 2))
                elif u'|' in rcmd:
                    if repeat == 1 and u'1' not in cmd:
                        repeat = 0
                    self.stc.SetCurrentCol(repeat)
                elif rcmd[-1] == u'0':
                    self.stc.SetCurrentCol(0)
                else:
                    doit = mcmd[rcmd[-1]]
                    for x in xrange(repeat):
                        doit()

            # Begin Undo action so all changes can be rolled back in one undo
            self.stc.BeginUndoAction()
            if re.match(re.compile('c|c' + VI_DCMD_RIGHT), rcmd):
                # Cut to selection and enter insert mode
                if rcmd == u'cc':
                    self.stc.SetSelectionEnd(self.stc.GetSelectionEnd() - \
                                         len(self.stc.GetEOLChar()))
                self.stc.Cut()
                self.SetMode(ViKeyHandler.INSERT)
            elif re.match(re.compile('d|d' + VI_DCMD_RIGHT), rcmd):
                # Cut selection and stay in normal mode
                self.stc.Cut()
            elif re.match(re.compile('y|y' + VI_DCMD_RIGHT), rcmd):
                # Copy selection
                self.stc.Copy()
                self.stc.GotoPos(cpos)
            elif rcmd == u'<<':
                # Unindent selection
                self.stc.BackTab()
            elif rcmd == u'>>':
                # Indent selection
                self.stc.Tab()
            else:
                pass
            self.stc.EndUndoAction()

            if rcmd in '<<>>' or rcmd[-1] == u'G':
                self.stc.GotoIndentPos(cline)

            # Save the completed command and clear cache
            self.last = cmd
            self.cmdcache = u''
        elif re.match(VI_GCMDS, cmd):
            rcmd = cmd[-1]
            if rcmd == u'g':
                self.stc.GotoLine(0)
            elif rcmd == u'f':
                pass # TODO: gf (Goto file at cursor)
            self.last = cmd
            self.cmdcache = u''
        elif re.match(VI_IDENT, cmd):
            direction = {u'#' : VI_FIND_REVERSE, u'*' : VI_FIND_FORWARD}[cmd]
            self._VimFindIdent(direction)
            self.cmdcache = u''
        # Bookmarks
        elif re.match(VI_BM, cmd):
            self._VimBookmark(cmd)
            self.cmdcache = u''
        # Motions towards a character
        elif re.match(VI_FCMDS, cmd):
            self._VimFindChar(cmd)
            self.last_find = cmd
            self.cmdcache = u''
        elif cmd == u';' and self.last_find:
            self._VimFindChar(self.last_find)
            self.cmdcache = u''
        elif cmd == u',' and self.last_find:
            self._VimFindChar(self._VimFindCharReverseCmd(self.last_find))
            self.cmdcache = u''
        else:
            pass

        # Update status bar
        if mw and self.mode == ViKeyHandler.NORMAL:
            evt = ed_event.StatusEvent(ed_event.edEVT_STATUS, self.stc.GetId(),
                                       u'NORMAL  %s' % self.cmdcache,
                                       ed_glob.SB_BUFF)
            wx.PostEvent(self.stc.GetTopLevelParent(), evt)

        return True

    def _VimBookmark(self, cmd):
        """Handle vim-style bookmarks"""
        label = cmd[1]
        
        # Add bookmark
        if cmd[0] == u'm':
            cline = self.stc.GetCurrentLine()
            text, ccol = self.stc.GetCurLine()

            if label in string.ascii_lowercase: # Local bookmarks
                bm_handle = self.stc.MarkerAdd(cline, ed_basestc.MARK_MARGIN)
                self.bookmarks[label] = (bm_handle, ccol)
            elif label in string.ascii_uppercase: # Global bookmarks
                # TODO
                pass
        else: # ` goto bookmark
            if label in self.bookmarks:
                bm_handle, col = self.bookmarks[label]
                line = self.stc.MarkerLineFromHandle(bm_handle)
                if line != -1:
                    pos = self.stc.FindColumn(line, col)
                    self.stc.GotoPos(pos)
                else: #line == -1 means the bookmark was deleted by the user
                    del self.bookmarks[label] #XXX: is this safe?

    def _VimFindCharReverseCmd(self, cmd):
        """Reverse the direction of the find char command given by `cmd`
        @return: a string representing the command in reverse direction

        """
        if not cmd: return cmd
        return cmd[:-2] + cmd[-2].swapcase() + cmd[-1]

    def _VimFindChar(self, cmd, extend=False):
        """Vim f/F/t/T motion
        @param cmd: command string
        @keyword extend: extend the selection

        """
        repeat, cmd = SplitRepeatCmd(cmd)
        ch = cmd[1] #character to find
        cmd_type = cmd[0]
        mcmd = { u'f' : self.stc.FindNextChar,
                 u'F' : self.stc.FindPrevChar,
                 r't' : self.stc.FindTillNextChar,
                 r'T' : self.stc.FindTillPrevChar,
        }
        mcmd[cmd_type](ch, repeat, extend)

    def _VimFindIdent(self, direction=VI_FIND_FORWARD):
        """Vim motion to find next (or previous) occurance of identifier
        @param direction: VI_FIND_

        """
        ident = self.stc.GetIdentifierUnderCursor()
        flags = wx.stc.STC_FIND_WHOLEWORD | wx.stc.STC_FIND_MATCHCASE
        if not ident:
            return # Nothing to find
        if direction == VI_FIND_FORWARD: # Search forward
            self.stc.GotoPos(self.stc.GetSelectionEnd())
            self.stc.SearchAnchor()
            res = self.stc.SearchNext(flags, ident)
            if res == -1: # Nothing found, search from top
                self.stc.DocumentStart()
                self.stc.SearchAnchor()
                self.stc.SearchNext(flags, ident)
        elif direction == VI_FIND_REVERSE: # Search backward
            self.stc.SearchAnchor()
            res = self.stc.SearchPrev(flags, ident)
            if res == -1: # Nothing found, search from bottom
                self.stc.DocumentEnd()
                self.stc.SearchAnchor()
                self.stc.SearchPrev(flags, ident)
        else:
            raise Exception("Invalid search direction")

        #XXX: -10 is a hack for reasonable scrolling
        #     otherwise line would be first, which is odd
        self.stc.ScrollToLine(self.stc.GetCurrentLine()-10)


# ---------------------------------------------------------------------------- #
# Utility Functions

def SplitRepeatCmd( cmd ):
    """Split the command strings into a pair (repeat, rest)

    >>>SplitRepeatCmd( '3ab' )
    (3, 'ab')
    >>>SplitRepeatCmd( 'abc' )
    (1, 'abc')
    >>>SplitRepeatCmd( 'ab2' )
    (1, 'ab2')

    """
    cmd = cmd.strip() #just in case
    repeat, rest = re.match( REPEAT_RE, cmd ).groups()
    if repeat == '':
        repeat = 1
    else:
        repeat = int(repeat)
    return (repeat, rest)
