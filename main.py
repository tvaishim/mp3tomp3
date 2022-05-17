import sys
from math import ceil
import pathlib
import subprocess

import abookform

from PyQt5 import QtWidgets, QtCore, QtGui


class ThreadConvert(QtCore.QThread):
    signal_info = QtCore.pyqtSignal(str)
    signal_start = QtCore.pyqtSignal(str)
    signal_finish = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(ThreadConvert, self).__init__()
        self.app = parent

    def run(self):
        self.signal_start.emit(f"Начало...")

        filename = self.app.main_window.ui.lineEdit_2.text()

        # Объединение
        # self.signal_info.emit(f"Объединение...")
        path = pathlib.PurePath(self.app.main_window.ui.lineEdit_4.text(), "*.mp3")
        dire = path.parent
        file = path.name
        file_concat = str(pathlib.PurePath(dire, "concat.txt"))

        with open(file_concat, 'w') as f:
            for local_file in pathlib.Path(dire).glob(file):
                f.write(f"file '{str(local_file.name)}'\n")

        cmd = f'ffmpeg.exe -f concat -safe 0 -i "{file_concat}" -c copy "{filename}"'
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                stderr = stderr.decode('utf-8', 'replace')
                msgs = stderr.strip().split('\n')
                msg = msgs[-1]
                raise Exception(msg)
        except Exception as e:
            self.signal_info.emit(str(e))
            return

        # Разбивка на сегменты
        # self.signal_info.emit(f"Разбивка на сегменты...")
        if self.app.main_window.ui.checkBox.isChecked():
            seg_size = int(self.app.main_window.ui.lineEdit_3.text()) * 60
            if seg_size:
                path = pathlib.PurePath(filename)
                result_filename = str(path.with_stem(f"{path.stem}_%03d"))

                cmd = f'ffmpeg.exe -i "{filename}" -f segment -segment_time {seg_size} -c copy "{result_filename}"'
                # print(cmd)
                try:
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if p.returncode != 0:
                        stderr = stderr.decode('utf-8', 'replace')
                        msgs = stderr.strip().split('\n')
                        msg = msgs[-1]
                        raise Exception(msg)
                except Exception as e:
                    self.signal_info.emit(str(e))
                    return

                try:
                    pathlib.Path(filename).unlink()
                except Exception as e:
                    self.signal_info.emit(str(e))
                    return

        self.signal_finish.emit(f"Конвертация выполнена.")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent):
        super(MainWindow, self).__init__()
        self.app = parent
        self.ui = abookform.Ui_MainWindow()
        self.ui.setupUi(self)

        self.setFixedSize(self.width(), self.height())
        self.ui.lineEdit_3.setValidator(QtGui.QIntValidator(1, 1000))
        self.ui.lineEdit_3.setText("5")
        self.ui.checkBox.setChecked(True)

        self.ui.pushButton.clicked.connect(self.btn_click)
        self.ui.pushButton_2.clicked.connect(self.btn2_click)
        self.ui.pushButton_3.clicked.connect(self.btn3_click)

    def btn_click(self):
        if self.ui.lineEdit_2.text() and self.ui.lineEdit_4.text():
            if not self.app.thread_convert.isRunning():
                self.app.thread_convert.start()
        else:
            QtWidgets.QMessageBox.information(self, "Ошибка",
                                              "Не выбраны пути файлов!",
                                              buttons=QtWidgets.QMessageBox.Ok,
                                              defaultButton=QtWidgets.QMessageBox.Ok)

    def btn2_click(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(self, "Выбор имени сохранения", self.ui.lineEdit_2.text(), "mp3 audio file (*.mp3)")[0]
        if fn:
            self.ui.lineEdit_2.setText(fn)

    def btn3_click(self):
        fn = QtWidgets.QFileDialog.getExistingDirectory(self, "Выбор каталога с аудиокнигой", self.ui.lineEdit_4.text())
        if fn:
            self.ui.lineEdit_4.setText(fn)


class MainApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super(MainApp, self).__init__(argv)
        self.main_window = MainWindow(self)
        self.main_window.show()
        self.mutex = QtCore.QMutex()
        self.thread_convert = ThreadConvert(self)
        self.thread_convert.signal_info.connect(self.convert_info)
        self.thread_convert.signal_start.connect(self.convert_start)
        self.thread_convert.signal_finish.connect(self.convert_finish)

    def convert_start(self, info_text):
        self.main_window.ui.pushButton.setStyleSheet("QPushButton {background-color: #ff8080}")

    def convert_info(self, info_text):
        QtWidgets.QMessageBox.information(self.main_window, "Ошибка",
                                          info_text,
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)

    def convert_finish(self, info_text):
        self.main_window.ui.pushButton.setStyleSheet("background-color: light gray")
        self.main_window.ui.lineEdit_2.setText("")
        self.main_window.ui.lineEdit_4.setText("")
        QtWidgets.QMessageBox.information(self.main_window, "Выполнено",
                                          info_text,
                                          buttons=QtWidgets.QMessageBox.Ok,
                                          defaultButton=QtWidgets.QMessageBox.Ok)


if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec())
