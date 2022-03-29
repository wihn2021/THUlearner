from utils import THUer, homework
import json
import tkinter as tk
import sys
import requests

globalhomeworklist = []  # 用于存放所有作业


def main(argv=[]):
    if len(argv) == 0:
        print('Usage: python3 main.py filepath')
        sys.exit(1)
    m = handle(argv[0])


class handle():
    def __init__(self, path):
        self.fp = path
        self.p = tk.Tk()
        self.homeworklist = tk.Listbox(self.p, width=40)
        # 创建一个文本框，文字是“xxxttt”
        r = requests.get('http://localhost:6835/', data='hwinfo')
        for line in r.text.split('\n'):
            if line:
                self.homeworklist.insert(tk.END, line)
        self.homeworklist.bind('<Double-Button-1>', self.jzy)
        self.homeworklist.grid(row=0, column=0)
        self.homeworklist.pack()
        self.p.title('Homework')
        # set position
        self.p.geometry('+600+300')
        self.p.resizable(True, True)
        self.p.mainloop()

    def testcommand(self, *args, **kwargs):
        print('test' + str(args) + str(kwargs))
        print(self.homeworklist.curselection())

    def jzy(self, *args, **kwargs):
        data = 'tj %d %s' % (self.homeworklist.curselection()[0], self.fp)
        j = requests.get('http://localhost:6835/', data=data.encode('utf-8'))
        print(j.text)


if __name__ == '__main__':
    main(sys.argv[1:])
