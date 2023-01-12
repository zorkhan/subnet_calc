#! /usr/bin/python3

import sys
import os
import re
import datetime
import configparser
import ipaddress
from PyQt5.QtWidgets import ( QMainWindow, QApplication, QComboBox,
        QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QScrollBar, QTableWidget, QTabWidget, QTextEdit, QVBoxLayout, 
        QWidget, QTableWidgetItem, QPlainTextEdit, QFrame, QMessageBox,
        QAction, QHeaderView, QTreeView, QTableView, QAbstractItemView)
from PyQt5.QtGui import QIcon, QPixmap, QRegExpValidator, QStandardItemModel, QStandardItem, QFont, QFontInfo
from PyQt5.QtCore import QRegExp, QItemSelectionModel, QFile, QTextStream
from PyQt5 import QtCore

appPath = os.path.dirname(os.path.abspath(__file__))
iniFile = appPath+'/st.ini'
pngFile = appPath+'/st.png'
qssDark = appPath+'/st-dark.qss'
qssLite = appPath+'/st-light.qss'

gDebug = False
darkMode = True
themeName = 'dark'

defaultIPv4Addresses = [
    '1.0.0.1',
    '128.0.0.1',
    '192.0.0.1',
    '224.0.0.1',
    '240.0.0.1',
    '0.0.0.0',
    '0.0.0.1',
    '127.0.0.1',
    '255.255.255.255'
]

defaultIPv6Addresses = {
    '::/128'                       : 'Unspecified',
    '::1/128'                      : 'Loopback',
    'FE80:1::/10'                  : 'Link-Local',
    'FE80::102:304/96'             : '  6over4',
    'FE80::5EFE:102:304'           : '  ISATAP',
    'FEC0::'                       : 'Site-Local',
    '::/3'                         : 'Unformatted',
    '::/96'                        : '  IP4-Compatible',
    '::FFFF:0102:0304'             : '  IP4-Mapped',
    '2000::/3'                     : 'IANA Delegated',
    '2001::/32'                    : '  Teredo Tunneling',
    '2002::/16'                    : '  6to4',
    'FF00::/8'                     : 'Multicast',
    'FF01::/16'                    : '  Interface-Local',
    'FF01::1/128'                  : '    All Nodes',
    'FF01::2/128'                  : '    All Routers',
    'FF02::/16'                    : '  Link-Local',
    'FF02::1/128'                  : '    All Nodes',
    'FF02::2/128'                  : '    All Routers',
    'FF04::/16'                    : '  Admin-Local',
    'FF05::/16'                    : '  Site-Local',
    'FF05::2/128'                  : '    All Routers',
    'FF08::/16'                    : 'Organization-Local',
    'FF0E::/16'                    : 'Global'
}

#set a constant with index in the list of colors
H_COLOR, N_COLOR, S_COLOR, G_COLOR, X_COLOR, C_COLOR = range(6)
#              host      net       sub       group     open      cidr
themes = {
     'dark': ['ff70e2', '00f0f0', 'ffff00', 'ff00ff', 'fffe00', '00f0f0'],
     'lite': ['8802b5', '008080', '990900', '800080', '888888', '008080']
     }
     
class App(QMainWindow):

    def __init__(self):
        super().__init__()
        
        global darkMode, themeName

        self.title = 'Subnet Transmogrifier'

        self.setWindowTitle(self.title)
        self.setWindowIcon(QIcon('st-icon.png'))

        top,left,width,height,tab,darkMode = getSettings()
        debug (top,left,width,height)
        self.setGeometry(left, top, width, height)

        if darkMode:
            themeName='dark'
        else:
            themeName='lite' 


        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # add graphic and program name

        layout = QVBoxLayout(self.central_widget)

        self.titleFrame = QFrame()
        self.titleFrame.setStyleSheet('QFrame {background-color: #011423;}') #match the background to the image
        self.titleLayout = QHBoxLayout(self.titleFrame)
        self.titleLayout.setContentsMargins(10,0,10,0) #top, left, right, bottom
        self.titleLayout.setSpacing(0)

        # Title picture widget
        pixmap = QPixmap(pngFile)
        self.pixmap = pixmap
        self.image = QLabel()
        self.image.setAlignment(QtCore.Qt.AlignCenter)
        self.image.setPixmap(self.pixmap)
        self.image.setMinimumWidth(600)
        self.titleLayout.addWidget(self.image)

        # Title text widgets
        self.leftTitle1 = QLabel('Subnet', self.image)
        self.leftTitle1.setStyleSheet("""
            color: yellow;
            padding: 10px 00px;
            background-color: none;
            font-family: segoe print;
            font-size: 16pt;
            font-weight: bold;
            line-height: 1;
        """)
        self.leftTitle2 = QLabel('Transmogrifier', self.image)
        self.leftTitle2.setStyleSheet("""
            color: yellow;
            padding: 32px 20px;
            background-color: none;
            font-family: segoe print;
            font-size: 16pt;
            font-weight: bold;
            line-height: 1;
        """)

        self.rightTitle = QLabel('Next Generation IPv4/v6 Subnet Calculator', self.image)
        self.rightTitle.setStyleSheet("""
            color: yellow;
            background-color: none;
            font-family: segoe print;
            font-size: 11pt;
        """)
        # position this one at the bottom right of the pixmap
        self.rightTitle.setAlignment( QtCore.Qt.AlignRight )

        layout.addWidget(self.titleFrame)

        self.rightTitle.setFixedWidth(self.titleFrame.geometry().width()-20)
        self.rightTitle.move(0,pixmap.height()-self.rightTitle.geometry().height())


        self.tabWidget = MyTabWidget(self)
        layout.addWidget(self.tabWidget)
        self.tabWidget.tabs.setCurrentIndex(tab)

        #menu
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        #editMenu = mainMenu.addMenu('Edit')
        #viewMenu = mainMenu.addMenu('View')
        #searchMenu = mainMenu.addMenu('Search')
        optionsMenu = mainMenu.addMenu('Options')
        helpMenu = mainMenu.addMenu('Help')

        exitButton = QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        darkModeAction = QAction('Dark Mode',self, checkable=True, checked=darkMode==True)
        darkModeAction.setStatusTip('Dark Mode')
        darkModeAction.triggered.connect(self.toggleDarkMode)
        optionsMenu.addAction(darkModeAction)
        
        aboutButton = QAction('About', self)
        aboutButton.setShortcut('Ctrl+H')
        aboutButton.setStatusTip('About application')
        aboutButton.triggered.connect(self.doAbout)
        helpMenu.addAction(aboutButton)

        if darkMode:
            self.toggleStyleSheet(qssDark)
        else:
            self.toggleStyleSheet(qssLite)
        

        self.show()
        
        # resize after window has been rendered
        self.rightTitle.setFixedWidth(self.titleFrame.geometry().width()-20)

    def toggleStyleSheet(self, path):
        
        # get the QApplication instance,  or crash if not set
        app = QApplication.instance()
        if app is None:
            raise RuntimeError('No Qt Application found.')

        file = QFile(path)
        file.open(QFile.ReadOnly | QFile.Text)
        stream = QTextStream(file)
        app.setStyleSheet(stream.readAll())
        
        #find all the multi-color labels and update with the appropriate dark/light color
        for child in self.central_widget.children():
            for w in child.children():
                if isinstance(w, QTabWidget):
                    for label in w.findChildren(QLabel,'multiColor'):
                        old = label.text()
                        if darkMode:
                            for color in range(len(themes['dark'])):
                                old = re.sub(themes['lite'][color], themes['dark'][color], old)
                        else:
                            for color in range(len(themes['dark'])):
                                old = re.sub(themes['dark'][color], themes['lite'][color], old)
                        label.setText(old)
                        
                    for label in w.findChildren(QTextEdit,'multiColor'):
                        old = label.toHtml()
                        if darkMode:
                            for color in range(len(themes['dark'])):
                                old = re.sub(themes['lite'][color], themes['dark'][color], old)
                        else:
                            for color in range(len(themes['dark'])):
                                old = re.sub(themes['dark'][color], themes['lite'][color], old)
                        label.clear()
                        label.setText(old)
                        
    def toggleDarkMode(self,state):
        debug ('toggleDarkMode',state)
        
        global darkMode, themeName
        
        if state:
            darkMode = True
            themeName='dark'
            self.toggleStyleSheet(qssDark)
            
        else:
            darkMode = False
            themeName='lite'
            self.toggleStyleSheet(qssLite)
        
    def doAbout(self):
        debug ('about')
        now = datetime.datetime.now()
        aboutText = '''
<b>Subnet Transmogrifier</b> - An IPv4/v6 subnet calculator.<br>
<br>
Copyright &copy; #YEAR#, Craig Schaeffer<br>
<br>
Version v#VERSION#<br>
<br>
LICENSE:<br>
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.<br><br>
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.<br><br>
You should have received a copy of the GNU General Public License along with this program.  If not, see <a href="http://www.gnu.org/licenses/"><font color="#COLOR#">http://www.gnu.org/licenses/</font></a>.
'''
        aboutText = re.sub('#VERSION#','1.0.2019.1016',aboutText)
        aboutText = re.sub('#YEAR#',str(now.year),aboutText)
        if darkMode:
            aboutText = re.sub('#COLOR#','#00BCD4',aboutText)
        else:
            aboutText = re.sub('#COLOR#','#0000EE',aboutText)
        about = QMessageBox()
        about.setIcon(QMessageBox.Information)
        about.setText(aboutText)
        about.setWindowTitle('Subnet Transmogrifier')
        about.setStandardButtons(QMessageBox.Ok)
        about.exec_()

    def resizeEvent(self, event):
        #g=self.titleFrame.geometry()
        #print (g.top(), g.left(), g.width(), g.height())
        try:
            self.rightTitle.setFixedWidth(self.titleFrame.geometry().width()-20)

        except:
            pass

    def closeEvent(self, event):
        debug ('close event')
        g=self.geometry()
        debug (g.top(), g.left(), g.width(), g.height())
        saveSettings( g.top(), g.left(), g.width(), g.height(), self.tabWidget.tabs.currentIndex(), darkMode )


class MyConversionsTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        debug ('\ninit conversions')

        # dotted decimal
        self.ddLabel = QLabel('Dotted Decimal')
        self.ddComboBox = QComboBox()
        self.ddComboBox.setEditable(True)
        self.ddComboBox.addItems(defaultIPv4Addresses)
        self.ddComboBox.currentTextChanged.connect(self._ddChanged)

        self.conversionValue = IP2Int(self.ddComboBox.currentText())

        # decimal
        self.decLabel = QLabel('Decimal')

        self.decLineEdit = QLineEdit()
        reg_ex = QRegExp(r'\d{1,10}')
        input_validator = QRegExpValidator(reg_ex, self.decLineEdit)
        self.decLineEdit.setValidator(input_validator)
        #self.decLineEdit.setMaximumHeight(24)
        self.decLineEdit.setProperty('ValueOk', True)
        self.decLineEdit.textEdited.connect(self._decChanged)

        # dotted hexadecimal
        self.dhexLabel = QLabel('Dotted Hexadecimal')
        self.dhexLineEdit = QLineEdit()
        self.dhexLineEdit.setInputMask(r'HH\.HH\.HH\.HH')
        #self.dhexLineEdit.setValidator( QRegExpValidator( QRegExp('^(([a-fA-F0-9]{2})\.){3}[a-fA-F0-9]{2}$'), self.decLineEdit) )
        self.dhexLineEdit.setMaximumHeight(24)
        self.dhexLineEdit.setProperty('ValueOk', True)
        self.dhexLineEdit.textEdited.connect(self._dhexChanged)

        # hexadecimal
        self.hexLabel = QLabel('Hexadecimal')
        self.hexLineEdit = QLineEdit()
        self.hexLineEdit.setValidator( QRegExpValidator( QRegExp('0x[a-fA-F0-9]{1,8}$'), self.hexLineEdit) )
        self.hexLineEdit.setMaximumHeight(24)
        self.hexLineEdit.setProperty('ValueOk', True)
        self.hexLineEdit.textEdited.connect(self._hexChanged)

        # dotted binary
        self.dbinLabel = QLabel('Dotted Binary')
        self.dbinLineEdit = QLineEdit()
        self.dbinLineEdit.setValidator( QRegExpValidator( QRegExp(r'^(([01]{8})\.){3}[01]{8}$'), self.dbinLineEdit) )
        self.dbinLineEdit.setMaximumHeight(24)
        self.dbinLineEdit.setProperty('ValueOk', True)
        self.dbinLineEdit.textEdited.connect(self._dbinChanged)

        # binary
        self.binLabel = QLabel('Binary')
        self.binLineEdit = QLineEdit()
        self.binLineEdit.setValidator( QRegExpValidator( QRegExp(r'^[01]{32}$'), self.binLineEdit) )
        self.binLineEdit.setMaximumHeight(24)
        self.binLineEdit.setProperty('ValueOk', True)
        self.binLineEdit.textEdited.connect(self._binChanged)

        # filler - force all the widgets above to the top
        self.fillerLabel = QLabel('')

        # grid
        convGrid = QGridLayout()
        convGrid.setVerticalSpacing(2)
        convGrid.addWidget(self.ddLabel   , 0,0)       #row, col[, rowspan, colspan]
        convGrid.addWidget(self.ddComboBox, 1,0)
        convGrid.addWidget(self.decLabel,   0,1)
        convGrid.addWidget(self.decLineEdit,1,1)

        convGrid.addWidget(self.dhexLabel,   2,0)
        convGrid.addWidget(self.dhexLineEdit,3,0)
        convGrid.addWidget(self.hexLabel,    2,1)
        convGrid.addWidget(self.hexLineEdit, 3,1)

        convGrid.addWidget(self.dbinLabel,   4,0)
        convGrid.addWidget(self.dbinLineEdit,5,0,1,2)

        convGrid.addWidget(self.binLabel,   6,0)
        convGrid.addWidget(self.binLineEdit,7,0,1,2)

        convGrid.addWidget(self.fillerLabel,8,0)
        convGrid.setRowStretch(8, 1)

        self.setLayout(convGrid)

        self._updateAll('')


    def _ddChanged(self):
        debug ('ddChanged')

        if (ipValid(self.ddComboBox.currentText())):

            self.ddComboBox.setProperty('ValueOk', True)
            self.conversionValue = IP2Int(self.ddComboBox.currentText())
            self._updateAll('dd')
        else:
            self.ddComboBox.setProperty('ValueOk', False)
            self.conversionValue = 0
            self.decLineEdit.clear()
            self.binLineEdit.clear()
            self.decLineEdit.clear()
            self.dhexLineEdit.clear()
            self.dbinLineEdit.clear()
            self.hexLineEdit.clear()

        self.ddComboBox.setStyle(self.ddComboBox.style())

    def _decChanged(self):
        debug ('_decChanged')
        if (self.decLineEdit.hasAcceptableInput() ):
            val = int(self.decLineEdit.text())
            if (val <= 2**32):
                self.decLineEdit.setProperty('ValueOk', True)
                self.conversionValue = val
                self._updateAll('dec')
            else:
                self.decLineEdit.setProperty('ValueOk', False)
        else:
            self.conversionValue = 0
            self.decLineEdit.setProperty('ValueOk', False)
            
        self.decLineEdit.setStyle(self.decLineEdit.style())

    def _dhexChanged(self):
        debug ('_dhexChanged')
        
        if (self.dhexLineEdit.hasAcceptableInput() ):
            self.dhexLineEdit.setProperty('ValueOk', True)
            # strip the '.' and convert the hex to dec
            self.conversionValue = int(re.sub(r'\.', '', self.dhexLineEdit.text()), 16)
            self._updateAll('dhex')
        else:
            self.dhexLineEdit.setProperty('ValueOk', False)
            
        self.dhexLineEdit.setStyle(self.dhexLineEdit.style())

    def _hexChanged(self):
        debug ('_hexChanged')

        if (self.hexLineEdit.hasAcceptableInput() ):
            self.hexLineEdit.setProperty('ValueOk', True)
            self.conversionValue = int(self.hexLineEdit.text(), 16)
            self._updateAll('hex')
        else:
            self.hexLineEdit.setProperty('ValueOk', False)
            
        self.binLineEdit.setStyle(self.binLineEdit.style())

    def _dbinChanged(self):
        debug ('_dbinChanged')

        if (self.dbinLineEdit.hasAcceptableInput() ):
            self.dbinLineEdit.setProperty('ValueOk', True)
            # strip the '.' and convert the bin to dec
            self.conversionValue = int(re.sub(r'\.', '', self.dbinLineEdit.text()), 2)
            self._updateAll('dbin')
        else:
            self.dbinLineEdit.setProperty('ValueOk', False)
            
        self.dbinLineEdit.setStyle(self.dbinLineEdit.style())

    def _binChanged(self):
        debug ('_binChanged')

        if (self.binLineEdit.hasAcceptableInput() ):
            self.binLineEdit.setProperty('ValueOk', True)
            self.conversionValue = int(self.binLineEdit.text(), 2)
            self._updateAll('bin')
        else:
            self.binLineEdit.setProperty('ValueOk', False)
            
        self.binLineEdit.setStyle(self.binLineEdit.style())

    # update all the boxes, except the one that caused the change
    def _updateAll(self,whatTriggered):

        if whatTriggered != 'dd':   self.ddComboBox.setCurrentText( Int2IP(self.conversionValue) ) 

        if whatTriggered != 'dec':  self.decLineEdit.setText( str(self.conversionValue) ) 
        if whatTriggered != 'dhex': self.dhexLineEdit.setText( Int2HexIP(self.conversionValue) )
        if whatTriggered != 'hex':  self.hexLineEdit.setText( hex(self.conversionValue) ) 

        bin = '{:032b}'.format(self.conversionValue)
        if whatTriggered != 'bin':  self.binLineEdit.setText( bin ) 

        bin = re.sub('(.{8})(?!$)', r'\1.', bin) #insert a '.' every 8 chars
        if whatTriggered != 'dbin': self.dbinLineEdit.setText( bin ) 


class MyClassesTab(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        debug ('\ninit classes')
        

        # address
        self.addrLabel = QLabel('Address')

        self.addrComboBox = QComboBox()
        self.addrComboBox.setEditable(True)
        self.addrComboBox.addItems(defaultIPv4Addresses)

        self.addrComboBox.currentTextChanged.connect(self._addrChanged)

        # global addr object
        self.addr = ipaddress.IPv4Address(self.addrComboBox.currentText())

        # subnet mask
        self.classLabel = QLabel('Class')
        self.classComboBox = QComboBox()
        self.classComboBox.addItems([
            'Class A',
            'Class B',
            'Class C',
            'Class D/Multicast',
            'Class E/Experimental',
            '"This" host',
            '"This" network',
            'Loopback',
            'Broadcast',
        ])
        self.classComboBox.activated.connect(self._classChanged)

        # address block range
        self.addrblockLabel = QLabel('Class Address Range')
        self.addrblockLabel2 = QLabel()
        self.addrblockLabel2.setAlignment( QtCore.Qt.AlignRight )

        self.addrblockLineEdit = QLineEdit()
        self.addrblockLineEdit.setReadOnly(True)
        #self.addrblockLineEdit.setMaximumHeight(24)

        # class bit usage
        self.classbitLabel = QLabel('Class Bit Usage')
        self.classbitLabel.setObjectName('multiColor')
        
        self.classbitTextEdit = QTextEdit()
        self.classbitTextEdit.setObjectName('multiColor')
        self.classbitTextEdit.setReadOnly(True)
        self.classbitTextEdit.setMaximumHeight(22)
        self.classbitTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.diagramGroup = QGroupBox('')
        self.diagramLayout = QGridLayout()
        self.diagramLayout.setSpacing(0)
        self.diagramGroup.setLayout(self.diagramLayout)

        # filler - force all the widgets above to the top
        self.fillerLabel = QLabel('')


        #add all the widgets to the grid
        classesGrid = QGridLayout()
        classesGrid.addWidget(self.addrLabel,    0,0)       #row, col[, rowspan, colspan]
        classesGrid.addWidget(self.addrComboBox, 1,0)
        classesGrid.addWidget(self.classLabel,   0,1)
        classesGrid.addWidget(self.classComboBox,1,1)

        classesGrid.addWidget(self.addrblockLabel,   2,0)
        classesGrid.addWidget(self.addrblockLabel2,  2,1)
        classesGrid.addWidget(self.addrblockLineEdit,3,0,1,2)

        classesGrid.addWidget(self.classbitLabel,   4,0,1,2)
        classesGrid.addWidget(self.classbitTextEdit,5,0,1,2)

        classesGrid.addWidget(self.diagramGroup,6,0,1,2)    #help diagrams

        classesGrid.addWidget(self.fillerLabel,9,0)
        classesGrid.setRowStretch(9,1)

        self.setLayout(classesGrid)

        self._showClassDiagram()
        self._addrChanged()

    def _addrChanged(self):
        debug ('_addrChanged', self.addrComboBox.currentText())

        if (ipValid(self.addrComboBox.currentText())):

            c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address
            self.addr = ipaddress.IPv4Address(self.addrComboBox.currentText())
            labelText = 'Class Bit Usage'
            html = ''
            range=''
            if (int(self.addr)==0):         #this host
                self.classComboBox.setCurrentIndex(5)
                html = '{}'.format('0'*32)
                range = '0.0.0.0'

            elif (int(self.addr)==1):       #this network
                self.classComboBox.setCurrentIndex(6)
                labelText += f' (<font color=#{themes[themeName][X_COLOR]}>x=Open</font>)'
                html = '{}{}'.format('0'*8, 'x'*24)
                range = '0.0.0.1 - 0.255.255.255'

            elif (int(self.addr)==2**32-1): #broadcast
                self.classComboBox.setCurrentIndex(8)
                html = '{}'.format('1'*32)
                range = '255.255.255.255'

            elif (self.addr.is_loopback):
                self.classComboBox.setCurrentIndex(7)
                labelText += f' (<font color="#{themes[themeName][X_COLOR]}">x=Open</font>)'
                html = '{}{}'.format('01111111', 'x'*24)
                range = '127.0.0.0 - 127.255.255.255'

            elif (self.addr.is_multicast):
                self.classComboBox.setCurrentIndex(3)
                labelText += f' (<font color="#{themes[themeName][G_COLOR]}">g=Group</font>)'
                html = '{}{}'.format('1110', 'g'*28)
                range = '224.0.0.0 - 239.255.255.255'

            elif (int(self.addr) & 0xF0000000 == 0xF0000000):   # class E
                self.classComboBox.setCurrentIndex(4)
                labelText += f' (<font color="#{themes[themeName][X_COLOR]}">x=Open</font>)'
                html = '{}{}'.format('1111', 'x'*28)
                range = '240.0.0.0 - 255.255.255.254'

            elif (n==8):
                self.classComboBox.setCurrentIndex(0)
                labelText += f' (<font color="#{themes[themeName][N_COLOR]}">n=Network</font>;'
                labelText += f' <font color="#{themes[themeName][H_COLOR]}">h=Host</font>)'
                html = '0{}{}'.format('n'*7, 'h'*24)
                range = '1.0.0.0 - 126.255.255.255'

            elif(n==16):
                self.classComboBox.setCurrentIndex(1)
                labelText += f' (<font color="#{themes[themeName][N_COLOR]}">n=Network</font>;'
                labelText += f' <font color="#{themes[themeName][H_COLOR]}">h=Host</font>)'
                html = '10{}{}'.format('n'*14, 'h'*16)
                range = '128.0.0.0 - 191.255.255.255'

            elif(n==24):
                self.classComboBox.setCurrentIndex(2)
                labelText += f' (<font color="#{themes[themeName][N_COLOR]}">n=Network</font>;'
                labelText += f' <font color="#{themes[themeName][H_COLOR]}">h=Host</font>)'
                html = '110{}{}'.format('n'*21, 'h'*8)
                range = '192.0.0.0 - 223.255.255.255'

            if (self.addr.is_private):
                debug('is private')
                self.addrblockLabel2.setText('[Private]')
            else:
                self.addrblockLabel2.setText('')

            self.classbitLabel.setText(labelText)
            self.classbitLabel.setObjectName('multiColor')

            html = re.sub('(.{8})(?!$)', r'\1.', html) #insert a '.' every 8 chars
            html = re.sub('(n+)', r'<font color="#{}">\1</font>'.format(themes[themeName][N_COLOR]), html) #color n teal
            html = re.sub('(x+)', r'<font color="#{}">\1</font>'.format(themes[themeName][X_COLOR]), html) #color x gray
            html = re.sub('(g+)', r'<font color="#{}">\1</font>'.format(themes[themeName][G_COLOR]), html) #color g magenta
            html = re.sub('(h+)', r'<font color="#{}">\1</font>'.format(themes[themeName][H_COLOR]), html) #color h green
            html = re.sub('(s+)', r'<font color="#{}">\1</font>'.format(themes[themeName][S_COLOR]), html) #color s red

            self.classbitTextEdit.clear()
            #self.classbitTextEdit.appendHtml(html)
            self.classbitTextEdit.setText(html)

            self.addrblockLineEdit.setText(range)
        else:
            debug ('clear all')
            self.classComboBox.setCurrentIndex(99)
            self.classbitTextEdit.clear()
            self.addrblockLineEdit.clear()

    def _classChanged(self):
        debug('_classChanged', self.classComboBox.currentIndex(), self.classComboBox.currentText())
        self.addrComboBox.setCurrentIndex(self.classComboBox.currentIndex())

    def _drawClassFormat(self,widths,details):

        gb = QGroupBox('')
        gb.setStyleSheet('QGroupBox {border-style: none;}')
        gl = QGridLayout()
        gl.setSpacing(0)
        gb.setLayout(gl)

        
        # address format shaded box
        for c in range(len(widths)):
            # #need a frame around these
            frame = QFrame()
            f = QFont()
            if (widths[c] == 1):
                bgcolor = '#00c0c0'
                f = getMonospaceFont()
            elif (details[c][0] == 'H'):
                bgcolor = '#e0e0ff'
            else:
                bgcolor = '#e0ffff'
            frame.setStyleSheet(f'border: 1px solid black; background-color: {bgcolor}; min-height: 30px;')
            gl.setColumnStretch(c,widths[c])
            frame.setFrameShape(QFrame.Box)   #Box, Panel, StyledPanel, WinPanel
            frame.setFrameShadow(QFrame.Plain)
            gl.addWidget(frame,0,c)

            label = QLabel(details[c])
            label.setStyleSheet('QLabel {color: black; background-color: transparent;}')
            label.setFont(f)
            gl.addWidget(label, 0, c, QtCore.Qt.AlignCenter)

        return gb

    def _showClassDiagram(self):
        debug ('updateAddressFormat')

        list = ['Class','First Octet Range','Max Hosts','Format']
        for c in range(len(list)):
            label = QLabel(list[c])
            label.setStyleSheet('QLabel {font-weight: bold}')
            self.diagramLayout.addWidget(label,0,c,QtCore.Qt.AlignCenter)

        list = ['A','1-126','16M']
        for c in range(len(list)):
            label = QLabel(list[c])
            self.diagramLayout.addWidget(label,1,c,QtCore.Qt.AlignCenter)
        gb = self._drawClassFormat([1,7,24],['0','Network ID\n(bits 2 to 8)','Host ID\n(24 bits)'])
        self.diagramLayout.addWidget(gb,1,3)

        list = ['B','128-191','64K']
        for c in range(len(list)):
            label = QLabel(list[c])
            self.diagramLayout.addWidget(label,2,c,QtCore.Qt.AlignCenter)
        gb = self._drawClassFormat([1,1,14,16],['1','0','Network ID\n(bits 3 to 16)','Host ID\n(16 bits)'])
        self.diagramLayout.addWidget(gb,2,3)

        list = ['C','192-223','254']
        for c in range(len(list)):
            label = QLabel(list[c])
            self.diagramLayout.addWidget(label,3,c,QtCore.Qt.AlignCenter)
        gb = self._drawClassFormat([1,1,1,21,8],['1','1','0','Network ID\n(bits 4 to 24)','Host ID\n(8 bits)'])
        self.diagramLayout.addWidget(gb,3,3)

        list = ['D','224-239','N/A']
        for c in range(len(list)):
            label = QLabel(list[c])
            self.diagramLayout.addWidget(label,4,c,QtCore.Qt.AlignCenter)
        gb = self._drawClassFormat([1,1,1,1,28],['1','1','1','0','Multicast Group Address\n(28 bits)'])
        self.diagramLayout.addWidget(gb,4,3)

        list = ['E','240-255','N/A']
        for c in range(len(list)):
            label = QLabel(list[c])
            self.diagramLayout.addWidget(label,5,c,QtCore.Qt.AlignCenter)
        gb = self._drawClassFormat([1,1,1,1,28],['1','1','1','1','Experimental Address ID\n(bits 5 to 32)'])
        self.diagramLayout.addWidget(gb,5,3)


class MySubnetsTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        debug ('\ninit subnets')

        # address
        self.addrComboBox = QComboBox()
        self.addrComboBox.setEditable(True)
        self.addrComboBox.addItems(defaultIPv4Addresses)
        self.addrLabel = QLabel('Address')
        self.addrComboBox.currentTextChanged.connect(self._addrChanged)

        # subnet mask
        self.maskLabel = QLabel('Subnet Mask')
        self.maskComboBox = QComboBox()

        c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address

        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), str(n)), strict=False)

        for x in range(2, h+1):
            # debug (ipaddress.ip_address(2**32-2**x))
            self.maskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**x), 32-x))
        self.maskComboBox.setCurrentIndex(self.maskComboBox.count()-1)
        self.maskComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.maskComboBox.activated.connect(self._maskChanged)

        # subnet bits, max subnets, host bits, max hosts
        self.subnetbitsLabel = QLabel('Subnet Bits')
        self.subnetbitsComboBox = QComboBox()
        for x in range(0, 24+1):                          # 0 .. number of network bits
            self.subnetbitsComboBox.addItem(str(x))
        self.subnetbitsComboBox.activated.connect(self._subnetbitsChanged)

        self.maxsubnetLabel = QLabel('Max Subnets')
        self.maxsubnetsComboBox = QComboBox()
        self.maxsubnetsComboBox.activated.connect(self._maxsubnetsChanged)

        self.hostbitsLabel = QLabel('Host Bits')
        self.hostbitsComboBox = QComboBox()
        self.hostbitsComboBox.activated.connect(self._hostbitsChanged)

        self.maxhosttLabel = QLabel('Max Hosts')
        self.maxhostsComboBox = QComboBox()
        self.maxhostsComboBox.activated.connect(self._maxhostsChanged)

        # network bit usage label
        labelText  = f'<font color="#{themes[themeName][N_COLOR]}">n=Network</font>; '
        labelText += f'<font color="#{themes[themeName][S_COLOR]}">s=Subnet</font>; '
        labelText += f'<font color="#{themes[themeName][H_COLOR]}">h=Host</font>'
        labelText += ')'

        self.netUsageLabel = QLabel('Network Bit Usage (' + labelText)
        self.netUsageLabel.setObjectName('multiColor')
        self.descrLabel = QLabel('[]')
        self.descrLabel.setAlignment( QtCore.Qt.AlignRight )

        self.netUsageTextEdit = QTextEdit()
        self.netUsageTextEdit.setObjectName('multiColor')
        self.netUsageTextEdit.setReadOnly(True)
        self.netUsageTextEdit.setMaximumHeight(22)
        self.netUsageTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # subnet bit usage label
        self.subnetUsageLabel = QLabel('Subnet Bit Usage (' + labelText)
        self.subnetUsageLabel.setObjectName('multiColor')

        self.subnetUsageTextEdit = QTextEdit()
        self.subnetUsageTextEdit.setObjectName('multiColor')
        self.subnetUsageTextEdit.setReadOnly(True)
        self.subnetUsageTextEdit.setMaximumHeight(22)
        self.subnetUsageTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        #results table
        self.resultsTable = QTableWidget(1, 4)
        self.resultsTable.setHorizontalHeaderLabels(('Subnet', 'Mask', 'Host Range', 'Broadcast'))
        self.resultsTable.horizontalHeader().setStyleSheet('::section {font-weight: bold; padding: 1px}')
        self.resultsTable.verticalHeader().setStyleSheet('::section { padding: 0px 1px;}')
        self.resultsTable.setAlternatingRowColors(True)
        self.resultsTable.setCornerButtonEnabled(False)

        #add all the widgets to the grid
        subnetsGrid = QGridLayout()
        subnetsGrid.addWidget(self.addrLabel,0,0,1,2)       #row, col[, rowspan, colspan]
        subnetsGrid.addWidget(self.addrComboBox,1,0,1,2)
        subnetsGrid.addWidget(self.maskLabel,0,2,1,2)
        subnetsGrid.addWidget(self.maskComboBox,1,2,1,2)

        subnetsGrid.addWidget(self.netUsageLabel,2,0,1,3)
        subnetsGrid.addWidget(self.descrLabel,2,3)
        subnetsGrid.addWidget(self.netUsageTextEdit,3,0,1,4)

        subnetsGrid.addWidget(self.subnetbitsLabel,4,0)
        subnetsGrid.addWidget(self.subnetbitsComboBox,5,0)
        subnetsGrid.addWidget(self.maxsubnetLabel,4,1)
        subnetsGrid.addWidget(self.maxsubnetsComboBox,5,1)

        subnetsGrid.addWidget(self.hostbitsLabel,4,2)
        subnetsGrid.addWidget(self.hostbitsComboBox,5,2)
        subnetsGrid.addWidget(self.maxhosttLabel,4,3)
        subnetsGrid.addWidget(self.maxhostsComboBox,5,3)

        subnetsGrid.addWidget(self.subnetUsageLabel,6,0,1,4)
        subnetsGrid.addWidget(self.subnetUsageTextEdit,7,0,1,4)

        subnetsGrid.addWidget(self.resultsTable,8,0,1,4)


        self.setLayout(subnetsGrid)

        self._updatePulldowns('subnetMask')
        self._updateAll()

    def _clearTable(self, rows):
        self.resultsTable.setRowCount(rows)

    def _updateTable(self):
        debug ('_updateTable')
        mask = 30 - self.maskComboBox.currentIndex()
        net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), str(mask)), strict=False)
        debug ('maxsubnets:', self.maxsubnetsComboBox.currentText())
        rows = int(self.maxsubnetsComboBox.currentText())
        subnetbits = int(self.subnetbitsComboBox.currentText())

        newprefix = mask + subnetbits

        r = 0
        tableList = list(net.subnets(new_prefix=newprefix))
        tableLen = len(tableList)

        if (tableLen > 1024):
            buttonReply = QMessageBox.question(self, 'Large Table', 'The subnet table has '+str(tableLen)+' entries\n Continue?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                self.resultsTable.setRowCount(0)
                return
            else:
                debug('No clicked.')

        self._clearTable(rows)

        for n in tableList:
            self.resultsTable.setRowHeight(r, 18)

            self.resultsTable.setItem(r, 0, QTableWidgetItem(str(n.network_address)))
            self.resultsTable.setItem(r, 1, QTableWidgetItem(str(n.netmask)+' (/'+str(n.prefixlen)+')'))
            if (newprefix == 32):
                self.resultsTable.setItem(r, 2, QTableWidgetItem(str(n)))
                self.resultsTable.setItem(r, 3, QTableWidgetItem('N/A'))
            else:
                self.resultsTable.setItem(r, 2, QTableWidgetItem(str(n[1])+' - '+str(n[-2])))
                self.resultsTable.setItem(r, 3, QTableWidgetItem(str(n.broadcast_address)))

            #center the text
            for c in range(4):
                self.resultsTable.item(r,c).setTextAlignment(QtCore.Qt.AlignCenter)

            r += 1

        self.resultsTable.resizeColumnsToContents()


    def _updateUsage(self):
        debug ('_updateUsage')

        self.netUsageTextEdit.clear()
        bIP = '{:032b}'.format(int(ipaddress.IPv4Address(self.addrComboBox.currentText())))
        #debug ('bIP' , bIP )
        if (bIP[:1] == '0'):
            net_class='Class A'
            html_bits = '0'
            netBits=8
        elif (bIP[:2] == '10'):
            net_class='Class B'
            html_bits = '10'
            netBits=16
        elif (bIP[:3] == '110'):
            net_class='Class C'
            html_bits = '110'
            netBits=24
        elif (bIP[:4] == '1110'):
            net_class='Class D - Multicast'
            html_bits = '1110'
            netBits=24
        elif (bIP[:4] == '1111'):
            net_class='Class E - Experimental'
            html_bits = '1111'
            netBits=24
        else:
            debug('Class other')

        classBits = len(html_bits)


        self.addr = ipaddress.IPv4Address(self.addrComboBox.currentText())

        if (self.addr.is_private and int(self.addr)>1 and int(self.addr)<2**32-1 and not self.addr.is_loopback and not self.addr.is_multicast): #ignore this host and this network
            debug('is private')
            net_class += ' - Private'

        #subnetBits = ipaddress.ip_network(self.maskComboBox.currentText()).prefixlen
        subnetBits = 30 - self.maskComboBox.currentIndex()

        delta = subnetBits - netBits
        if ( delta <= 0): # steal bits from class
            netBits = netBits + delta

        subnetBits = abs(delta)
        hostBits = 32-subnetBits-netBits

        netBits = netBits - len(html_bits)

        debug ( f'bits {classBits} net {netBits} subnet {subnetBits} host {hostBits}' )

        html = '{}{}{}{}'.format(html_bits, 'n'*netBits, 's'*subnetBits, 'h'*hostBits)
        html = re.sub('(.{8})(?!$)', r'\1.', html) #insert a '.' every 8 chars
        #color the pieces
        html = re.sub('(n+)', r'<font color="#{}">\1</font>'.format(themes[themeName][N_COLOR]), html) #color n teal
        html = re.sub('(s+)', r'<font color="#{}">\1</font>'.format(themes[themeName][S_COLOR]), html) #color s red
        html = re.sub('(h+)', r'<font color="#{}">\1</font>'.format(themes[themeName][H_COLOR]), html) #color h green

        self.descrLabel.setText('['+net_class+']')


        self.netUsageTextEdit.clear()
        self.netUsageTextEdit.setText(html)


    def _updateSubNetUsage(self):
        debug ('_updateSubNetUsage')
        self.subnetUsageTextEdit.clear()

        bIP = '{:032b}'.format(int(ipaddress.IPv4Address(self.addrComboBox.currentText())))

        if (bIP[:1] == '0'):        #Class A
            html_bits = '0'
            netBits=8
        elif (bIP[:2] == '10'):     #Class B
            html_bits = '10'
            netBits=16
        elif (bIP[:3] == '110'):    #Class C
            html_bits = '110'
            netBits=24
        elif (bIP[:4] == '1110'):   #Class D - Multicast
            html_bits = '1110'
            netBits=24
        elif (bIP[:4] == '1111'):   #Class E - Experimental
            html_bits = '1111'
            netBits=24
        else:
            assert False, 'FATAL: unhandled address type'

        classBits = len(html_bits)

        # get the lengths based on the class mask
        match = re.search(r'\/(\d+)\)', self.maskComboBox.currentText())
        prefix = int(match.group(1))    #assumes success

        classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current mask

        subnetBits = int(self.subnetbitsComboBox.currentText())
        netBits -= classBits

        if (subnetBits >= 0):
            hostBits -= subnetBits  #steal some bits from host
        else:
            netBits -= subnetBits   #steal from net bits

        debug ( f'_updateSubNetUsage: bits {classBits} net {netBits} subnet {subnetBits} host {hostBits}' )

        html = '{}{}{}{}'.format(html_bits, 'n'*netBits, 's'*subnetBits, 'h'*hostBits)
        html = re.sub('(.{8})(?!$)', r'\1.', html) #insert a '.' every 8 chars

        #color the pieces
        html = re.sub('(n+)', r'<font color="#{}">\1</font>'.format(themes[themeName][N_COLOR]), html) #color n teal
        html = re.sub('(s+)', r'<font color="#{}">\1</font>'.format(themes[themeName][S_COLOR]), html) #color s red
        html = re.sub('(h+)', r'<font color="#{}">\1</font>'.format(themes[themeName][H_COLOR]), html) #color h green

        self.subnetUsageTextEdit.clear()
        self.subnetUsageTextEdit.setText(html)

    def _addrChanged(self):
        debug ('addr changed', self.addrComboBox.currentText())
        if (ipValid(self.addrComboBox.currentText())):

            self.maskComboBox.setEnabled(True)
            self.subnetbitsComboBox.setEnabled(True)
            self.maxsubnetsComboBox.setEnabled(True)
            self.hostbitsComboBox.setEnabled(True)
            self.maxhostsComboBox.setEnabled(True)

            c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address

            self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), str(n)), strict=False)

            self.addr = ipaddress.IPv4Address(self.addrComboBox.currentText())

            self.maskComboBox.clear()
            for x in range(2, h+1):
                # debug (ipaddress.ip_address(2**32-2**x))
                self.maskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**x), 32-x))
            self.maskComboBox.setCurrentIndex(self.maskComboBox.count()-1)
            self.maskComboBox.setMaxVisibleItems(self.maskComboBox.count())

            self._updatePulldowns('subnetMask')
            self._updateAll()
        else:
            self.netUsageTextEdit.clear()
            self.subnetUsageTextEdit.clear()

            self.maskComboBox.setEnabled(False)
            self.subnetbitsComboBox.setEnabled(False)
            self.maxsubnetsComboBox.setEnabled(False)
            self.hostbitsComboBox.setEnabled(False)
            self.maxhostsComboBox.setEnabled(False)

            self._clearTable(0)

    def _maskChanged(self):
        bits = 30 - self.maskComboBox.currentIndex()
        debug ('mask changed' , self.maskComboBox.currentText(), bits)

        self._updatePulldowns('subnetMask')
        self._updateAll()

    def _maxsubnetsChanged(self):
        debug ('maxsubnetsChanged')
        self._updatePulldowns('maxSubnets')
        self._updateAll()

    def _subnetbitsChanged(self):
        debug ('subnetbitsChanged')
        self._updatePulldowns('subnetBits')
        self._updateAll()

    def _hostbitsChanged(self):
        debug ('_hostbitsChanged')
        self._updatePulldowns('hostBits')
        self._updateAll()

    def _maxhostsChanged(self):
        debug ('_maxhostsChanged')
        self._updatePulldowns('maxHosts')
        self._updateAll()

    def _updatePulldowns(self, requestor):

        classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the current addr

        if (requestor == 'subnetMask'):      #subnetMask changed, calc from that
            prefix = 30 - self.maskComboBox.currentIndex()
            debug ('subnetmask prefix:',prefix)
            classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current mask

        elif (requestor == 'subnetBits'):
            prefix = 30 - self.maskComboBox.currentIndex() + int(self.subnetbitsComboBox.currentText())
            classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current mask

        elif (requestor == 'maxSubnets'):
            debug ('index:', self.maxsubnetsComboBox.currentIndex(), 'val:', self.maxsubnetsComboBox.currentText())
            prefix = self.maxsubnetsComboBox.currentIndex() + netBits
            classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current addr

        elif (requestor == 'hostBits'):
            debug ('index:', self.hostbitsComboBox.currentIndex(), 'val:', self.hostbitsComboBox.currentText())
            prefix = 32 - int(self.hostbitsComboBox.currentText())
            debug ('new prefix', prefix)
            classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current addr

        elif (requestor == 'maxHosts'):
            debug ('index:', self.maxhostsComboBox.currentIndex(), 'val:', self.maxhostsComboBox.currentText())
            prefix = 32 - int(self.maxhostsComboBox.currentText())
            prefix=20
            debug ('new prefix', prefix)
            classBits, netBits, subnetBits, hostBits = getBits(self.addrComboBox.currentText(), prefix)   #get the bit lengths based on the current addr


        debug ( f'\n_updatePulldowns ({requestor}): \n  prefix {prefix} bits {classBits} net {netBits} subnet {subnetBits} host {hostBits}' )

        # if (requestor != 'subnetMask'):
            # self.maskComboBox.setCurrentIndex(hostBits-1)

        if (requestor != 'subnetBits'):
            self.subnetbitsComboBox.clear()

            #if we are here because of a new mask, force subnet bits to 0 (not subnetting) and shrink the available subnets
            if (requestor == 'subnetMask'):
                for x in range(0, subnetBits+hostBits-1):    # 0 .. number of network bits
                    self.subnetbitsComboBox.addItem(str(x))
                self.subnetbitsComboBox.setCurrentIndex(0)
            else:
                for x in range(0, 31-netBits):                               # 0 .. number of network bits
                    self.subnetbitsComboBox.addItem(str(x))
                self.subnetbitsComboBox.setCurrentIndex(subnetBits)
            self.subnetbitsComboBox.setMaxVisibleItems(self.subnetbitsComboBox.count())

        if (requestor != 'maxSubnets'):
            debug ('maxSubnets:', 32-hostBits, hostBits)
            self.maxsubnetsComboBox.clear()
            if (requestor == 'subnetMask'):
                for x in range(0, subnetBits+hostBits-1):
                    self.maxsubnetsComboBox.addItem(str(2**x))
                self.maxsubnetsComboBox.setCurrentIndex(0)
            else:
                for x in range(0, subnetBits+hostBits-1):  #
                    self.maxsubnetsComboBox.addItem(str(2**x))
                self.maxsubnetsComboBox.setCurrentIndex(int(self.subnetbitsComboBox.currentText()))
            self.maxsubnetsComboBox.setMaxVisibleItems(self.maxsubnetsComboBox.count())

        if (requestor != 'hostBits'):
            self.hostbitsComboBox.clear()
            debug ('hostbits: s',subnetBits,'h',hostBits)
            if (requestor == 'subnetMask'):
                for x in range(1, subnetBits+hostBits+1):
                    self.hostbitsComboBox.addItem(str(x))
                    self.hostbitsComboBox.setCurrentIndex(subnetBits+hostBits-1)
            else:
                for x in range(1, hostBits+1):
                    self.hostbitsComboBox.addItem(str(x))
                self.hostbitsComboBox.setCurrentIndex(hostBits-1)
            self.hostbitsComboBox.setMaxVisibleItems(self.hostbitsComboBox.count())

        if (requestor != 'maxHosts'):
            self.maxhostsComboBox.clear()
            if (requestor == 'subnetMask'):
                for x in range(1, subnetBits+hostBits+1):
                    self.maxhostsComboBox.addItem(str(2**x-2))
                self.maxhostsComboBox.setCurrentIndex(subnetBits+hostBits-1)
            else:
                for x in range(1, hostBits+1):
                    self.maxhostsComboBox.addItem(str(2**x-2))
                self.maxhostsComboBox.setCurrentIndex(hostBits-1)
            self.maxhostsComboBox.setMaxVisibleItems(self.maxhostsComboBox.count())

    def _updateAll(self):
        self._updateUsage()
        self._updateSubNetUsage()
        self._updateTable()


class MyIPv6Tab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        debug ('\ninit IPv6')

        # address
        self.addrLabel = QLabel('Address')


        self.addrComboBox = QComboBox()
        self.addrComboBox.setEditable(True)

        #create a 2 column pulldown

        self.addrModel = QStandardItemModel()
        self.addrModel.setHorizontalHeaderLabels( ['Address', 'Address Type'] )

        for x in defaultIPv6Addresses:

            col1_item = QStandardItem(x)
            col2_item = QStandardItem(defaultIPv6Addresses[x])
            self.addrModel.appendRow([col1_item, col2_item])

        view = QTreeView()
        view.setRootIsDecorated(False)

        self.addrComboBox.setView(view)
        self.addrComboBox.setModel(self.addrModel)
        view.setColumnWidth(0,200)


        self.addrComboBox.setMaxVisibleItems(self.addrComboBox.count())
        self.addrComboBox.setDuplicatesEnabled(False)
        self.addrComboBox.InsertPolicy(QComboBox.NoInsert)
        #self.addrComboBox.activated.connect(self._addrChanged)
        self.addrComboBox.editTextChanged.connect(self._addrChanged)

        # address type - treeview

        self.typeLabel = QLabel('Address Type')

        self.treeView = QTreeView()
        self.treeView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treeView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.model = self.createModel(self)
        self.treeView.setModel(self.model)
        #self.treeView.setUniformRowHeights(True)

        self.addItem(self.model, 'Unspecified','::/128','')
        self.treeView.setCurrentIndex(self.model.index(0,0))    # and select it
        self.addItem(self.model, 'Loopback','::1/128','')

        self.Unicast = self.addItem(self.model, 'Unicast','', 'Abstract')

        self.LinkLocal = self.addItem(self.Unicast, 'Link-Local', 'FE80::/10','')
        self.sixover4 = self.addItem(self.LinkLocal, '6over4','FE80::/96','')
        self.isatap = self.addItem(self.LinkLocal, 'ISATAP','FE80::5EFE:0:0/96','')

        self.siteLocal = self.addItem( self.Unicast, 'Site-Local', 'FEC0::/10', 'Deprecated')

        self.Global = self.addItem( self.Unicast,'Global','','Abstract')
        self.Unformatted = self.addItem(self.Global, 'Unformatted','::/3','')
        self.ipv4compat = self.addItem(self.Unformatted, 'IPv4-Compatible','::/96','Deprecated')
        self.ipv4 = self.addItem(self.Unformatted, 'IPv4-Mapped','::FFFF:0.0.0.0/96','')

        self.EUI64 = self.addItem(self.Global, 'EUI-64 Formatted','','Abstract')
        self.IANADelegated = self.addItem(self.EUI64,'IANA Delegated','2000::/3','')
        self.Toredo = self.addItem(self.IANADelegated, 'Teredo Tunneling','2001::/32','')
        self.sixtofour =self.addItem(self.IANADelegated, '6to4','2002::/16','')

        self.Multicast = self.addItem(self.model, 'Multicast','FF00::/8', '')
        self.IntLocal = self.addItem(self.Multicast, 'Interface-Local', 'FF01::/16','')
        self.allNodes1 = self.addItem(self.IntLocal, 'All Nodes','FF01::1/128','')
        self.allRouters1 = self.addItem(self.IntLocal, 'All Routers','FF01::2/128','')
        self.LinkLocalM = self.addItem(self.Multicast, 'Link-Local', 'FF02::/16','')
        self.allNodes2 = self.addItem(self.LinkLocalM, 'All Nodes','FF02::1/128','')
        self.allRouters2 = self.addItem(self.LinkLocalM, 'All Routers','FF02::2/128','')

        self.adminLocal = self.addItem(self.Multicast, 'Admin-Local','FF04::/16','')

        self.SiteLocal = self.addItem(self.Multicast, 'Site-Local', 'FF05::/16','Deprecated')
        self.allRouters3 = self.addItem(self.SiteLocal, 'All Routers','FF05::2/128','Deprecated')

        self.orgLocal = self.addItem(self.Multicast, 'Organization-Local','FF08::/16','')
        self.GlobalM = self.addItem(self.Multicast, 'Global','FF0E::/16','')


        self.treeView.expandAll()
        self.treeView.resizeColumnToContents(0)
        self.treeView.selectionModel().currentRowChanged.connect(self._treeViewChanged)
        #self.treeView.selectionModel().selectionChanged.connect(self._treeViewChanged)

        self.formatLabel = QLabel('Address Format')

        self.addrGroup = QGroupBox('')
        self.addrLayout = QGridLayout()
        self.addrLayout.setSpacing(0)
        self.addrGroup.setLayout(self.addrLayout)

        # grid
        ipv6Grid = QGridLayout()
        ipv6Grid.addWidget(self.addrLabel   ,0,0)       #row, col[, rowspan, colspan]
        ipv6Grid.addWidget(self.addrComboBox,1,0)

        ipv6Grid.addWidget(self.typeLabel,   2,0)
        ipv6Grid.addWidget(self.treeView,    3,0)

        ipv6Grid.addWidget(self.formatLabel, 4,0)
        ipv6Grid.addWidget(self.addrGroup,    5,0)

        self.setLayout(ipv6Grid)

        self._addrChanged()

    def updateAddressFormat(self, list1,list2,list3):
        debug ('updateAddressFormat')

        # clear the grid
        for i in reversed(range(self.addrLayout.count())):
            try:
                self.addrLayout.itemAt(i).widget().setParent(None)
            except:
                continue

        # first row of address format:   x bits...
        for c in range(len(list1)):
            label = QLabel(list1[c])
            label.setObjectName('ipv6Text')
            self.addrLayout.addWidget(label,0,c,QtCore.Qt.AlignCenter)

            # proportinally size the columns base on the number of bits
            bits = re.search(r'(\d+) bits', list1[c]).group(1)
            self.addrLayout.setColumnStretch(c,int(bits))

        # second row of address format: shaded box
        for c in range(len(list2)):
            # #need a frame around these
            frame = QFrame()
            frame.setObjectName('ipv6Frame')
            frame.setFrameShape(QFrame.Box)   #Box, Panel, StyledPanel, WinPanel
            frame.setFrameShadow(QFrame.Plain)
            self.addrLayout.addWidget(frame,1,c)
            
            label = QLabel(list2[c])
            label.setStyleSheet('QLabel {color: black; background-color: transparent;}')
            self.addrLayout.addWidget(label, 1, c, QtCore.Qt.AlignCenter)

        # third row of address format: descriptive text
        for c in range(len(list3)):
            label = QLabel(list3[c])
            label.setObjectName('ipv6Text')
            label.setStyleSheet('QLabel {padding-bottom: 4px;}')
            self.addrLayout.addWidget(label,2,c,QtCore.Qt.AlignCenter|QtCore.Qt.AlignTop)

        self.addrLayout.setContentsMargins(10,0,10,0) #top, left, right, bottom

    def _treeViewChanged(self,newIndex,oldIndex=None):
        debug ('\n_treeViewChanged')

        # get the addr pattern from the tree and apply it to the address
        index = self.treeView.currentIndex()
        # item = self.treeView.model().itemFromIndex(index)
        # print ('item.text',item.text())
        sibling = index.siblingAtColumn(1)
        debug ('sibling',self.treeView.model().itemFromIndex(sibling).text())
        self.addrComboBox.setCurrentText(self.treeView.model().itemFromIndex(sibling).text())

    def _addrChanged(self):
        debug ('_addrChanged')
        if ipv6Valid(self.addrComboBox.currentText()):

            debug ('')
            self.treeView.setEnabled(True)
            # clear the grid
            for i in reversed(range(self.addrLayout.count())):
                try:
                    self.addrLayout.itemAt(i).widget().setParent(None)
                except:
                    continue

            ipaddr = self.addrComboBox.currentText()
            #debug ('ipaddr',ipaddr)
            match = re.search(r'^([a-fA-F0-9:]+)[\/ ]?',ipaddr)
            #debug ('ipaddr', match.group(1))
            addr = ipaddress.IPv6Address(match.group(1))

            bIPv6 = '{:0128b}'.format(int(addr))
            exploded = addr.exploded

            debug (exploded, str(addr))
            debug ('012345678901234567890123456789012345678')
            debug ('          1         2         3       ')
            debug ('bIPv6', re.sub(r'(.{8})(?!$)', r'\1.', bIPv6))  #binary with '.'

            debug ('6to4:[{}] ipv4_mapped:[{}] is_link_local:[{}] is_site_local:[{}] is_global:[{}]'.format(
                addr.sixtofour, addr.ipv4_mapped, addr.is_link_local, addr.is_site_local, addr.is_global))

            selmod = self.treeView.selectionModel()

            if (addr.is_unspecified):
                debug ('unspecified')
                index = self.model.index(0,0)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                self.updateAddressFormat(['128 bits'],['0000...0000<sub>2</sub>'],['Unspecified Address Constant'])

            elif (addr.is_loopback):
                debug ('loopback')
                index = self.model.index(1,0)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                self.updateAddressFormat(['128 bits'],['0000...0001<sub>2</sub>'],['Loopback Address Constant'])

            elif (addr.ipv4_mapped is not None):
                debug ('ipv4_mapped', addr.ipv4_mapped)
                index = self.model.indexFromItem(self.ipv4)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                self.updateAddressFormat(
                    ['3 bits','77 bits','16 bits','32 bits'],
                    ['000<sub>2</sub>','0', 'FFFF', Int2IP(int(exploded[30:34]+exploded[35:],16))],
                    ['6to4 Prefix','Embedded IPv4 Address Prefix','IPv4-\nMapped\nConstant','IPv4 Address']
                )

        #unicast
        # ------

            elif (addr.is_link_local):      #FE80:/10 link-local
                if (addr.compressed[:10] == 'fe80::5efe'):   #ISATAP
                    debug ('ISATAP')
                    index = self.model.indexFromItem(self.isatap)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['10 bits','86 bits','32 bits'],
                                            ['0xFE80','0',Int2IP(int(exploded[30:34]+exploded[35:],16))],
                                            ['Link-\nLocal\nPrefix','ISATAP Constant','IPv4 Address'])
                elif (exploded[:29] == 'fe80:0000:0000:0000:0000:0000'):         #6over4 FE80::/96
                    debug ('6over4')
                    index = self.model.indexFromItem(self.sixover4)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['10 bits','86 bits','32 bits'],
                                            ['0xFE80','0',Int2IP(int(exploded[30:34]+exploded[35:],16))],
                                            ['Link-\nLocal\nPrefix','6over4 Constant','IPv4 Address'])
                else:
                    debug ('link_local')
                    index = self.model.indexFromItem(self.LinkLocal)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                    eui64 = re.sub(':', '', exploded[20:])
                    eui64 = re.sub('(.{2})(?!$)', r'\1:', eui64) #insert a ':' every 2 chars

                    subid = str(hex(int(bIPv6[10:64],2)))

                    # these 54 bits should all be zero, otherwise it is invalid
                    if (int(bIPv6[10:64],2) == 0):
                        label = 'Unused'
                    else:
                        label = 'Mangled Scope ID'
                    self.updateAddressFormat(['10 bits','54 bits','64 bits'],
                                            ['0xFE80',subid,eui64],
                                            ['Link-\nLocal\nPrefix',label,'EUI-64 Interface ID'])

            elif (addr.is_site_local):
                debug ('is_site_local')
                index = self.model.indexFromItem(self.siteLocal)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                eui64 = re.sub(':', '', exploded[20:])
                eui64 = re.sub('(.{2})(?!$)', r'\1:', eui64) #insert a ':' every 2 chars

                subid = str(hex(int(bIPv6[10:64],2)))

                self.updateAddressFormat(
                    ['10 bits','54 bits','64 bits'],
                    ['0xFEC0', subid,  eui64],
                    ['Site-\nLocal\nPrefix','Subnet ID','EUI-64 InterfaceID']
                )

            elif (addr.sixtofour):
                debug ('6to4')
                index = self.model.indexFromItem(self.sixtofour)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                eui64 = re.sub(':', '', exploded[20:])
                eui64 = re.sub('(.{2})(?!$)', r'\1:', eui64) #insert a ':' every 2 chars

                self.updateAddressFormat(
                    ['16 bits','32 bits','16 bits','64 bits'],
                    ['2001',Int2IP(int(exploded[5:9]+exploded[10:14],16)), '0x'+exploded[15:19].upper(), eui64],
                    ['6to4 Prefix','IPv4 Address','Subnet ID','EUI-64 InterfaceID']
                )

            elif (addr.teredo):
                debug ('teredo',addr.teredo,addr.teredo[1].exploded)
                index = self.model.indexFromItem(self.Toredo)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                #2001:0000:0000:0001:60c0:9f23
                #01234567890123456789012345
                # print ('flags',addr.exploded[20:24])
                # print ('port', addr.exploded[25:29], int(addr.exploded[25:29],16) )
                self.updateAddressFormat(
                    ['32 bits','32 bits','16 bits','16 bits','32 bits'],
                    ['2001:0000',addr.teredo[0].exploded,'0x'+addr.exploded[20:24].upper(), str(int(addr.exploded[25:29],16)), addr.teredo[1].exploded],
                    ['Teredo Prefix','Teredo Server Address','Teredo\nFlags','Obfuscated\nNAT UDP\nPort','Obfuscated NAT Public\nIPv4 Address']
                )

            elif (bIPv6[:3]=='001' ):       #IANA Delegated
                debug ('IANA Delegated')

                index = self.model.indexFromItem(self.IANADelegated)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                bits61 = '0x{0:0{1}x}'.format (int(bIPv6[3:64],2),16)   #format bits 3-64 as binary and convert to hex
                bits61 = bits61[2:] #strip 0x
                bits61 = re.sub('(.{4})(?!$)', r'\1.', bits61) #add a '.' every 4 chars

                eui64 = re.sub(':', '', exploded[20:])
                eui64 = re.sub('(.{2})(?!$)', r'\1:', eui64) #insert a ':' every 2 chars

                self.updateAddressFormat(
                    ['3 bits','61 bits','64 bits'],
                    ['001<sub>2</sub>','0x'+bits61, eui64],
                    ['IANA-\nDelegated\nPrefix','Unknown','EUI-64 Interface ID']
                )

        # multicast
        # ---------
            elif (addr.is_multicast):
                debug ('multicast')

                if (re.search(r'^ff.1',addr.compressed)):   #Interface-local

                    if (addr.compressed == 'ff01::1'):      #all nodes

                        index = self.model.indexFromItem(self.allNodes1)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x1', '0000:0000:0000:0000:0000:0000:0001'],
                                                ['Multicast\nPrefix','Flags','Intf-\nLocal\nScope', 'All Nodes Group ID'])

                    elif (addr.compressed == 'ff01::2'):    #all routers

                        index = self.model.indexFromItem(self.allRouters1)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x1', '0000:0000:0000:0000:0000:0000:0002'],
                                                ['Multicast\nPrefix','Flags','Intf-\nLocal\nScope', 'All Routers Group ID'])

                    else:
                        index = self.model.indexFromItem(self.IntLocal)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x1', exploded[5:]],
                                                ['Multicast\nPrefix','Flags','Intf-\nLocal\nScope', 'Group ID'])

                elif (re.search('^ff.2',addr.compressed)):   #Link-local

                    if (addr.compressed == 'ff02::1'):      #all nodes

                        index = self.model.indexFromItem(self.allNodes2)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x2', '0000:0000:0000:0000:0000:0000:0001'],
                                                ['Multicast\nPrefix','Flags','Link-\nLocal\nScope', 'All Nodes Group ID'])

                    elif (addr.compressed == 'ff02::2'):    #all routers

                        index = self.model.indexFromItem(self.allRouters2)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x2', '0000:0000:0000:0000:0000:0000:0002'],
                                                ['Multicast\nPrefix','Flags','Link-\nLocal\nScope', 'All Routers Group ID'])

                    else:
                        index = self.model.indexFromItem(self.LinkLocalM)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x2', exploded[5:]],
                                                ['Multicast\nPrefix','Flags','Link-\nLocal\nScope', 'Group ID'])

                elif (re.search('^ff.4',addr.compressed)):   #Admin-local

                    index = self.model.indexFromItem(self.adminLocal)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                            ['0xFF','....<sub>2</sub>', '0x4', exploded[5:]],
                                            ['Multicast\nPrefix','Flags','Admin-\nLocal\nScope', 'Group ID'])

                elif (re.search('^ff.5',addr.compressed)):   #Site-local

                    if (addr.compressed == 'ff05::2'):    #all routers

                        index = self.model.indexFromItem(self.allRouters3)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x5', '0000:0000:0000:0000:0000:0000:0002'],
                                                ['Multicast\nPrefix','Flags','Site-\nLocal\nScope', 'All Routers Group ID'])

                    else:
                        index = self.model.indexFromItem(self.SiteLocal)
                        selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                        self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                                ['0xFF','....<sub>2</sub>', '0x5', exploded[5:]],
                                                ['Multicast\nPrefix','Flags','Site-\nLocal\nScope', 'Group ID'])


                elif (re.search('^ff.8',addr.compressed)):   #Org-local

                    index = self.model.indexFromItem(self.orgLocal)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                            ['0xFF','....<sub>2</sub>', '0x8', exploded[5:]],
                                            ['Multicast\nPrefix','Flags','Org-\nLocal\nScope', 'Group ID'])


                elif (re.search('^ff.e',addr.compressed)):   #global

                    index = self.model.indexFromItem(self.GlobalM)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                            ['0xFF','....<sub>2</sub>', '0xE', exploded[5:]],
                                            ['Multicast\nPrefix','Flags','Global\nScope', 'Group ID'])

                else:       #Generic multicast

                    index = self.model.indexFromItem(self.Multicast)
                    selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                    self.updateAddressFormat(['8 bits','4 bits','4 bits','112 bits'],
                                            ['0xFF','....<sub>2</sub>', '0x0', exploded[5:]],
                                            ['Multicast\nPrefix','Flags','Reserved\nScope', 'Group ID'])


            elif (bIPv6[:96]=='0'*96):  #ipv4-compat

                debug ('IPv4 compatible')
                index = self.model.indexFromItem(self.ipv4compat)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)
                self.updateAddressFormat(['3 bits','77 bits','16 bits','32 bits'],
                                        ['000<sub>2</sub>','0', '0000', Int2IP(int(exploded[30:34]+exploded[35:],16)) ],
                                        ['Unformatted\nPrefix','Embedded IPv4 Address Prefix','IPv4-\nCompatible\nConstant', 'IPv4 Address'])

            elif (bIPv6[:3]=='000'):    #unformatted

                debug ('unformatted')

                index = self.model.indexFromItem(self.Unformatted)
                selmod.select(index,QItemSelectionModel.ClearAndSelect|QItemSelectionModel.Rows)

                self.updateAddressFormat(['3 bits','125 bits'],
                                        ['000<sub>2</sub>', exploded ],
                                        ['Unformatted\nPrefix', 'Unknown'])
            else:
                assert False, 'FATAL: unhandled address type'

        else:
            debug ('ipv6 not valid')
            self.treeView.setEnabled(False)
            # clear the grid
            for i in reversed(range(self.addrLayout.count())):
                try:
                    self.addrLayout.itemAt(i).widget().setParent(None)
                except:
                    continue

    def createModel(self, parent):
        model = QStandardItemModel(0, 3, parent)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Type')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Pattern')
        model.setHeaderData(2, QtCore.Qt.Horizontal, 'Notes')

        return model

    #add three cols of data, return typeItem in case it is used later
    def addItem(self, parent, type, pattern, notes):
        typeItem = QStandardItem(type)
        notesItem = QStandardItem(notes)
        patternItem = QStandardItem(pattern)
        if (notes == 'Abstract'):
            typeItem.setEnabled(False)
            notesItem.setEnabled(False)
            patternItem.setEnabled(False)

        parent.appendRow( [ typeItem, patternItem, notesItem ] )
        return typeItem


class MyVLSMTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        debug ('\ninit vlsm')

        # address
        self.addrComboBox = QComboBox()
        self.addrComboBox.setEditable(True)
        self.addrComboBox.addItems(defaultIPv4Addresses)
        self.addrLabel = QLabel('Address')
        self.addrComboBox.currentTextChanged.connect(self._addrChanged)

        # subnet mask
        self.maskComboBox = QComboBox()

        self.maskLabel = QLabel('Subnet Mask')
        c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address
        # debug (c,n,s,h)

        for x in range(0, 32):
            self.maskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**x), 32-x))
        self.maskComboBox.setCurrentIndex(32-n)
        self.maskComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.maskComboBox.activated.connect(self._maskChanged)

        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

        # network bit usage label
        labelText  = f'<font color="#{themes[themeName][N_COLOR]}">n=Network</font>; '
        labelText += f'<font color="#{themes[themeName][H_COLOR]}">h=Host</font>'
        labelText += ')'

        self.netUsageLabel = QLabel('Network Bit Usage (' + labelText)
        self.netUsageLabel.setObjectName('multiColor')

        self.descrLabel = QLabel()
        self.descrLabel.setAlignment( QtCore.Qt.AlignRight )

        self.netUsageTextEdit = QTextEdit()
        self.netUsageTextEdit.setObjectName('multiColor')
        self.netUsageTextEdit.setReadOnly(True)
        self.netUsageTextEdit.setMaximumHeight(22)
        self.netUsageTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # subnet bits, max subnets, host bits, max hosts
        self.maskbitsLabel = QLabel('Mask Bits')
        self.maskbitsComboBox = QComboBox()
        for x in range(1,32+1):
            self.maskbitsComboBox.addItem(str(x))
        self.maskbitsComboBox.setMaxVisibleItems(32)
        self.maskbitsComboBox.activated.connect(self._maskbitsChanged)

        self.maxsubnetLabel = QLabel('Maximum Subnets')
        self.maxsubnetsComboBox = QComboBox()
        for x in range(32-1,0,-1):
            self.maxsubnetsComboBox.addItem(str(2**x))
        self.maxsubnetsComboBox.setMaxVisibleItems(32)
        self.maxsubnetsComboBox.activated.connect(self._maxsubnetsChanged)

        self.maxaddrLabel = QLabel('Maximum Addresses')

        self.maxaddrComboBox = QComboBox()
        for x in range(32-1,0,-1):
            self.maxaddrComboBox.addItem(str(2**x-2))
        self.maxaddrComboBox.setMaxVisibleItems(32)
        self.maxaddrComboBox.activated.connect(self._maxaddrChanged)

        # static output
        self.vlsmaddrLabel = QLabel('VLSM Network Address')
        self.vlsmaddrTextEdit = QLineEdit()
        self.vlsmaddrTextEdit.setReadOnly(True)

        self.vlsmnoteLabel = QLabel('VLSM Network Notation')
        self.vlsmnoteTextEdit = QLineEdit()
        self.vlsmnoteTextEdit.setReadOnly(True)

        self.vlsmrangeLabel = QLabel('VLSM Address Range')
        self.vlsmrangeTextEdit = QLineEdit()
        self.vlsmrangeTextEdit.setReadOnly(True)


        # filler - force all the widgets above to the top
        self.fillerLabel = QLabel('')

        # grid
        vlsmGrid = QGridLayout()
        vlsmGrid.addWidget(self.addrLabel   ,0,0,1,3)       #row, col[, rowspan, colspan]
        vlsmGrid.addWidget(self.addrComboBox,1,0,1,3)
        vlsmGrid.addWidget(self.maskLabel,   0,3,1,3)
        vlsmGrid.addWidget(self.maskComboBox,1,3,1,3)

        vlsmGrid.addWidget(self.netUsageLabel,2,0,1,4)
        vlsmGrid.addWidget(self.descrLabel,2,4,1,2)
        vlsmGrid.addWidget(self.netUsageTextEdit,3,0,1,6)

        vlsmGrid.addWidget(self.maskbitsLabel,4,0,1,2)
        vlsmGrid.addWidget(self.maskbitsComboBox,5,0,1,2)

        vlsmGrid.addWidget(self.maxsubnetLabel,4,2,1,2)
        vlsmGrid.addWidget(self.maxsubnetsComboBox,5,2 ,1,2)

        vlsmGrid.addWidget(self.maxaddrLabel,4,4,1,2)
        vlsmGrid.addWidget(self.maxaddrComboBox,5,4,1,2)

        vlsmGrid.addWidget(self.vlsmaddrLabel,6,0,1,2)
        vlsmGrid.addWidget(self.vlsmaddrTextEdit,7,0,1,2)
        vlsmGrid.addWidget(self.vlsmnoteLabel,6,2,1,2)
        vlsmGrid.addWidget(self.vlsmnoteTextEdit,7,2,1,2)
        vlsmGrid.addWidget(self.vlsmrangeLabel,6,4,1,2)
        vlsmGrid.addWidget(self.vlsmrangeTextEdit,7,4,1,2)


        vlsmGrid.addWidget(self.fillerLabel,8,0)
        vlsmGrid.setRowStretch(8,1)

        self.setLayout(vlsmGrid)

        self._updateAll()

    def _addrChanged(self):
        debug ('addr changed', self.addrComboBox.currentText())
        if (ipValid(self.addrComboBox.currentText())):
            self.maxaddrComboBox.setEnabled(True)
            self.maxsubnetsComboBox.setEnabled(True)
            self.maskbitsComboBox.setEnabled(True)
            self.maskComboBox.setEnabled(True)

            c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address
            self.maskComboBox.setCurrentIndex(32-n)

            self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

            self._updateAll()
        else:
            self.netUsageTextEdit.clear()
            self.vlsmaddrTextEdit.clear()
            self.vlsmnoteTextEdit.clear()
            self.vlsmrangeTextEdit.clear()

            self.maxaddrComboBox.setEnabled(False)
            self.maxsubnetsComboBox.setEnabled(False)
            self.maskbitsComboBox.setEnabled(False)
            self.maskComboBox.setEnabled(False)

    def _maskChanged(self):
        bits = 32 - self.maskComboBox.currentIndex()
        debug ('mask changed' , self.maskComboBox.currentText(), bits)

        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

        self._updateAll()

    def _maskbitsChanged(self):
        debug ('maskbits changed' , self.maskbitsComboBox.currentText())

        prefix = self.maskbitsComboBox.currentIndex()+1
        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), prefix), strict=False)
        debug ('net',self.net)

        self._updateAll()

    def _maxsubnetsChanged(self):
        prefix = 32-self.maxsubnetsComboBox.currentIndex()
        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), prefix), strict=False)

        self._updateAll()

    def _maxaddrChanged(self):
        prefix = 32-self.maxaddrComboBox.currentIndex()
        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), prefix), strict=False)

        self._updateAll()

    def _updateVLSMInfo(self):
        self.vlsmaddrTextEdit.setText(str(self.net[0]))
        self.vlsmnoteTextEdit.setText(str(self.net))
        self.vlsmrangeTextEdit.setText( str(self.net[0])+' - '+str(self.net[-1]) )

    def _updatePulldowns(self):

        prefix = self.net.prefixlen
        debug ('_updatePullDowns, prefix',prefix)

        self.maskComboBox.setCurrentIndex(32-prefix)
        self.maskbitsComboBox.setCurrentIndex(prefix-1)
        self.maxsubnetsComboBox.setCurrentIndex(prefix-1)
        self.maxaddrComboBox.setCurrentIndex(prefix-1)

        self._updateVLSMInfo()


    def _updateUsage(self):

        c, n, s, h = getBits(self.addrComboBox.currentText(),0)   #get the bit lengths based on the classful address
        self.addr = ipaddress.IPv4Address(self.addrComboBox.currentText())


        if (int(self.addr)==0):         #this host
            net_class='Class A - This Host'
            html_bits = '0'

        elif (int(self.addr)==1):       #this network
            net_class='Class A - This Network'
            html_bits = '0'

        elif (int(self.addr)==2**32-1): #broadcast
            net_class='Class E - Broadcast'
            html_bits = '1111'

        elif (self.addr.is_loopback):
            net_class='Class A - Loopback'
            html_bits = '0'

        elif (self.addr.is_multicast):
            net_class='Class D - Multicast'
            html_bits = '1110'

        elif (int(self.addr) & 0xF0000000 == 0xF0000000):   # class E
            net_class='Class E - Experimental'
            html_bits = '1111'

        elif (n==8):
            net_class='Class A'
            html_bits = '0'

        elif(n==16):
            net_class='Class B'
            html_bits = '10'

        elif(n==24):
            net_class='Class C'
            html_bits = '110'

        classBits = len(html_bits)

        if (self.addr.is_private and int(self.addr)>1 and int(self.addr)<2**32-1 and not self.addr.is_loopback and not self.addr.is_multicast): #ignore this host and this network
            debug('is private')
            net_class += ' - Private'

        hostBits = self.maskComboBox.currentIndex()
        netBits = 32 - hostBits - classBits
        if (netBits<0):
            hostBits += netBits
            netBits = 0

        debug ( f'_updateUsage: bits {classBits} net {netBits} host {hostBits}' )

        html = '{}{}{}'.format(html_bits, 'n'*netBits, 'h'*hostBits)

        html = re.sub('(.{8})(?!$)', r'\1.', html) #insert a '.' every 8 chars

        #color the pieces
        html = re.sub('(n+)', r'<font color="#{}">\1</font>'.format(themes[themeName][N_COLOR]), html) #color n teal
        html = re.sub('(h+)', r'<font color="#{}">\1</font>'.format(themes[themeName][H_COLOR]), html) #color h green

        self.descrLabel.setText('['+net_class+']')


        self.netUsageTextEdit.clear()
        self.netUsageTextEdit.setText(html)

    def _updateAll(self):
        self._updatePulldowns()
        self._updateUsage()
        self._updateVLSMInfo()


class MyCIDRTab(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        # address
        self.addrComboBox = QComboBox()
        self.addrComboBox.setEditable(True)
        self.addrComboBox.addItem('10.110.110.100')
        self.addrComboBox.addItem('10.0.0.0')
        self.addrComboBox.addItem('221.221.221.0')
        self.addrComboBox.addItem('192.168.1.0')
        self.addrComboBox.addItem('206.67.58.195')
        self.addrComboBox.addItem('128.1.2.0')
        self.addrComboBox.addItem('224.0.0.0')
        self.addrComboBox.addItem('240.0.0.0')
        self.addrLabel = QLabel('Address')
        self.addrComboBox.currentTextChanged.connect(self._addrChanged)

        # subnet mask
        self.maskComboBox = QComboBox()

        self.maskLabel = QLabel('Address Block Mask')

        c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address
        debug (c,n,s,h)

        for x in range(0, 32):
            # debug (ipaddress.ip_address(2**32-2**x))
            self.maskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**x), 32-x))
        self.maskComboBox.setCurrentIndex(32-n)
        self.maskComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.maskComboBox.activated.connect(self._maskChanged)

        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

        # address block range
        self.addrblockLabel = QLabel('Address Block Range')

        self.addrblockLineEdit = QPlainTextEdit()
        self.addrblockLineEdit.setReadOnly(True)
        self.addrblockLineEdit.setMaximumHeight(24)

        # cidr bits, max routes, cidr mask
        self.cidrbitsLabel = QLabel('CIDR Bits')
        self.cidrbitsComboBox = QComboBox()
        for x in range(1,24+1):                          # 0 .. number of network bits
            self.cidrbitsComboBox.addItem(str(x))
        self.cidrbitsComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.cidrbitsComboBox.activated.connect(self._cidrbitsChanged)

        self.maxroutesLabel = QLabel('Max Routes')
        self.maxroutesComboBox = QComboBox()
        self.maxroutesComboBox.activated.connect(self._maxroutesChanged)

        self.cidrmaskLabel = QLabel('CIDR Mask')
        self.cidrmaskComboBox = QComboBox()

        self.cidrmaskComboBox.activated.connect(self._cidrmaskChanged)

        # cidr bit usage label
        labelText  = f'<font color="#{themes[themeName][C_COLOR]}">c=CIDR</font>; '
        labelText += f'<font color="#{themes[themeName][X_COLOR]}">x=Open</font>'
        labelText += ')'

        self.netUsageLabel = QLabel('CIDR Bit Usage (' + labelText)
        self.netUsageLabel.setObjectName('multiColor')

        self.usageTextEdit = QTextEdit()
        self.usageTextEdit.setObjectName('multiColor')
        self.usageTextEdit.setReadOnly(True)
        self.usageTextEdit.setMaximumHeight(22)
        self.usageTextEdit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        #results table
        self.resultsTable = QTableWidget(1, 2)
        self.resultsTable.setHorizontalHeaderLabels(('Route', 'Address Range'))
        self.resultsTable.horizontalHeader().setStyleSheet('::section {font-weight: bold; padding: 1px}')
        self.resultsTable.verticalHeader().setStyleSheet('::section { padding: 0px 1px;}')
        self.resultsTable.setAlternatingRowColors(True)
        self.resultsTable.setContentsMargins(0,0,0,0) #top, left, right, bottom
        self.resultsTable.setCornerButtonEnabled(False)
        #self.resultsTable.setSpacing(0)

        # grid
        cidrGrid = QGridLayout()
        cidrGrid.addWidget(self.addrLabel,0,0,1,2)       #row, col[, rowspan, colspan]
        cidrGrid.addWidget(self.addrComboBox,1,0,1,2)
        cidrGrid.addWidget(self.maskLabel,0,2,1,2)
        cidrGrid.addWidget(self.maskComboBox,1,2,1,2)
        cidrGrid.addWidget(self.addrblockLabel,2,0)
        cidrGrid.addWidget(self.addrblockLineEdit,3,0,1,4)

        cidrGrid.addWidget(self.cidrbitsLabel,4,0)
        cidrGrid.addWidget(self.cidrbitsComboBox,5,0)

        cidrGrid.addWidget(self.maxroutesLabel,4,1)
        cidrGrid.addWidget(self.maxroutesComboBox,5,1)

        cidrGrid.addWidget(self.cidrmaskLabel,4,2,1,2)
        cidrGrid.addWidget(self.cidrmaskComboBox,5,2,1,2)

        cidrGrid.addWidget(self.netUsageLabel,6,0,1,4)
        cidrGrid.addWidget(self.usageTextEdit,7,0,1,4)
            
        cidrGrid.addWidget(self.resultsTable,8,0,1,4)

        self.setLayout(cidrGrid)

        self._maskChanged() #force pulldowns to update
        self._updateAll()

    def _addrChanged(self):
        debug ('addr changed', self.addrComboBox.currentText())
        if (ipValid(self.addrComboBox.currentText())):
            debug ('valid')

            self.maskComboBox.setEnabled(True)
            self.cidrbitsComboBox.setEnabled(True)
            self.maxroutesComboBox.setEnabled(True)
            self.cidrmaskComboBox.setEnabled(True)

            c, n, s, h = getBits(self.addrComboBox.currentText(), 0)   #get the bit lengths based on the classful address
            self.maskComboBox.setCurrentIndex(32-n)

            self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

            self._maskChanged() #force update of other pulldowns

        else:
            debug ('addr not valid')
            self.addrblockLineEdit.clear()
            self.usageTextEdit.clear()

            self.maskComboBox.setEnabled(False)
            self.cidrbitsComboBox.setEnabled(False)
            self.maxroutesComboBox.setEnabled(False)
            self.cidrmaskComboBox.setEnabled(False)

            self.resultsTable.setRowCount(0)

    def _maskChanged(self):
        bits = 32 - self.maskComboBox.currentIndex()
        debug ('mask changed' , self.maskComboBox.currentText(), bits)

        self.net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), 32-self.maskComboBox.currentIndex()), strict=False)

        self.cidrbitsComboBox.clear()
        for x in range(1,32-self.net.prefixlen+1):                          # 0 .. number of network bits
            self.cidrbitsComboBox.addItem(str(x))
        self.cidrbitsComboBox.setCurrentIndex(0)
        self.cidrbitsComboBox.setMaxVisibleItems(self.maskComboBox.count())

        self._cidrbitsChanged() #force update of other pulldowns

    def _cidrbitsChanged(self):
        debug ('_cidrbitsChanged')

        #update max routes
        self.maxroutesComboBox.clear()
        for x in range(1, self.cidrbitsComboBox.count()+1):  #always same # of entries as cidrbits list
            self.maxroutesComboBox.addItem(str(2**x))
        self.maxroutesComboBox.setMaxVisibleItems(self.maxroutesComboBox.count())
        self.maxroutesComboBox.setCurrentIndex(self.cidrbitsComboBox.currentIndex())

        #update CIDR mask
        self.cidrmaskComboBox.clear()
        for x in range(32-self.maskComboBox.currentIndex()+1, 33):
            self.cidrmaskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**(32-x)), x))
        self.cidrmaskComboBox.setMaxVisibleItems(self.cidrmaskComboBox.count())
        self.cidrmaskComboBox.setCurrentIndex(self.cidrbitsComboBox.currentIndex())

        self._updateAll()

    def _maxroutesChanged(self):
        debug ('_maxroutesChanged')

        # update cidr bits
        self.cidrbitsComboBox.clear()
        for x in range(1,32-self.net.prefixlen+1):                          # 0 .. number of network bits
            self.cidrbitsComboBox.addItem(str(x))
        self.cidrbitsComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.cidrbitsComboBox.setCurrentIndex(self.maxroutesComboBox.currentIndex())

        #update CIDR mask
        self.cidrmaskComboBox.clear()
        for x in range(32-self.maskComboBox.currentIndex()+1,33):
            self.cidrmaskComboBox.addItem('{}  (/{})'.format(ipaddress.ip_address(2**32-2**(32-x)), x))
        self.cidrmaskComboBox.setMaxVisibleItems(self.cidrmaskComboBox.count())
        self.cidrmaskComboBox.setCurrentIndex(self.maxroutesComboBox.currentIndex())

        self._updateAll()

    def _cidrmaskChanged(self):
        debug ('_cidrmaskChanged')

        # update cidr bits
        self.cidrbitsComboBox.clear()
        for x in range(1,32-self.net.prefixlen+1):                          # 0 .. number of network bits
            self.cidrbitsComboBox.addItem(str(x))
        self.cidrbitsComboBox.setMaxVisibleItems(self.maskComboBox.count())
        self.cidrbitsComboBox.setCurrentIndex(self.cidrmaskComboBox.currentIndex())

        #update max routes
        self.maxroutesComboBox.clear()
        for x in range(1,self.cidrbitsComboBox.count()+1):  #always same # of entries as cidrbits list
            self.maxroutesComboBox.addItem(str(2**x))
        self.maxroutesComboBox.setMaxVisibleItems(self.maxroutesComboBox.count())
        self.maxroutesComboBox.setCurrentIndex(self.cidrmaskComboBox.currentIndex())

        self._updateAll()

    def _updateUsage(self):
        self.usageTextEdit.clear()
        bIP = '{:032b}'.format(int(ipaddress.IPv4Address(self.addrComboBox.currentText())))
        #debug ('bIP' , bIP )
        #html_bits = bIP[0:self.maskComboBox.currentIndex()+1]
        html_bits = bIP[0:self.net.prefixlen]


        cidrBits = int(self.cidrbitsComboBox.currentText())
        openBits=32-cidrBits-len(html_bits)

        debug ('html_bits', html_bits,cidrBits, openBits)

        html = '{}{}{}'.format(html_bits, 'c'*cidrBits, 'x'*openBits)
        #debug ('html',html)
        html = re.sub('(.{8})(?!$)', r'\1.', html) #insert a '.' every 8 chars
        #debug ('html',html)
        #color the pieces
        html = re.sub('(c+)', r'<font color="#{}">\1</font>'.format(themes[themeName][C_COLOR]),html) #color n teal
        html = re.sub('(x+)', r'<font color="#{}">\1</font>'.format(themes[themeName][X_COLOR]),html) #color s gray


        self.usageTextEdit.clear()
        self.usageTextEdit.setText(html)

    def _updateAddrBlockRange(self):
        prefixlen = 32 -self.maskComboBox.currentIndex()
        debug ('_updateAddrBlockRange mask:', prefixlen)
        net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), str(prefixlen)), strict=False)
        addr = IP2Int(str(net.netmask)) ^ 0xFFFFFFFF    #xor
        addr = addr | IP2Int (str(net.network_address))
        self.addrblockLineEdit.setPlainText( str(net.network_address) + ' - ' + Int2IP(addr) )


    def _updateTable(self):
        debug ('_updateTable')
        mask = 32 - self.maskComboBox.currentIndex()
        net = ipaddress.ip_network('{}/{}'.format(self.addrComboBox.currentText(), str(mask)), strict=False)
        subnetbits = int(self.cidrbitsComboBox.currentText())

        newprefix = mask + subnetbits
        debug ('newprefix:',newprefix)
        rows = int(self.maxroutesComboBox.currentText())

        r = 0
        tableList = list(net.subnets(new_prefix=newprefix))
        tableLen = len(tableList)

        if (tableLen > 1024):
            buttonReply = QMessageBox.question(self, 'Large Table', 'The subnet table has '+str(tableLen)+' entries\n Continue?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.No:
                self.resultsTable.setRowCount(0)
                return
            else:
                debug('Yes clicked.')

        self._clearTable(rows)

        for n in tableList:

            item =  QTableWidgetItem(str(n.network_address))
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.resultsTable.setItem(r, 0,item)

            if (newprefix == 32):
                item = QTableWidgetItem(str(n))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.resultsTable.setItem(r, 1, item)
            else:
                item = QTableWidgetItem(str(n.network_address) + ' - ' + str(n[-2]))
                item.setTextAlignment(QtCore.Qt.AlignCenter)
                self.resultsTable.setItem(r, 1, item)

            self.resultsTable.resizeRowToContents(r)
            r += 1

        self.resultsTable.resizeColumnsToContents()
        self.resultsTable.resizeRowsToContents()


    def _clearTable(self, rows):
        self.resultsTable.setRowCount(rows)

    def _updateAll(self):
        self._updateAddrBlockRange()
        self._updateUsage()
        self._updateTable()


class MyTabWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()
        self.tabs.resize(300, 200)

        # Add tabs
        self.tabSubnets = MySubnetsTab(self)
        self.tabs.addTab(self.tabSubnets,'Subnets')

        self.tabVLSM = MyVLSMTab(self)
        self.tabs.addTab(self.tabVLSM,'VLSM')

        self.tabCIDR = MyCIDRTab(self)
        self.tabs.addTab(self.tabCIDR,'CIDR')

        self.tabIPv6 = MyIPv6Tab(self)
        self.tabs.addTab(self.tabIPv6,'IPv6')

        self.tabClasses = MyClassesTab(self)
        self.tabs.addTab(self.tabClasses,'Classes')

        self.tabConversions = MyConversionsTab(self)
        self.tabs.addTab(self.tabConversions,'Conversions')

        self.tabs.setCurrentIndex(1)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        print (self.tabSubnets.styleSheet())

        debug ('init complete\n--------------------------------------------------\n')
        debug ('')

#-----------------
# global functions
#-----------------

def ipValid(ip):
    return re.match(r'^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$', ip)

def ipv6Valid(ip):
    #print ('ipaddr',ip)
    match = re.search(r'^([a-fA-F0-9:]+)[\/ ]?',ip)
    if match:
        #print ('ipaddr', match.group(1))
        ip = match.group(1)
    else:
        return

    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False

def IP2Int(ip):
    o = [int(x) for x in ip.split('.')]
    res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
    return res

def Int2IP(ipnum):
    o1 = int(ipnum / 16777216) % 256
    o2 = int(ipnum / 65536) % 256
    o3 = int(ipnum / 256) % 256
    o4 = int(ipnum) % 256
    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()

def Int2HexIP(ipnum):
    o1 = format( int(ipnum / 16777216) % 256, '02x')
    o2 = format( int(ipnum / 65536) % 256, '02x')
    o3 = format( int(ipnum / 256) % 256, '02x')
    o4 = format( int(ipnum) % 256, '02x')
    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()

def wildcard_conversion(subnet):
    wildcard = []
    for x in subnet.split('.'):
        component = 255 - int(x)
        wildcard.append(str(component))
    wildcard = '.'.join(wildcard)
    return wildcard

def getBits(addr, mask):

    if (ipValid(addr)):
        bIP = '{:032b}'.format( int(ipaddress.IPv4Address(addr)) )

        if (bIP[:1] == '0'):
            netBits=8
            classBits=1
        elif (bIP[:2] == '10'):
            netBits=16
            classBits=2
        elif (bIP[:3] == '110'):
            netBits=24
            classBits=3
        elif (bIP[:3] == '111'):
            netBits=24
            classBits=4

        #mask is optional, if not given use mask for the appropriate subnet class
        if (mask > 0):
            subnetBits = mask
            delta = subnetBits - netBits
            if ( delta <= 0): # steal bits from class
                netBits = netBits + delta

            subnetBits = abs(delta)
        else:
            subnetBits = 0
            hostBits = 31-netBits

        hostBits = 32-subnetBits-netBits

        debug (f'c={classBits} n={netBits} s={subnetBits} h={hostBits}')
        return classBits, netBits, subnetBits, hostBits

    else:
        return None, None, None, None

def saveSettings(top,left,width,height,tab,darkMode):
    config = configparser.ConfigParser()

    config.read(iniFile)

    config.set('main','top',str(top))
    config.set('main','left',str(left))
    config.set('main','width',str(width))
    config.set('main','height',str(height))
    config.set('main','tab',str(tab))

    if darkMode:
        config.set('main','dark','True')
    else:
        config.set('main','dark','False')

    with open(iniFile, 'w') as f:
        config.write(f)

def getSettings():
    config = configparser.ConfigParser()

    width = 620
    height = 885
    left = 90
    top = 50
    tab = 0
    darkMode = True    #local var

    if (os.path.exists(iniFile)):
        config.read(iniFile)
        top      = config.getint('main','top')
        left     = config.getint('main','left')
        width    = config.getint('main','width')
        height   = config.getint('main','height')
        tab      = config.getint('main','tab')
        darkMode = config.getboolean('main','dark')
    else:
        config.add_section('main')
        config.set('main','top',str(top))
        config.set('main','left',str(left))
        config.set('main','width',str(width))
        config.set('main','height',str(height))
        config.set('main','tab',str(tab))
        if darkMode:
            config.set('main','dark','True')
        else:
            config.set('main','dark','False')

        with open(iniFile, 'w') as f:
            config.write(f)

    return top,left,width,height,tab,darkMode
    
def getMonospaceFont():
    preferred = ['Consolas', 'DejaVu Sans Mono', 'Monospace', 'Lucida Console', 'Monaco']
    for name in preferred:
        font = QFont(name)
        if QFontInfo(font).fixedPitch():
            #print ('Preferred monospace font: %r', font.toString())
            return font

    font = QFont()
    font.setStyleHint(QFont().Monospace)
    font.setFamily('monospace')
    debug ('Using fallback monospace font: %r', font.toString())
    return font

    
def debug(*args, **kwargs):
    if (gDebug):
        print (*args, **kwargs)

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = App()
    app.exec_()
    sys.exit()
