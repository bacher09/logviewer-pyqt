#!/usr/bin/env python
import sys, signal, datetime
from PyQt4 import QtCore, QtGui 
from log_show_ui import Ui_MainWindow
import logs_parse

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class TableLog(QtCore.QAbstractTableModel):
    names =  ['Date and Time', 'Message Type', 'Message', 'Path','Number of line' ]
    obj_order = ('datetime_str','type_text','message','path','num_line')
    column_len = len(obj_order)
    obj_data = []
    obj_filtered_data = []
    filter_fun = None
    sort_funs = {'datetime_str': lambda x: x.datetime,
                 'type_text': lambda x: x.type_mes, # Sorting not by Alphavit
                 'message': lambda x: x.message,
                 'path': lambda x: x.path,
                 'num_line': lambda x: x.num_line
                 } 
    def __init__(self, parent = None):
        self = super(TableLog, self).__init__(parent)
    
    def updateData(self, data):
        self.layoutAboutToBeChanged.emit()
        self.obj_data[:] = data
        self.layoutChanged.emit()
    
    def updateDataByIterator(self, iterator):
        self.updateData([ i for i in iterator])
    
    def updateFilter(self):
        self.layoutAboutToBeChanged.emit()
        if self.filter_fun:
            self.obj_filtered_data = filter(self.filter_fun, self.obj_data)
        self.layoutChanged.emit()
    
    def changeFilter(self, filter_fun):
        self.filter_fun = filter_fun
        self.updateFilter()
    
    @property
    def object_data(self):
        if self.filter_fun==None:
            return self.obj_data
        elif not self.obj_filtered_data:
            self.obj_filtered_data = None
        return self.obj_filtered_data
    
    @object_data.setter
    def object_data(self, value):
        if self.filter_fun:
            self.obj_filtered_data = value
        else:
            self.obj_data = value
    
    def rowCount(self, parrent=None):
        try:
            return len(self.object_data)
        except TypeError:
            return 0
    
    def columnCount(self, parrent=None):
        return self.column_len
    
    def headerData(self, section=None, orient=None, role=None):
        if section<5 and role<5 and QtCore.Qt.Horizontal == orient:
            return QtCore.QVariant(self.names[section])
        return super(TableLog, self).headerData(section, orient, role)
    
    def sort(self, column, order = QtCore.Qt.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        self.object_data = sorted(self.object_data, 
                              key = self.sort_funs[self.obj_order[column]],
                              reverse = (order !=QtCore.Qt.AscendingOrder))
        self.layoutChanged.emit()
    
    def data(self, index, role):
        if not index.isValid():
            return None
        elif role!=QtCore.Qt.DisplayRole:
            return None
        elif index.column()<self.column_len:
            return getattr(self.object_data[index.row()], \
                    self.obj_order[index.column()])
        return None

class Main(QtGui.QMainWindow, Ui_MainWindow):
    check_boxs = ['notify_type','notify_warn','notify_error', 'date_filter']
    datetime_edit = ['start_datetime','end_datetime']
    
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        self.action_Open.triggered.connect(self.fileOpen)
        self.logs_table_model = TableLog()
        self.logs_table.setModel(self.logs_table_model)
        for i in self.check_boxs:
            getattr(self,i).toggled.connect(self.changeFilter)
        for i in self.datetime_edit:
            getattr(self,i).dateTimeChanged.connect(self.changeFilter)
        self.search_input.textEdited.connect(self.changeFilter)
        now = datetime.datetime.now()
        self.start_datetime.setDateTime(QtCore.QDateTime(now.year, 
                                                         now.month, 
                                                         now.day, 
                                                         now.hour, 
                                                         now.minute, 
                                                         now.second 
                                        ))
                        
    
    def fileOpen(self):
        self.file_name = unicode(QtGui.QFileDialog.getOpenFileName(self,\
                                    "Open File"))
        self.logs_table_model.updateDataByIterator(logs_parse.read_log(self.file_name))
        self.logs_table.resizeColumnsToContents()
    
    def changeFilter(self):
        notify = self.notify_type.isChecked()
        warn = self.notify_warn.isChecked()
        error = self.notify_error.isChecked()
        message = self.search_input.text()
        datetime_activated = self.date_filter.isChecked()
        type_list = []
        datetime_start = None
        datetime_end = None
        if notify:
            type_list.append(logs_parse.WARN_TYPES['INFO'])
        if warn:
            type_list.append(logs_parse.WARN_TYPES['WARN'])
        if error:
            type_list.append(logs_parse.WARN_TYPES['ERROR'])
        if datetime_activated:
            datetime_start = self.start_datetime.dateTime().toPyDateTime()
            datetime_end = self.end_datetime.dateTime().toPyDateTime()
            
        self.logs_table_model.changeFilter( \
            logs_parse.closure_filter(startdate= datetime_start,
                                      enddate = datetime_end,
                                      types=type_list,
                                      message = message))

     
def main():
    def handler(signum, frame):
        print("Exiting")
        window.close()
    app = QtGui.QApplication(sys.argv)
    window = Main()
    window.show()
    signal.signal(signal.SIGINT, handler)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
