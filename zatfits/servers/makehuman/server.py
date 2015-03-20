#!/usr/bin/python

from socket import socket, gethostname, AF_INET, SOCK_STREAM
from select import select


class ZTServer:

    def __init__(self, port, verbose=False):
        self.verbose = verbose
        self.port = port
        self._received = []
        self._sockets = []
        self._listeningSock = None
        self.tosend = {}
        self.newListeningSocket()

    def newListeningSocket(self):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind((gethostname(), self.port))
        sock.listen(5)
        self._listeningSock = sock
        self._sockets.append(sock)
        if self.verbose is True:
            print('Creating new listening socket at %s %s' %
                  sock.getsockname())

    def _receive(self, sock):
        received = sock.recv(1024)
        if received == '':
            self._sockets.remove(sock)
            self.tosend[sock] = []
            if self.verbose is True:
                print('Removed sock %s %s' % sock.getpeername())
            sock.close()
        else:
            self._received.append((received, sock))

    def Received(self):
        r = self._received
        self._received = []
        return r

    def newConnection(self):
        client_sock, address = self._listeningSock.accept()
        self._sockets.append(client_sock)
        if self.verbose is True:
            print('New connection from %s %s' % (client_sock.getpeername()))

    def _write(self, msg, sock):
        sock.send(msg)
        if self.verbose is True:
            print('Sending %s bytes to %s' % (len(msg), sock))

    def Send(sock, msg):
        try:
            self.tosend[sock].append(msg)
        except:
            self.tosend[sock] = [msg]

    def Iterate(self):
        readable, writable, errored = select(self._sockets,
                                             self._sockets,
                                             [],
                                             1)

        for sock in readable:
            if sock is self._listeningSock:
                try:
                    self.newConnection()
                except Exception as e:
                    print('Error at new connection %s' % str(e))
            else:
                try:
                    self._receive(sock)
                except Exception as e:
                    print('Error while receiving %s' % str(e))

if __name__ == '__main__':

    s = ZTServer(9000, verbose=True)
    while True:
        s.Iterate()
        new_messages = s.Received()
        if new_messages:
            print new_messages
