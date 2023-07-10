#
# Copyright (c) 2023 Analog Devices Inc.
#
# This file is part of libm2k
# (see http://www.github.com/analogdevicesinc/libm2k).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#
import libm2k

ctx=libm2k.m2kOpen()
ctx.calibrateADC()
ctx.calibrateDAC()

siggen=ctx.getAnalogOut()

#call buffer generator, returns sample rate and buffer
samp0,buffer0 = sine_buffer_generator(0,1000,0,0,0)
samp1,buffer1 = sine_buffer_generator(1,1000,0,0,0)

siggen.enableChannel(0, True)
siggen.enableChannel(1, True)

siggen.setSampleRate(0, samp0)
siggen.setSampleRate(1, samp1)

siggen.push([buffer0,buffer1])

print( " Turning off signal gen ")
siggen.stop()
libm2k.contextClose(ctx)