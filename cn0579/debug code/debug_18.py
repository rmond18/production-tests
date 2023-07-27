#Debug: use m2k to retest sin_parameters
#added record feature to example python script
#boards current source should be souldered


# Copyright (C) 2021 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys

import matplotlib.pyplot as plt
from adi import cn0579

import sin_params
import numpy as np
import os.path
import time

# This function gets the serial number of the board from the command line arguments and print it.
def get_serial():
    print("\nSetting up serial number....")
    sn = sys.argv[1]

    # # Checking if serial number is valid
    # if len(sn) == 10 and sn.isdigit():
    #     print ("Serial number:", int(sn))
    # else:
    #     sys.exit('\nIncorrect serial number! Must be 10 digits.\nExample: 202205100001\n')
    
    return sn

def record_data(sn, channel, snr, thd, sinad, enob, sfdr, floor):
    file_exists = os.path.exists('de10_d18_report.csv')
    record = open("de10_d18_report.csv","a")
   
    if(file_exists==0):
        record.write("SN, Channel, SNR, THD, SINAD, ENOB, SFDR, FLOOR\n")
    record.write(str(sn) + "," + "Ch_" + str(channel) + "," + str(snr)+ "," + str(thd)+ "," + str(sinad)+ "," + str(enob)+ "," + str(sfdr)+"," + str(floor)+"\n")
    record.close()
    return


# This function initializes the context and set-up other parameters.
def init_my_adc(my_uri):
    

    my_adc = cn0579(uri=my_uri)
    my_adc.rx_buffer_size = 1024

    # Set Sample Rate. Options are 1ksps to 256ksps, 1k* power of 2.
    # Note that sample rate and power mode are not orthogonal - refer
    # to datasheet.
    my_adc.sampling_frequency = 256000

    # Choose a power mode:
    my_adc.power_mode = "FAST_MODE"
    # my_adc.power_mode = "MEDIAN_MODE"
    # my_adc.power_mode = "LOW_POWER_MODE"

    # Choose a filter type:
    my_adc.filter_type = "WIDEBAND"
    # my_adc.filter_type = "SINC5"

    # Choose output format:
    # my_adc.rx_output_type = "raw"
    my_adc.rx_output_type = "SI"
    return my_adc

# Switches current source on/off. A is the channel number, while mode is on or off. Mode = 1 is on and the opposite for off.
def csource_switch(my_cn0579, a, mode):
    if mode == 1:
        if a == 0:
            my_cn0579.CC_CH0 = 1
        elif a == 1:
            my_cn0579.CC_CH1 = 1
        elif a == 2:
            my_cn0579.CC_CH2 = 1
        else:
            my_cn0579.CC_CH3 = 1
    else:
        if a == 0:
            my_cn0579.CC_CH0 = 0
        elif a == 1:
            my_cn0579.CC_CH1 = 0
        elif a == 2:
            my_cn0579.CC_CH2 = 0
        else:
            my_cn0579.CC_CH3 = 0
    
    # time.sleep(3)
    return

print("CN0579 Production Test \nTest script starting....")

# set serial number for the board on test
sn = get_serial()

# Optionally passs URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[2] if len(sys.argv) >= 3 else "ip:analog.local"
print("\nConnecting with CN0579 context at: " + str(my_uri))

# Set Shift Voltage:
vshift=58478
def set_DAC(vshift,z,my_adc):
    d_code = vshift
    time.sleep(2)
    if z == 0:
        my_adc.shift_voltage0 = d_code
        print("Channel 0 DAC: %s" % d_code)
    elif z == 1:
        my_adc.shift_voltage1 = d_code
        print("Channel 1 DAC: %s" % d_code)
    elif z == 2:
        my_adc.shift_voltage2 = d_code
        print("Channel 2 DAC: %s" % d_code)
    else:
        my_adc.shift_voltage3 = d_code
        print("Channel 3 DAC: %s" % d_code)

    time.sleep(2)
    return 

for ch in range (0,4):
    my_adc = init_my_adc(my_uri)
    input("\nShort channel %s.Enter to continue" %ch)
    csource_switch(my_adc, ch, 1)

    set_DAC(vshift,ch, my_adc)
    # Verify settings:
    print("Power Mode: ", my_adc.power_mode)
    print("Sampling Frequency: ", my_adc.sampling_frequency)
    print("Filter Type: ", my_adc.filter_type)
    print("Enabled Channels: ", my_adc.rx_enabled_channels)
    print("Ch0 Shift Voltage: ", my_adc.shift_voltage0)
    print("Ch1 Shift Voltage: ", my_adc.shift_voltage1)
    print("Ch2 Shift Voltage: ", my_adc.shift_voltage2)
    print("Ch3 Shift Voltage: ", my_adc.shift_voltage3)
    
    input("\nTurn on M2K on Channel %s.Enter to continue" %ch)
    
    plt.clf()
    data = my_adc.rx()
    # for ch in [1]:
    plt.plot(range(0, len(data[0])), data[ch], label="voltage" + str(ch))
    plt.xlabel("Data Point")
    if my_adc.rx_output_type == "SI":
        plt.ylabel("Millivolts")
    else:
        plt.ylabel("ADC counts")
    plt.legend(
        bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
        loc="lower left",
        ncol=4,
        mode="expand",
        borderaxespad=0.0,
    )
    #plt.pause(0.01)
    plt.show() 


    # for ch in my_adc.rx_enabled_channels:
    # for ch in [1]:
    parameters = sin_params.sin_params(data[ch])
    snr = parameters[1]
    thd = parameters[2]
    sinad = parameters[3]
    enob = parameters[4]
    sfdr = parameters[5]
    floor = parameters[6]
    print("\nChannel " + str(ch))
    print("SNR = "+ str(snr))
    print("THD = "+ str(thd))
    print("SINAD = "+ str(sinad))
    print("ENOB = "+ str(enob))
    print("SFDR = "+ str(sfdr))
    print("FLOOR = "+ str(floor))

    record_data(sn, ch, snr, thd, sinad, enob, sfdr, floor)

    input("\nTurn off M2K.Enter to continue")

    csource_switch(my_adc, ch, 0)
        
    # Set Shift Voltage:
    my_adc.shift_voltage0=0
    my_adc.shift_voltage1=0
    my_adc.shift_voltage2=0
    my_adc.shift_voltage3=0
    
    del my_adc

