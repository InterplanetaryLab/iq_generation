#!/usr/bin/python3
import time
import pyvisa
import math
import numpy as np
import matplotlib.pyplot as plt

#utilizes rigol manual and
# https://btbm.ch/rigol-dg1022-how-to-create-waveforms-with-python/ for inspiration

def arb_send(arb, message):
    arb.write(message)
    # arb write but has delay that is somewhat conservative (see btbm.ch)
    delay = 0.001 * len(message)
    if delay < 0.2:
        delay = 0.2
    print(message)
    time.sleep(delay)

def output_2khz_250mv(arb):
    arb_send(arb,":SOURCE1:FUNC SIN")
    arb_send(arb,":FREQ 2000")
    arb_send(arb,":VOLT .25")
    arb_send(arb,":PHASE 0")
    arb_send(arb,":OUTP1:IMP INF")

def dtmf_gen_1(x):
    return (math.sin(2*math.pi*x*697)+math.sin(2*math.pi*x*1209))

def create_data_points(func, x_start, x_end, number_of_steps):
    """
    This function calculates and scales to [-1,1] the Y points of the mathematical function func in the domain
    [x_start, x_end]. It also plots the results.
    :param func: The mathematical function to be transferred. Single parameter functions only (e.g. math.cos).
    The output of the function must be float.
    :type func: str
    :param x_start: The first element of the domain that x belongs. Must be less than x_end
    :type x_start: float
    :param x_end: The last element of the domain that x belongs. Must be greater than x_start
    :type x_end: float
    :param number_of_steps: The number of points on the X axis
    :type number_of_steps: int
    :return: The data points separated by commas (e.g. ,-1.0,-0.999,0.123)
    :rtype: str
    """
    output_string = ''
    y = []
    for i in range(number_of_steps):
        x = x_start + i * (x_end - x_start) / number_of_steps
        y.append(func(x))

    # Y scaling
    y_max = max(y)
    y_min = min(y)
    y_delta = y_max - y_min
    y_l_scaled = []

    for i in y:
        y_scaled = (i - y_min) / (y_delta / 2)  # Scale Y to [0,2]
        y_scaled -= 1.0  # Scale Y to [-1,1]
        output_string += ',' + str(round(y_scaled, 6))  # Round to 6 digits
        y_l_scaled.append(y_scaled)  # append to list
    # plot function
    plt.plot(y_l_scaled)
    plt.ylabel(func.__name__ + '(x) (scaled), [' + str(x_start) + ',' + str(x_end) + ']')
    plt.show()
    return output_string

def store_to_arb(arb,points,func_name):
    arb_send(arb,'DATA:DEL' + func_name)
    arb_send(arb,'DATA:DEL VOLATILE')
    arb_send(arb,'DATA VOLATILE' + points)
    arb_send(arb,'DATA:COPY ' + func_name)

def load_to_channel1_and_start(arb,frequency, volts_low, volts_high, points):
    """
    :param frequency: The frequency in Hertz
    :type frequency: float
    :param volts_low: The lowest voltage of VPP
    :type volts_low: float
    :param volts_high: The highest voltage of VPP
    :type volts_high: float
    :param points: the data points separated by commas (e.g. ,-1.0,-0.999,0.123)
    :type points: str
    """
    arb_send(arb,'OUTP OFF')  # Switch CH1 off
    arb_send(arb,'FUNC USER')  # Select user function
    arb_send(arb,'FREQ ' + str(frequency))  # Set the frequency
    arb_send(arb,'VOLT:UNIT VPP')  # Set VPP mode
    arb_send(arb,'VOLT:HIGH ' + str(volts_high))  # Set the max value for VPP
    arb_send(arb,'VOLT:LOW ' + str(volts_low))  # Set the min value for VPP
    arb_send(arb,'DATA VOLATILE' + points)  # Send the arb function to the VOLATILE memory
    arb_send(arb,'FUNC:USER VOLATILE')  # Load the volatile memory
    arb_send(arb,'OUTP ON')  # Turn CH1 on

def output_dual_tone(arb,freq1,freq2):
    arb_send(arb,":SOURCE1:FUNC:DUALT:FREQ1 %d"%freq1)
    arb_send(arb,":SOURCE1:FUNC:DUALT:FREQ2 %d"%freq2)
    arb_send(arb,":VOLT .25")
    arb_send(arb,":PHASE 0")
    arb_send(arb,":OUTP1:IMP 50")
    arb_send(arb,'OUTP ON')  # Turn CH1 on

if __name__ == '__main__':
    rm = pyvisa.ResourceManager()
    print(rm.list_resources())

    dg1022_str = 'USB0::6833::1603::DG8A232603057::0::INSTR'
    arb = rm.open_resource(dg1022_str)

    #test Identify
    arb_send(arb,'*IDN?')
    print(arb.read())

    #test send
    #output_2khz_250mv(arb)
    #points = create_data_points(func=dtmf_gen_1,x_start = 0, x_end = math.pi*2/2000, number_of_steps=1000)
    #store_to_arb(arb,points,'DTMF1')
    #load_to_channel1_and_start(arb,frequency=1000, volts_low=-.1,volts_high=.1, points=points)
    #output_dual_tone(arb,770,1209)
