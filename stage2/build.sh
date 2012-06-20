#!/bin/sh

# This is just a crude script. The build process is not complex, I just don't
# like typing. :)

PREFIX=mipsel-linux
$PREFIX-gcc -nostdlib -DATTEMPT_STACK_REPAIR -o stage2.elf stage2.S &&
$PREFIX-objcopy -O binary --only-section=.text stage2.elf stage2.bin &&
./encoder.py stage2.bin stage2.b64 &&
cat stage2.b64
