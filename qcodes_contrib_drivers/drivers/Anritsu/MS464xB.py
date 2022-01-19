import logging
from typing import Any, Optional

from qcodes import VisaInstrument, MultiParameter, validators as vals, InstrumentChannel, ChannelList

log = logging.getLogger(__name__)


class FrequencySweepMagPhase(MultiParameter):
    def __init__(self, name: str, instrument: "MS464xBChannel") -> None:
        super().__init__(
            name,
            instrument=instrument,
            names=("magnitude", "phase"),
            labels=(
                f"{instrument.short_name} magnitude",
                f"{instrument.short_name} phase",
            ),
            units=("", "rad"),
            setpoints=((), (),),
            shapes=((), (),),
        )


class MS464xBChannel(InstrumentChannel):
    def __init__(
            self,
            parent: "MS464xB",
            name: str,
            channel: int,
            vna_parameter: Optional[str] = None,
            existing_trace_to_bind_to: Optional[str] = None,
            ) -> None:
        super().__init__(parent, name)
        self._instrument_channel = channel



class MS464xB(VisaInstrument):
    def __init__(self,
                 name: str,
                 address: str,
                 init: bool = True,
                 **kwargs: Any) -> None:
        super(MS464xB, self).__init__(name, address, **kwargs)

        m_frequency = {
            "MS4642B": (10e6, 20e9),
            "MS4644B": (10e6, 40e9),
            "MS4645B": (10e6, 50e9),
            "MS4647B": (10e6, 70e9),
        }
        self.model = self.get_idn()['model']
        if self.model not in m_frequency.keys():
            raise RuntimeError(f"Unsupported FSV model {self.model}")
        self._min_freq, self._max_freq = m_frequency[self.model]
        self.options = self.ask("*OPT?").strip().split(",")

        if init:
            self.reset()

        channels = ChannelList(
            self, "VNAChannels", MS464xBChannel, snapshotable=True
        )
        self.add_submodule('channels', channels)

        if init:
            self.add_channel('channel1')

        self.add_parameter(name='trig_source',
                           label='Triggering source',
                           set_cmd='TRIG:SOUR {}',
                           get_cmd='TRIG:SOUR?',
                           vals=vals.Enum('AUTO', 'MAN', 'EXTT', 'EXT', 'REM'))
        self.add_parameter(name='port_count',
                           label='Number of instrument test ports',
                           set_cmd=False,
                           get_cmd='SYST:PORT:COUN?')

    def reset(self):
        self.write('*RST')

    def add_channel(self, channel_name: str, **kwargs: Any) -> None:
        i_channel = len(self.channels) + 1
        channel = self.MS464xBChannel(self, channel_name, i_channel, **kwargs)
        self.channels.append(channel)
        if i_channel == 1:
            self.display_single_window()
        if i_channel == 2:
            self.display_dual_window()
        # shortcut
        setattr(self, channel_name, channel)
        # initialising channel
        self.write(f"SENS{i_channel}:SWE:TYPE LIN")
        self.write(f"SENS{i_channel}:SWE:TIME:AUTO ON")
        self.write(f"CALC{i_channel}:PAR:FORM REIM")

