# motor402
> An implementation of a CANopen device profile for drives and motion control according to CiA 402®.

This library heavily depends on the *CANopen for Python* implementation of the CANopen standard, mainly to provide NMT, SDO and PDO support. [[1]](#1)

## What is CANopen?

CANopen is a CAN-based communication system. It comprises higher-layer protocols and profile specifications. CANopen has been developed as a standardized embedded network with highly flexible configuration capabilities. It was designed originally for motion-oriented machine control systems, such as handling systems. Today it is used in various application fields, such as medical equipment, off-road vehicles, maritime electronics, railway applications, or building automation. [[2]](#2)

### CiA 301

CiA 301 specifies the CANopen application layer. This includes the data types, encoding rules and object dictionary objects as well as the CANopen communication services and protocols.

It also specifies the network management services (NMT).
The NMT follows a master-slave architecture. Most devices are regarded as NMT slaves and are identified by their node ID (1-127).

<div align="center">
    <img src="assets/CiA301-NMT.png" />
    <p>Figure 1. NMT Finite State Automaton</p>
</div>

### CiA 402

The CAN in Automation 402 is a profile which **defines specifications for devices able to be digitally controlled**, such as stepper motors, frequency converters and servo motors.

It includes a FSA (Figure 2) that defines the device behavior for each state, determining the available commands and wether the power is enabled or not.

<div align="center">
    <img src="assets/CiA402-FSA.png" />
    <p>Figure 2. CiA402 Finite State Automaton</p>
</div>

Although CiA402 is a well-specified set of motion control profiles, the manufacturer-specific functions and parameters (or lack thereof) *heavily* limit the exchangeability of compliant devices. [[3]](#3)


## Installation

```bash
pip install motor402
```

or just by cloning this repository and running

```bash
git clone https://gitlab.com/altairLab/elasticteam/can/motor402
python setup.py install
```

## Usage example

To bring up the *can0* interface we would write as follows:
```bash
sudo ip link set can0 type can bitrate 1000000
sudo ip link set up can0
```

```python
import canopen
from motor402 import Motor

NODE_ID = 0x75
EDS_PATH = "./examples/TMCM-6212.eds"
TARGET_POSITION = 200

network = canopen.Network()
node = canopen.RemoteNode(NODE_ID, EDS_PATH)
network.add_node(node)
network.connect(bustype="socketcan", channel="can0", bitrate=1000000)

node.nmt.state = "PRE-OPERATIONAL"

motor = Motor(node)

node.nmt.state = "OPERATIONAL"
motor.to_switch_on_disabled()

motor.move_to_target(TARGET_POSITION)
```


## References

<a id="1">[1]</a>  [CANopen for Python](https://github.com/christiansandberg/canopen)

<a id="2">[2]</a>  [CANopen – The standardized embedded network](https://www.can-cia.org/canopen)

<a id="3">[3]</a>  [CiA® 402 series: CANopen device profile for drives and motion control](https://www.can-cia.org/can-knowledge/canopen/cia402)

## Authors

- Matteo Meneghetti
- Noè Murr

## Contributing

1. Fork it
2. Create your feature branch (`git checkout -b feature/foo`)
3. Commit your changes (`git commit -am 'Add some foo'`)
4. Push to the branch (`git push origin feature/foo`)
5. Create a new Pull Request
