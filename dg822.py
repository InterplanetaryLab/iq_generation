# Class for interfacing with Rigol DG8** + DG9** Series AWG
#!/usr/bin/python3
import time
import pyvisa
import math
import numpy as np
import struct

class dg822:
    def __init__(self):
        self.device_addr_str = "XXXXX" # Invalid default str
        self.arb = 0 # arb device
        self.rm = 0 # resource manager for pyvisa
        self.fake_test = 0 # flag so that output statements can be tested without the rigol device
    def connect_arb(self, device_addr_str = ''):
        if (device_addr_str != ''):
            self.device_addr_str = device_addr_str

        # Get resource manager
        self.rm = pyvisa.ResourceManager()
        print(self.rm.list_resources())

        self.arb = rm.open_resource(self.device_addr_str)
        self.arb_send('*IDN?')
        data_return_idn = self.arb.read()
        print(data_return_idn)
        if (data_return_idn > 0):
            #assuming for now that the device was found correctly if the return data len is greater than 0
            return 1
        else:
            return 0
    def rigol_len(length):
        rtxt = "#"
        rtxt += str(len(str(length))) + str(length)
        return rtxt
    def arb_send(self, data):
        if (self.fake_test != 1):
            self.arb(data)
        # arb write but has delay that is somewhat conservative (see btbm.ch)
        delay = 0.001 * len(data)
        if delay < 0.2:
            delay = 0.2
        print(data)
        time.sleep(delay)
    # inputs is channel num, sp_freq, volt pkpk, phase, dc offset, data_samples (expected to already be capped to limits of -2^15 and 2^15
    def set_output_arb(self,channel_number,sp_freq,volt,phase,offset,data):
        number = ((channel_number%2)+1)
        samplebytes = struct.pack('<' + 'h'*len(data), *data)
        while (len(samplebytes) > 65536):
            self.arb_send((b":SOURCE%d:TRACE:DATA:DAC16 VOLATILE,CON,#"%number) + dg822.rigol_len(65536).encode('utf-8') + samplebytes[0:65536])

        if (len(samplebytes) > 0):
            self.arb_send((b"SOURCE%d:TRACE:DATA:DAC16 VOLATILE,END,"%number) + dg822.rigol_len(len(samplebytes)).encode('utf-8') + samplebytes)

    def set_output(self,channel_number,state):
        number = ((channel_number%2)+1)
        if (state == 1):
            out_str = (':OUTPUT%d ON'%number)
        else:
            out_str = (':OUTPUT%d OFF'%number)
        print(out_str)
        self.arb_send(out_str)
    # sets the given channel to 1 250mV 2kHz sine output. Relatively low power (approximately 0dBm). DOES NOT SET OUTPUT ON.
    def set_test_sin(self,channel_number,high_imp):
        self.set_output(channel_number,0)
        number = ((channel_number%2)+1)
        out_str = ":SOURCE%d:FUNC SIN"%number
        self.arb_send(out_str)

        out_str = ":FREQ 2000"
        self.arb_send(out_str)
        out_str = ":VOLT .25"
        self.arb_send(out_str)

        out_str = ":PHASE 0"
        self.arb_send(out_str)
        
        if (high_imp == 1):
            out_str = ":OUTPUT%d:IMP INF"%number
        else:
            out_str = ":OUTPUT%d:IMP 50"%number
        self.arb_send(out_str)
        
if __name__ == '__main__':
    rigol_dg = dg822()
    rigol_dg.fake_test = 1 # setting to 1 so commands aren't sent to the arb just commands are built
    # output on/off test
   # rigol_dg.set_output(1,1)
   # rigol_dg.set_output(1,0)
   # rigol_dg.set_output(2,1)
   # rigol_dg.set_output(2,0)

   # # test_sin
   # rigol_dg.set_test_sin(1,0)
   # rigol_dg.set_test_sin(2,0)
   # rigol_dg.set_test_sin(1,1)
   # rigol_dg.set_test_sin(2,1)

    # arb test
    points = [1,2,3,4,-1,-2,-3,-4]
    rigol_dg.set_output_arb(channel_number=1,sp_freq=1,volt=1,phase=0,offset=0,data=points)
