#!/usr/bin/env python3

# Input method problem may happen
# https://stackoverflow.com/questions/50077228/cant-use-fcitx-with-self-written-qt-app

import sys, os
import json

from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, \
    QMenu, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QIcon


class Data:
    def __init__(self):
        self.path = os.path.join(os.getenv("HOME"), '.local/share/Reminder/')
        self.data_fn = 'data.json'
        self.fn = os.path.join(self.path, self.data_fn)
        self.raw_items = []
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        if not os.path.exists(self.fn):
            open(self.fn, 'a').close()
        self.load()

    def load(self):
        with open(self.fn, 'r') as f:
            if f.read().strip() != '':
                f.seek(0)
                self.raw_items = json.load(f)

    def dump(self):
        with open(self.fn, 'w') as f:
            json.dump(self.raw_items, f, ensure_ascii=False, indent=4)

    def add_item(self, item):
        self.raw_items.append(item)
        self.dump()

    def add_mark(self, item_key, log_info):
        for i in self.raw_items:
            if i[0] == item_key:
                i[1]['Log'].append(log_info)
        self.dump()

    def delete_item(self, item_key):
        self.raw_items = [x for x in self.raw_items if x[0]!=item_key]
        self.dump()

    def delete_mark(self, item_key):
        for i in self.raw_items:
            if i[0] == item_key:
                if len(i[1]['Log']) == 1:
                    self.delete_item(item_key)
                else:
                    i[1]['Log'] = i[1]['Log'][:-1]
                self.dump()


class App:
    def __init__(self):

        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.tray_icon = QSystemTrayIcon(QIcon("flower1.png"), self.app)
        self.data = Data()
        self.menu_f = [
            ('Separator', {}),
            ('Options', {
                'Add Item': self.add_item,
                'Help':     self.help_info,
                'Quit':     self.exit_app
            })
        ]
        self.main_menu = QMenu()
        self.tray_icon.setContextMenu(self.main_menu)
        self.refresh_menu()

        self.tray_icon.show()
        sys.exit(self.app.exec_())

    def refresh_menu(self):
        self.main_menu.clear()
        def day_back(y):
            last_t = QDateTime.fromString(y['Log'][-1][0], Qt.ISODate)
            dd = QDateTime.daysTo(last_t, QDateTime.currentDateTime())
            if dd == 0:
                return "今天刚刚"
            else:
                return str(dd)+"天前"
        def item_menu(x):
            return {
                'Mark': lambda _:self.add_mark(x),
                'Erase': lambda _:self.delete_mark(x),
                'Delete': lambda _: self.delete_item(x)
            }
        items = [("《%s》%s读过"%(x, day_back(y)), item_menu(x)) for x,y in self.data.raw_items]
        m = items + self.menu_f

        for k, v in m:
            if k == 'Separator':
                self.main_menu.addSeparator()
            else:
                if not v:
                    self.main_menu.addAction(k)
                else:
                    k_menu = self.main_menu.addMenu(k)
                    for kk, vv in v.items():
                        kk_menu = k_menu.addAction(kk)
                        kk_menu.triggered.connect(vv)

    @staticmethod
    def help_info():
        QMessageBox.about(None, "Help", "Help yourself.")

    @staticmethod
    def log_gen(tag):
        now = QDateTime.currentDateTime()
        log = (now.toString(Qt.ISODate), tag)
        return log

    def add_item(self):
        qin = QInputDialog()
        qin.setAttribute(Qt.WA_InputMethodEnabled)      # critical
        text, ok = qin.getText(None, "Add item", "New Item", QLineEdit.Normal, "Key/Type")
        if ok: print(text)
        else: return
        text_s = text.split('/')
        if len(text_s) != 2:
            QMessageBox.warning(None, "Warning", "Format not accepted.")
            self.add_item()
            return
        elif text_s[1] != 'BOOK':
            QMessageBox.warning(None, "Warning", "Type not accepted. ('BOOK' now are accepted)")
            self.add_item()
            return
        elif text_s[0] in [x for x,y in self.data.raw_items]:
            QMessageBox.warning(None, "Warning", "\"%s\" is already in list." % (text_s[0]))
            self.add_item()
            return
        else:
            self.data.add_item (
                [text_s[0], {'Type': text_s[1], 'Log': [self.log_gen('Add')]}]
            )
            self.refresh_menu()
        pass

    def add_mark(self, item_key):
        self.data.add_mark(item_key, self.log_gen('Mark'))
        self.refresh_menu()

    def delete_item(self, item_key):
        reply = QMessageBox.question(None, 'Message', 'You are deleting the item "%s". Are you sure?' % (item_key), QMessageBox.Yes, QMessageBox.No)
        if reply:
            self.data.delete_item(item_key)
            self.refresh_menu()
        pass

    def delete_mark(self, item_key):
        self.data.delete_mark(item_key)
        self.refresh_menu()
        pass

    def exit_app(self):
        self.app.exit(0)


if __name__ == "__main__":
    test = App()
