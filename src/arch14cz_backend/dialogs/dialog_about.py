#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from arch14cz_backend import __version__, __date__
import arch14cz_backend

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class DialogAbout(QtWidgets.QFrame):
	
	def __init__(self):
		
		QtWidgets.QFrame.__init__(self)
		
		self.setMinimumWidth(400)
		self.setLayout(QtWidgets.QVBoxLayout())
		
		content = QtWidgets.QFrame()
		content.setLayout(QtWidgets.QHBoxLayout())
		self.layout().addWidget(content)
		
		logo = QtWidgets.QLabel()
		logo.setPixmap(QtGui.QPixmap(os.path.join(os.path.dirname(arch14cz_backend.__file__), "res/cm_logo.svg")))
		path_third = os.path.join(os.path.dirname(arch14cz_backend.__file__), "THIRDPARTY.TXT").replace("\\", "/")
		label = QtWidgets.QLabel('''
<h2>Arch<span style="color:red">14C</span>Z - backend</h2>
<h4>Backend interface for the database of archaeological radiocarbon dates of the Czech Republic</h4>
<p>Version %s (%s)</p>
<p>Copyright © <a href="mailto:peter.demjan@gmail.com">Peter Demján</a> 2022 - %s</p>
<p>&nbsp;</p>
<p>This application uses the Graph-based data storage <a href="https://github.com/demjanp/deposit">Deposit</a></p>
<p>&nbsp;</p>
<p>Licensed under the <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">GNU General Public License</a></p>
<p><a href="https://github.com/demjanp/arch14cz_backend">Home page</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="%s">Third party libraries</a></p>
		''' % (__version__, __date__, __date__.split(".")[-1], path_third))
		label.setOpenExternalLinks(True)
		content.layout().addWidget(logo)
		content.layout().addWidget(label)
