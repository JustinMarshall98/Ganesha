###############################################################################
# Name: __init__.py                                                           #
# Purpose: Editra Control Library                                             #
# Author: Cody Precord <cprecord@editra.org>                                  #
# Copyright: (c) 2007 Cody Precord <staff@editra.org>                         #
# Licence: wxWindows Licence                                                  #
###############################################################################

"""
Editra Control Library is library of custom controls developed for use in
Editra but are not tied to Editra's framework in anyway.

Controls:
  - PlateButton: Customizable flat button
  - ControlBox: Custom panel with easy layout and optional mini toolbar like
                control.
  - ControlBar: Custom mini toolbar like control used by ControlBox
  - OutputBuffer: Output display buffer that can be easily used with threads

"""

__author__ = "Cody Precord <cprecord@editra.org>"
__cvsid__ = "$Id: __init__.py 59256 2009-03-02 00:52:16Z CJP $"
__revision__ = "$Revision: 59256 $"


__all__ = ['auinavi', 'choicedlg', 'colorsetter', 'ctrlbox', 'eclutil',
           'ecpickers', 'elistmix', 'encdlg', 'finddlg', 'infodlg', 'panelbox',
           'outbuff', 'platebtn', 'pstatbar', 'segmentbk', 'txtentry']

#-----------------------------------------------------------------------------#

from auinavi import *
from choicedlg import *
from colorsetter import *
from ctrlbox import *
from eclutil import *
from ecpickers import *
from elistmix import *
from encdlg import *
from finddlg import *
from infodlg import *
from outbuff import *
from panelbox import *
from platebtn import *
from pstatbar import *
from segmentbk import *
from txtentry import *

# TODO: Delete module entries once all plugins have been updated to not 
#       import them sepearatly.
