from utils import THUer
import json
import socket
import threading
import time
import os
import sys
import signal
import logging
import logging.handlers
import traceback


class server:
    def __init__(self, port):
        self.last_login_time = 0
        self.port = port
        mydata = json.load(open('data.json'))
        self.thuer = THUer(mydata['username'], mydata['password'])
        self.hwlist = []
        self.hwinfo=''
        self.startup()
        self.run()

    def startup(self):
        self.thuer.login()
        self.last_login_time = time.time()
        print('login success @ %s' % time.ctime())
        self.hwlist = []
        self.hwinfo = ''
        for c in self.thuer.courselist:
            for h in c.homeworklist:
                self.hwlist.append(h)
        for c in self.thuer.courselist:
            for hh in c.handedhomeworklist:
                self.hwlist.append(hh)
        for id, h in enumerate(self.hwlist):
            self.hwinfo += '%d %s %s\n' % (id, h.parent.name, h.bt)

    def run(self):
        # 创建socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', self.port))
        s.listen(5)
        print('listening on port %d' % self.port)
        while True:
            conn, addr = s.accept()
            print('connected by', addr)
            t = threading.Thread(target=self.handle, args=(conn, addr))
            t.start()

    def handle(self, conn, addr):
        try:
            data = conn.recv(1024)
            data = data.decode('utf-8')
            print('data1:'+data)
            data2 = conn.recv(1024)
            data2 = data2.decode('utf-8')
            if self.last_login_time + 6 < time.time():
                self.startup()
            print('data2:'+data2)
            if data2 == 'hwinfo':
                self.send_hw_info(conn)
            elif data2.startswith('tj'):
                self.tjzy(conn, data2)
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            conn.close()

    def send_hw_info(self, conn):
        print('send hw info %s' % self.hwinfo)
        try:
            header = '''HTTP/1.1 200 OK\r\nContent-Type: text/plain;charset=UTF-8\r\n\r\n '''
            conn.sendall((header + self.hwinfo).encode('utf-8'))

        except Exception as e:
            print(e)
            traceback.print_exc()

    def tjzy(self, conn, data):
        a, b, c = data.split(' ')
        b = int(b)
        try:
            res = self.hwlist[b].handinafile(c)
            print('handing in %s' % c)
            if res:
                header = '''HTTP/1.1 200 OK\r\nContent-Type: text/plain;charset=UTF-8\r\n\r\n '''
                conn.sendall((header + res).encode('utf-8'))
                print(res)
        except Exception as e:
            print(e)
            traceback.print_exc()
        finally:
            self.startup()


def main():
    s = server(6835)


if __name__ == '__main__':
    main()
