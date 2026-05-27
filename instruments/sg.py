class VirtualSG:
    def __init__(self, dut, freq=5.2e9, power_dbm=-100.0):
        self.dut = dut
        self.freq = freq
        self.power_dbm = power_dbm
        self.is_on = False

    def set_cw_tone(self, freq): 
        self.freq = freq
        if self.is_on:
            self.dut.apply_cw_drive(self.freq, self.power_dbm)
        
    def set_power(self, power_dbm): 
        self.power_dbm = power_dbm
        if self.is_on:
            self.dut.apply_cw_drive(self.freq, self.power_dbm)
    
    def on(self):
        self.is_on = True
        self.dut.apply_cw_drive(self.freq, self.power_dbm)

    def off(self):
        self.is_on = False
        self.dut.remove_cw_drive()
