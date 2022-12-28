import numpy as np
import math
import matplotlib.pyplot as plt
from dg822_dtmf import *

def gen_cos_samples(samples,sp_rate,iq_freq):
    cos_samples = []
    for i in range(len(samples)):
        temp = 2*math.pi*1/sp_rate*i;
        cos_samples.append(samples[i]*np.cos(temp))
    return cos_samples

def gen_sin_samples(samples,sp_rate,iq_freq):
    sin_samples = []
    for i in range(len(samples)):
        temp = 2*math.pi*1/sp_rate*i;
        sin_samples.append(samples[i]*np.sin(temp))
    return sin_samples

def rescale(seq, low = 0, high = 16383):
    cur_low = min(seq)
    # shift the sequence to positive values
    if cur_low < 0.0: seq = [val - cur_low for val in seq]
    cur_low = min(seq)
    cur_high = max(seq)
    seq = [int(val*(high-low)*0.999/(cur_high-cur_low)) for val in seq]
    if min(seq) < low or max(seq) > high:
        print (seq)
        raise NameError("Something went wrong when rescaling values: min: %d, max: %d." % (min(seq), max(seq)))
    return seq



if __name__ == '__main__':
    sp_rate = 48E3 # 48k sample rate for now
    real_samples = []
    complex_samples = []

    send = 1 # send to 1 to send to rigol

    # Read in real and complex samples
    real_samples =[]
    complex_samples = []
    #for i in range(int(sp_rate)):
    #    real_samples.append(1)
    #    complex_samples.append(1)

    sample_count = len(complex_samples) # only 5 samples for now for a test generation
    filename = "/home/rommac/gnu_radio_dtmf/test_iq/complex"
    data = np.fromfile(open(filename), dtype=np.complex64)
    print(type(data))

    fft_out = np.fft.fft(data)
    f_list = sp_rate*np.arange((len(data)))/len(data)

    for i in data:
        real_samples.append(np.real(i))
        complex_samples.append(np.imag(i))
    cos_samples = rescale(gen_cos_samples(real_samples,sp_rate,sp_rate))
    sin_samples = rescale(gen_sin_samples(complex_samples,sp_rate,sp_rate))

    fig,(ax,ax2) = plt.subplots(1,2)
    ax.plot(f_list,np.abs(fft_out))
    ax2.plot(cos_samples)
    ax2.plot(sin_samples)
    plt.show()


    if (send):
        rm = pyvisa.ResourceManager()
        print(rm.list_resources())

        dg1022_str = 'USB0::6833::1603::DG8A232603057::0::INSTR'
        arb = rm.open_resource(dg1022_str)

        #test Identify
        #arb_send(arb,'*IDN?')
        load_to_channel1_and_start(arb,sp_rate, 0, .5, cos_samples)
        print(arb.read())
