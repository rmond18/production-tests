# Copyright (C) 2023 Analog Devices, Inc.
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
import sine_gen
import voltmeter
import matplotlib.pyplot as plt
from adi import cn0579
import sin_params
import numpy as np
# from save_for_pscope import save_for_pscope
import os.path
import time

def init_my_adc():
    # Optionally passs URI as command line argument,
    # else use default ip:analog.local
    my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
    print("\nuri: " + str(my_uri))

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
    
def get_params(sn, Channel, att):
    parameters = sin_params.sin_params(data[Channel])
    snr = parameters[1]
    thd = parameters[2]
    sinad = parameters[3]
    enob = parameters[4]
    sfdr = parameters[5]
    floor = parameters[6]
    print("\nChannel " + str(Channel))
    print("SNR = "+ str(snr))
    print("THD = "+ str(thd))
    print("SINAD = "+ str(sinad))
    print("ENOB = "+ str(enob))
    print("SFDR = "+ str(sfdr))
    print("FLOOR = "+ str(floor))
    
    if att==1:
        snr_lim= 50
    else: #att==100
        snr_lim= 35
    
    status=0

    if snr > snr_lim:
        print("SNR test PASS")
        status+=1
    else:
        print("SNR test FAIL")
        status-=1
        
    if thd < -35:
        print("THD test PASS")
        status+=1
    else:
        print("THD test FAIL")
        status-=1
           
    if status==2:
        stat="PASS"
    else:
        stat="FAIL"
    file_exists = os.path.exists('cn0579_report.csv')
    record = open("cn0579_report.csv","a")
   
    if(file_exists==0):
        record.write("SN, Channel, Attenuation, SNR, THD, SINAD, ENOB, SFDR, FLOOR, PASS/FAIL\n")
    record.write(str(sn) + "," + "Ch_" + str(Channel) + "," +str(att)+ "," + str(snr)+ "," + str(thd)+ "," + str(sinad)+ "," + str(enob)+ "," + str(sfdr)+"," + str(floor)+"," + str(stat)+"\n")
    record.close()
     
start = time.time()   
# set serial number for the board on test
sn = input("Enter serial number:")

channel=[0,1,2,3]
# channel = int(input("Pick channel[0,1,2,3]:"))
# prompt to connect to correct channel
for i in channel:
    
    my_adc= init_my_adc()
    
    print("\nRemove header on other channel.\nShort header on test jig for Channel", i)
    input("Press enter to continue.")
    # switch to full swing
    input("\nTurn test jig switch to full amplitude. Press enter to continue.")
    
    # turn on current source
    print("Turning on current source for Channel", i)
    if i==0:
        my_adc.CC_CH0=1
        my_adc.CC_CH1=0
        my_adc.CC_CH2=0
        my_adc.CC_CH3=0
    elif i==1:
        my_adc.CC_CH0=0
        my_adc.CC_CH1=1
        my_adc.CC_CH2=0
        my_adc.CC_CH3=0
    elif i==2:
        my_adc.CC_CH0=0
        my_adc.CC_CH1=0
        my_adc.CC_CH2=1
        my_adc.CC_CH3=0
    elif i==3:
        my_adc.CC_CH0=0
        my_adc.CC_CH1=0
        my_adc.CC_CH2=0
        my_adc.CC_CH3=1
        
    print("Current source CH0:", my_adc.CC_CH0)
    print("Current source CH1:", my_adc.CC_CH1)
    print("Current source CH2:", my_adc.CC_CH2)
    print("Current source CH3:", my_adc.CC_CH3) 
    print("Voltage reading for Channel", i)
    
    # m2k voltmeter to verify current source working
    voltage=voltmeter.read()
    
    # # compute corresponding value for vshift and DAC code
    # vshift= (voltage*0.3+2.5)/(1.3)
    # vshift_code= int((vshift/5)*65536)
    
    # run offset calibration, set Shift Voltage:
    vshift_code= 58478
    if i==0:
        my_adc.shift_voltage0 = vshift_code
        my_adc.shift_voltage1 = 0
        my_adc.shift_voltage2 = 0
        my_adc.shift_voltage3 = 0
    elif i==1:
        my_adc.shift_voltage0 = 0
        my_adc.shift_voltage1 = vshift_code
        my_adc.shift_voltage2 = 0
        my_adc.shift_voltage3 = 0
    elif i==2:
        my_adc.shift_voltage0 = 0
        my_adc.shift_voltage1 = 0
        my_adc.shift_voltage2 = vshift_code
        my_adc.shift_voltage3 = 0
    elif i==3:
        my_adc.shift_voltage0 = 0
        my_adc.shift_voltage1 = 0
        my_adc.shift_voltage2 = 0
        my_adc.shift_voltage3 = vshift_code
        
    # turn on m2k signal gen
    sine_gen.main()
    
    
    plt.clf()
    data = my_adc.rx()
    plt.plot(range(0, len(data[0])), data[i], label="voltage" + str(i))
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
    plt.show() 
    
    # run sin_params + record data
    print("Reading parameters...")
    att=1
    get_params(sn,i,att)
    
 

    # switch to 100:1 attenuation
    input("\nTurn test jig switch to 100:1 attenuation. Press enter to continue.")
    my_adc= init_my_adc()
    
    plt.clf()
    data = my_adc.rx()
    plt.plot(range(0, len(data[0])), data[i], label="voltage" + str(i))
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
    plt.show() 
    # run sin_params + record data
    print("Reading parameters...")
    att=100
    get_params(sn,i,att)
    
    
   
        
    #turn off m2k signal gen
    sine_gen.stop()

    #repeat for next 3 channels
#shutdown device
print("Test took " + str(time.time() - start) + " seconds.")