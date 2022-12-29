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
    def print_rm_device_list(self):
        if (self.rm == 0):
            self.rm = pyvisa.ResourceManager()
            print(self.rm.list_resources())

    def connect_arb(self, device_addr_str = ''):
        if (self.fake_test == 0):
            if (device_addr_str != ''):
                self.device_addr_str = device_addr_str

            # Get resource manager
            self.rm = pyvisa.ResourceManager()
            print(self.rm.list_resources())

            self.arb = self.rm.open_resource(self.device_addr_str)
            self.arb_send('*IDN?')
            data_return_idn = self.arb.read()
            print(data_return_idn)
            if (len(data_return_idn) > 0):
                #assuming for now that the device was found correctly if the return data len is greater than 0
                return 1
            else:
                return 0
        else:
            return 1 # return 1 for non device testing
    def rigol_len(length):
        rtxt = "#"
        rtxt += str(len(str(length))) + str(length)
        return rtxt

    def arb_send_raw(self, data): # present since writing sometimes doesn't work with the custom byte for arb points
        if (self.fake_test != 1):
            self.arb.write_raw(data)
        # arb write but has delay that is somewhat conservative (see btbm.ch)
        delay = 0.0001 * len(data) # 100 uS should be acceptable for a 1 byte transfer time
        if delay < 0.2:
            delay = 0.2
        print(data)
        time.sleep(delay)

    def arb_send(self, data):
        if (self.fake_test != 1):
            self.arb.write(data)
        # arb write but has delay that is somewhat conservative (see btbm.ch)
        delay = 0.0001 * len(data) # 100 uS should be acceptable for a 1 byte transfer time
        if delay < 0.2:
            delay = 0.2
        print(data)
        time.sleep(delay)
    # inputs is channel num, sp_freq, volt pkpk, phase, dc offset, data_samples (expected to already be capped to limits of -2^15 and 2^15
    def set_output_arb(self,channel_number,sp_freq,volt,phase,offset,data):
        number = dg822.get_channel_num(channel_number)

        self.set_output(channel_number,0)
        rigol_dg.arb_send(':SOURCE%d:APPL:SEQ'%number)
        rigol_dg.arb_send(':SOURCE%d:FUNC:SEQ:FILT INSERT'%number)
        samplebytes = struct.pack('<' + 'h'*len(data), *data)
        while (len(samplebytes) > 65536):
            self.arb_send_raw((b":SOURCE%d:TRACE:DATA:DAC16 VOLATILE,CON,#"%number) + dg822.rigol_len(65536).encode('utf-8') + samplebytes[0:65536])
            samplebytes = samplebytes[65536:]

        if (len(samplebytes) > 0):
            self.arb_send_raw((b"SOURCE%d:TRACE:DATA:DAC16 VOLATILE,END,"%number) + dg822.rigol_len(len(samplebytes)).encode('utf-8') + samplebytes)

        rigol_dg.arb_send(':SOURCE%d:FUNC:SEQ:SRAT %d.000000'%(number,sp_freq))
        rigol_dg.arb_send(':SOURCE%d:VOLT %.3fVPP'%(number,volt))
        rigol_dg.arb_send(':SOURCE%d:PHASE %.2f'%(number,phase))

    def set_output(self,channel_number,state):
        number = dg822.get_channel_num(channel_number)
        if (state == 1):
            out_str = (':OUTPUT%d ON'%number)
        else:
            out_str = (':OUTPUT%d OFF'%number)
        print(out_str)
        self.arb_send(out_str)
    # sets the given channel to 1 250mV 2kHz sine output. Relatively low power (approximately 0dBm). DOES NOT SET OUTPUT ON.
    def get_channel_num(channel_number):
        if (channel_number == 2):
            return 2
        elif(channel_number == 1):
            return 1

    def set_test_sin(self,channel_number,high_imp):
        self.set_output(channel_number,0)
        number = dg822.get_channel_num(channel_number)

        out_str = ":SOUR%d:VOLT:UNIT VPP"%number
        self.arb_send(out_str)
        out_str = ":SOUR%d:APPL:SIN 2000000,.25,0,0"%number
        self.arb_send(out_str)
        
        if (high_imp == 1):
            out_str = ":OUTPUT%d:IMP INF"%number
        else:
            out_str = ":OUTPUT%d:IMP 50"%number
        self.arb_send(out_str)
        
if __name__ == '__main__':
    rigol_dg = dg822()
    rigol_dg.device_addr_str = "USB0::6833::1603::DG8A232603057::0::INSTR"
    rigol_dg.fake_test = 0 # setting to 1 so commands aren't sent to the arb just commands are built
    #rigol_dg.print_rm_device_list()
    init_val = rigol_dg.connect_arb()
    if (init_val == 1):
        # output on/off test
        # rigol_dg.set_output(1,1)
        # rigol_dg.set_output(1,0)
        # rigol_dg.set_output(2,1)
        # rigol_dg.set_output(2,0)

        # # test_sin
        #rigol_dg.set_test_sin(1,0)
        #rigol_dg.set_test_sin(2,0)
        # rigol_dg.set_test_sin(1,1)
        # rigol_dg.set_test_sin(2,1)

        # arb test
        samples = []
        
        pulses = 10
        pulse_width = 15
        signal_length = 100000
        for p in range(0, pulses):
            samples += [30000] * pulse_width
            samples += [-30000] * pulse_width
            samples += [0] * (signal_length - len(samples))
        rigol_dg.set_output_arb(channel_number=1,sp_freq=3E6,volt=.25,phase=10,offset=0,data=samples)
        #rigol_dg.arb_send(':SOURCE1:APPL:SEQ')
        #rigol_dg.arb_send(':SOURCE1:FUNC:SEQ:FILT INSERT')
        ##rigol_dg.arb_send(':SOURCE1:TRACe:DATA:DAC16 VOLATILE,END,#23200001c2cac4231529e534141ca1ac0e53fb967aff6e1b22699d6a2dd00000a')
        #rigol_dg.arb_send_raw(b":SOURCE1:TRACe:DATA:DAC16 VOLATILE,END,#216\x00\x40\x00\x40\x00\x40\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00")
        #rigol_dg.arb_send(':SOURCE1:FUNC:SEQ:SRAT 20000.000000')
        #rigol_dg.arb_send(':SOUR1:VOLT 0.5VPP')
