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
import m2k_siggen as sig_gen
import voltmeter
import matplotlib.pyplot as plt
from adi import cn0579
import sin_params
import numpy as np
# from save_for_pscope import save_for_pscope
import os.path
import time

sin_amp = 5                                     # Amplitude of the m2k input signal (10 Vpp)
sin_freq = 1000                                 # 1kHz input signal
sin_offset = 0                                  # DC offset of input signal
sin_phase = 0                                   # Phase for input signal
failed_tests = []                               # List for failed tests


# This function is to check if command line input is correct. Only one argument is needed (serial number of board being tested). If input is more than one argument, test code will exit.
def check_input():
    n = len(sys.argv)                           # Number of total arguments on command line
    if n != 2:
         sys.exit('\nIncorrect syntax! \nExample: python cn0579_prod_test.py 202205100001\n')
    return

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

def print_csource(my_cn0579):
    print("Current source CH0: %s" % my_cn0579.CC_CH0)
    print("Current source CH1: %s" % my_cn0579.CC_CH1)
    print("Current source CH2: %s" % my_cn0579.CC_CH2)
    print("Current source CH3: %s" % my_cn0579.CC_CH3)

    return

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
    
    time.sleep(3)
    print_csource(my_cn0579)
    return

def read_DC(libm2k_ctx):
    volt_reading = sig_gen.voltmeter(libm2k_ctx)
    time.sleep(2)
    if  (10.5 < volt_reading < 11.3):
            print("DC input: %s Volts\nDC input PASS" % volt_reading)
    else:
        print("DC input: %s Volts\nDC input FAILED" % volt_reading)
        failed_tests.append("Failed input DC check")
        
        # sys.exit('Failed input DC check\n')
    
    time.sleep(2)
    return volt_reading

def set_shift(vr):
    vshift = ((vr * 0.3) + 2.5) / 1.3
    time.sleep(2)
    print("Calculated Vshift: %s" % vshift)
    return vshift

def print_DAC(my_cn0579):
    print("Channel 0 DAC: %s" % my_cn0579.shift_voltage0)
    print("Channel 1 DAC: %s" % my_cn0579.shift_voltage1)
    print("Channel 2 DAC: %s" % my_cn0579.shift_voltage2)
    print("Channel 3 DAC: %s" % my_cn0579.shift_voltage3)

    return

def set_DAC(vshift, z, my_cn0579):
    d_code = (65536 * vshift) / 5
    time.sleep(2)
    if z == 0:
        my_cn0579.shift_voltage0 = d_code
        print("Channel 0 DAC: %s" % d_code)
    elif z == 1:
        my_cn0579.shift_voltage1 = d_code
        print("Channel 1 DAC: %s" % d_code)
    elif z == 2:
        my_cn0579.shift_voltage2 = d_code
        print("Channel 2 DAC: %s" % d_code)
    else:
        my_cn0579.shift_voltage3 = d_code
        print("Channel 3 DAC: %s" % d_code)

    time.sleep(2)
    print_DAC(my_cn0579)
    return 

def stop_all(libm2k_ctx, siggen, my_cn0579):
    print("Turning off current sources, reseting DAC settings, and closing all m2k and cn0579 context")
    sig_gen.m2k_close(libm2k_ctx, siggen)
    for x in range(0,4):
        csource_switch(my_cn0579, x, 0)
        set_DAC(0, x, my_cn0579)                                                                        # Set output of the DAC to 0
        

def plot_data(channel,data,my_cn0579):
    plt.clf()
    plt.plot(range(0, len(data[0])), data[channel], label="voltage" + str(channel))
    plt.xlabel("Data Point")
    if my_cn0579.rx_output_type == "SI":
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
    return

def check_limits(parameters, test):
    att= len(test)
    print("Test =%s" %test)
    if att<9:          # for full scale test
        snr_lim= 50
    else:               # for attenuated test
        snr_lim= 35
    
    status=0

    if parameters[1] > snr_lim:
        print("SNR test PASS")
        status+=1
    else:
        print("SNR test FAIL")
        status-=1
        
    if parameters[2] < -30:
        print("THD test PASS")
        status+=1
    else:
        print("THD test FAIL")
        status-=1
           
    if status==2:
        stat="PASS"
    else:
        stat="FAIL"
    return stat
    
def record_data(sn, channel, test, snr, thd, sinad, enob, sfdr, floor, status):
    file_exists = os.path.exists('new_cn0579_report.csv')
    record = open("new_cn0579_report.csv","a")
   
    if(file_exists==0):
        record.write("SN, Channel, Attenuation, SNR, THD, SINAD, ENOB, SFDR, FLOOR, PASS/FAIL\n")
    record.write(str(sn) + "," + "Ch_" + str(channel) + "," +str(test)+ "," + str(snr)+ "," + str(thd)+ "," + str(sinad)+ "," + str(enob)+ "," + str(sfdr)+"," + str(floor)+"," + str(status)+"\n")
    record.close()
    return

# def get_params(channel, my_cn0579, test, sn):
#     data = my_cn0579.rx()
#     print("data length = %s" %(len(data)))
#     time.sleep(2)
#     parameters = sin_params.sin_params(data[channel])
#     time.sleep(2)
#     snr = parameters[1]
#     thd = parameters[2]
#     sinad = parameters[3]
#     enob = parameters[4]
#     sfdr = parameters[5]
#     floor = parameters[6]
#     print("\nChannel " + str(channel))
#     print("SNR = "+ str(snr))
#     print("THD = "+ str(thd))
#     print("SINAD = "+ str(sinad))
#     print("ENOB = "+ str(enob))
#     print("SFDR = "+ str(sfdr))
#     print("FLOOR = "+ str(floor))
    
#     status= check_limits(parameters, test)
#     time.sleep(2)
#     record_data(sn, channel, test, snr, thd, sinad, enob, sfdr, floor, status)
    
#     time.sleep(2)
#     return data


def channel_tests(my_cn0579, test_type, x, sn):
    
    csource_switch(my_cn0579, x, 1)                                                  # Turns on current source for channel x
    libm2k_ctx = sig_gen.init_m2k()
    volt_reading = read_DC(libm2k_ctx)                                              # Read DC voltage of the input signal using the M2k voltmeter
    
    vshift = set_shift(volt_reading)                                                 # Compute for the Vshift
    set_DAC(vshift, x, my_cn0579)                                                    # Set output of the DAC to corresponding digital code of the Vshift
    
    siggen = sig_gen.main(libm2k_ctx, sin_freq, sin_amp, sin_offset, sin_phase)      # Turns on M2k output
    time.sleep(2)
    adc_data=[]
    print("len adc_data = %s" %(len(adc_data)))
    parameters=[]
    print("Init params length = %s" %(len(parameters)))
    # adc_data=get_params(x, my_cn0579, test_type, sn)                                     # Compute sinparams
    adc_data = my_cn0579.rx()
    print("data length = %s" %(len(adc_data)))
    time.sleep(2)
    # print(adc_data)
    parameters = sin_params.sin_params(adc_data[x])
    time.sleep(2)
    print("params length = %s" %(len(parameters)))
    print(parameters)
    snr = parameters[1]
    thd = parameters[2]
    sinad = parameters[3]
    enob = parameters[4]
    sfdr = parameters[5]
    floor = parameters[6]
    print("\nChannel " + str(x))
    print("SNR = "+ str(snr))
    print("THD = "+ str(thd))
    print("SINAD = "+ str(sinad))
    print("ENOB = "+ str(enob))
    print("SFDR = "+ str(sfdr))
    print("FLOOR = "+ str(floor))
    
    status= check_limits(parameters, test_type)
    time.sleep(2)
    record_data(sn, x, test_type, snr, thd, sinad, enob, sfdr, floor, status)
    
    
    # plot_data(x, data, my_cn0579)                                                    # Plot ADC readings
    print("len adc_data = %s" %(len(adc_data)))
    print("len adc_data[x] = %s" %(len(adc_data[x])))
    # print(adc_data)
    print("Channel %s" %(x))
    print(adc_data[x])
    sig_gen.m2k_close(libm2k_ctx,siggen)                                             # Turn off M2k for channel x
    # sig_gen.m2k_stop(libm2k_ctx,siggen)
    csource_switch(my_cn0579, x, 0)     # Turn off current source for channel x 
    # volt_reading = read_DC(libm2k_ctx)
    set_DAC(0, x, my_cn0579)                            # Set output of the DAC to 0     
    adc_data.clear()
    print("len adc_data = %s" %(len(adc_data)))   
    del adc_data                                                     
    
    #print("Channel %s" %(x))
    #print(data[x])
    # del volt_reading
    return 

def main(my_uri):
    print("CN0579 Production Test \nTest script starting....")
    
    
    # set serial number for the board on test
    sn = get_serial()
    
    
    
    # for i in range(3,-1,-1):
    for i in range (0,4):
        if i==4: # to set test start at channel 1 then end with channel 0
            i=0
            
        print("\nStarting FS test for channel %s" %(i))
        input("\nAfter connecting the test jig on CN0579: \n1.) remove header on other channels.\n2.) short header on test jig for Channel %s. \n3.) turn test jig switch to full amplitude.\n\nPress enter to continue." %(i))
        q = "FS test"
        my_cn0579 = init_my_adc(my_uri)
        time.sleep(2)
        channel_tests(my_cn0579, q, i, sn)
        time.sleep(2)
        del my_cn0579
        
        att_cn0579 = init_my_adc(my_uri)
        print("\nStarting Attenuated test for channel %s" %(i))
        input("\n1.) keep header on test jig for Channel %s shorted\n2.) turn test jig switch to attenuated.\n\nPress enter to continue." %(i))
        q = "Attenuated"
        channel_tests(att_cn0579, q, i, sn)
        time.sleep(2)
        del att_cn0579
     
  
# retest= input("Repeat test on failed channel/s? [y/n]")
# if retest=='y'
  
#If test code is ran locally in FPGA, my_ip is just the localhost. If control will be through a Windows machine/external, need to get IP address of the connected setup through LAN.
if __name__ == '__main__':    
    start = time.time()   
    print("ADI packages import done")
    
    # Optionally passes URI as command line argument,
    # else use default ip:analog.local
    my_uri = sys.argv[2] if len(sys.argv) >= 3 else "ip:analog.local"
    print("\nConnecting with CN0579 context at: " + str(my_uri))
    
    main(my_uri)
    
   

    print("\nTest took " + str(time.time() - start) + " seconds.")
