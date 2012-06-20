#!/usr/bin/env python

# NULL-free shellcode encoder for little-endian MIPS CPUs.
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

import struct
import sys
import random
import base64

class Encoder(object):
    DECODER_INIT = '26400801'.decode('hex') # xor $t0, $t0, $t0
    DECODER_SET_T3 = 0x250B0000 # addiu $t3, $t0, ????
    DECODER_INC_T3 = 0x256B0000 # addiu $t3, $t3, ????
    DECODER = ('04010825' # addiu $t0, $t0, 0x0104
               '04020D31' # andi $t5, $t0, 0x0204
               '70FF0825' # addiu $t0, $t0, 0xFF70
               'FEFF1105' # bgezal $t0, 0xFFFE
               '24801002' # nop
               '38FFE927' # addiu $t1, $ra, 0xFF38
               '21586901' # addu $t3, $t3, $t1
               '04016C8D' # lw $t4, 0x0104($t3)
               '04012E8D' # lw $t6, 0x0104($t1)
               '2670CC01' # xor $t6, $t6, $t4
               '04012EAD' # sw $t6, 0x0104($t1)
               '21482D01' # addu $t1, $t1, $t5
               '23786901' # subu $t7, $t3, $t1
               'FAFFE01D' # bgtz $t7, 0xFFFA
               '2621E003' # xor $a0, $ra, $0
               '41040524' # addiu $a1, $0, 0x0441
               '0180A630' # andi $a2, $a1, 0x8001
               '33100224' # addiu $v0, $0, __NR_cacheflush
               '0C010101' # syscall
               '24801002' # nop
              ).decode('hex')

    BAD_BYTES = [0x00, 0x18]

    def __init__(self, unencoded=''):
        assert len(unencoded)%4 == 0
        self.unencoded = unencoded

        assert self.check(self.DECODER_INIT + self.DECODER)

    def encode(self):
        self.xor = ''
        self.encoded = ''
        self.choose_xor()
        self.create_decoder()
        self.apply_xor()
        assert self.check(self.encoded)
        return self.encoded

    def choose_xor(self):
        candidates = [[x for x in range(256) if x not in self.BAD_BYTES]]*4

        for index, byte in enumerate(self.unencoded):
            for bad in self.BAD_BYTES:
                eliminate = bad^ord(byte)
                if eliminate in candidates[index&3]:
                    candidates[index&3].remove(eliminate)

        self.xor = ''
        for clist in candidates:
            if not len(clist):
                sys.stderr.write('No XOR possible!\n')
                sys.exit(1)
            self.xor += chr(random.choice(clist))

    def create_decoder(self):
        self.encoded += self.DECODER_INIT
        for index, piece in enumerate(self.length_sum()):
            if not index:
                instruction = self.DECODER_SET_T3
            else:
                instruction = self.DECODER_INC_T3
            instruction |= piece & 0xFFFF
            self.encoded += struct.pack('<I', instruction)
        self.encoded += self.DECODER

    def length_sum(self):
        length = len(self.unencoded)

        for sum1 in range(0x0101,0x7FFF):
            sum2 = length-sum1
            if self.check(struct.pack('hh', sum1, sum2)):
                break

        assert sum1+sum2 == length
        assert self.check(struct.pack('hh', sum1, sum2))
        return (sum1, sum2)

    def apply_xor(self):
        for index, byte in enumerate(self.unencoded):
            self.encoded += chr(ord(byte) ^ ord(self.xor[index&3]))
        self.encoded += self.xor

    @classmethod
    def check(cls, code):
        return not any(ord(byte) in cls.BAD_BYTES for byte in code)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.stderr.write('Not enough arguments!\n')
        sys.exit(1)
    with open(sys.argv[1],'rb') as infile:
        unencoded = infile.read()
    encoded = Encoder(unencoded).encode()
    with open(sys.argv[2], 'w') as outfile:
        outfile.write(base64.encodestring(encoded))
