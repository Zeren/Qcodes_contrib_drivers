import logging
from typing import Any
import numpy as np

from qcodes import VisaInstrument
from qcodes import validators as vals

log = logging.getLogger(__name__)


class RohdeSchwarz_FSV3000(VisaInstrument):
    def __init__(self, name: str, address: str, **kwargs: Any) -> None:
        super().__init__(name, address, **kwargs)

        m_frequency = {
            "FSV3004": (10, 4e9),
            "FSV3007": (10, 7.5e9),
            "FSV3013": (10, 13.6e9),
            "FSV3030": (10, 30e9),
            "FSV3044": (10, 44e9),
        }

        self.model = self.get_idn()['model']
        if self.model not in m_frequency.keys():
            raise RuntimeError(f"Unsupported FSV model {self.model}")
        self._min_freq, self._max_freq = m_frequency[self.model]
        self.options = self.ask("*OPT?").strip().split(",")

        self.add_function("reset", call_cmd="*RST")
        self.add_parameter('options',
                           label='Options',
                           set_cmd=False,
                           get_cmd=self.get_options,
                           docstring="(ReadOnly) List of installed options.")
        self.add_parameter("start",
                           label='Start',
                           set_cmd='FREQ:STAR {}',
                           get_cmd='FREQ:STAR?',
                           vals=vals.Numbers(self._min_freq, self._max_freq))
        self.add_parameter('stop',
                           label='Stop',
                           set_cmd='FREQ:STOP {}',
                           get_cmd='FREQ:STOP?',
                           vals=vals.Numbers(self._min_freq, self._max_freq))
        self.add_parameter('center',
                           label='Center',
                           set_cmd='FREQ:CENT {}',
                           get_cmd='FREQ:CENT?',
                           vals=vals.Numbers(self._min_freq, self._max_freq))
        self.add_parameter('span',
                           label='Span',
                           set_cmd='FREQ:SPAN {}',
                           get_cmd='FREQ:SPAN?',
                           vals=vals.Numbers(self._min_freq, self._max_freq))
        if 'B25' in self.options:
            attenuation_aval = vals.Enum(*np.arange(0, 75.1, 1).tolist())
        else:
            attenuation_aval = vals.Enum(*np.arange(0, 75.1, 5).tolist())
        self.add_parameter('att',
                           label='Attenuator',
                           set_cmd='INP:ATT {}dB',
                           get_cmd='INP:ATT?',
                           vals=attenuation_aval)

        if 'B24' in self.options:
            self.add_parameter('preamp',
                               label='Preamplifier',
                               set_cmd='INP:GAIN:STAT {}',
                               get_cmd='INP:GAIN:STAT?',
                               val_mapping={'ON': 1, 'OFF': 0},
                               vals=vals.Enum('ON', 'OFF'))
            if self.model == 'FSV3044':
                values = vals.Enum(30)
            else:
                values = vals.Enum(15, 30)
            self.add_parameter('preamp_gain',
                               label='Preamplifier gain',
                               set_cmd='INP:GAIN:VAL {}',
                               get_cmd='INP:GAIN:VAL?',
                               vals=values)

    def get_options(self):
        return self.options


def test():
    import qcodes_contrib_drivers.drivers.RohdeSchwarz.FSV3000 as FSV3000
    fsv = FSV3000.RohdeSchwarz_FSV3000(name='FSV3044', address='TCPIP::192.168.88.15::hislip0::INSTR')
    print(fsv.options)
    # fsv.att(5)
    # fsv.preamp('OFF')
    # print(fsv.preamp(), fsv.preamp_gain())
    fsv.stop(3e9)

if __name__ == '__main__':
    test()
