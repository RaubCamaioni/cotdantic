# COT(PY)DANTIC

Pythonic generation of Coursor-On-Target (COT) messages (xml/protobuf).  
Provides pydantic_xml models with type completion / verification.  
Allows easy transformation between xml and protobuf.  
Provides human readable cot type construction.  

## COT/TAK Resources

[takproto](https://takproto.readthedocs.io/en/latest): Encoding of XML to protobuf  
[pydantic_xml](https://pydantic-xml.readthedocs.io/en/latest/): Python pydantic models to XML  
[pytak](https://pytak.readthedocs.io/en/latest/examples/): Wealth of COT/TAK format information  
[cot_types](https://github.com/dB-SPL/cot-types): Cot type to human readable mapping  
[MIL STD 2525](http://everyspec.com/MIL-STD/MIL-STD-2000-2999/MIL-STD-2525B_CHG-2_20725/#:~:text=These%20symbols%20are%20designed%20to%20enhance%20DOD%60s%20joint%20warfighting%20interoperability): cot type symbols  
[tak.gov](https://tak.gov/): Governing body of ATAK, Wintak, and other TAK based protocols  
[dev_guide](https://nps.edu/documents/104517539/109705106/COT+Developer+Guide.pdf/cb125ac8-1ed1-477b-a914-7557c356a303#:~:text=What%20is%20Cursor-on-Target?%20In%20a%20nutshell,): developer outline of COT messages  
[tak_miter](https://www.mitre.org/sites/default/files/pdf/09_4937.pdf): in-depth cot descriptions  

## Common Utilities

COT is sent with TCP/UDP and multicast.  
This package includes a simple multicast listener that automatically parses XML/Protobuf messages.  
The captured messages are printed in their XML/Protobuf representations.  
```
cot-listener --help
usage: cot-listener [-h] [--maddress MADDRESS] [--mport MPORT] [--minterface MINTERFACE] [--gaddress GADDRESS] [--gport GPORT] [--ginterface GINTERFACE] [--uaddress UADDRESS] [--uport UPORT] [--source SOURCE]
                    [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

options:
  -h, --help            show this help message and exit
  --maddress MADDRESS   SA address
  --mport MPORT         SA port
  --minterface MINTERFACE
                        SA interface
  --gaddress GADDRESS   Chat address
  --gport GPORT         Chat port
  --ginterface GINTERFACE
                        Chat interface
  --uaddress UADDRESS   Direct address
  --uport UPORT         Direct port
  --source SOURCE       Filter for messages from source
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

A docker build is included for multicast docker testing.  
For multicast to reach inside a docker network=host must be set.  

## COT Construction

Object based creation of COT.  
Common fields have default values.  
Optional fields are excluded from XML/Protobuf.  

Creation of COT python model  
```python
from cotdantic import *
from uuid import uuid4

uid = str(uuid4())
cot_type = str(atom.friend.ground.unit.combat.infantry)

point = Point(lat=38.711, lon=-77.147, hae=10, ce=5.0, le=10.0)
contact = Contact(callsign='Delta1', endpoint='192.168.0.100:4242:tcp')
group = Group(name='Cyan', role='Team Member')
detail = Detail(contact=contact, group=group)
cot_model = Event(
	uid=uid,
	type=cot_type,
	point=point,
	detail=detail,
)
```
COT Model  
```python
type='a-f-G-U-C-I' point=Point(lat=38.711, lon=-77.147, hae=10.0, le=10.0, ce=5.0) version=2.0 uid='c56af374-52f6-4c8a-bd1d-8f48e7ebb21b' how='m-g' time='2024-10-12T20:42:31.12Z' start='2024-10-12T20:42:31.12Z' stale='2024-10-12T20:47:31.12Z' qos=None opex=None access=None detail=Detail(contact=Contact(callsign='Delta1', endpoint='192.168.0.100:4242:tcp', phone=None), takv=None, group=Group(name='Cyan', role='Team Member'), status=None, track=None, precision_location=None, link=None, alias=None, image=None, video=None)
```

## COT Conversion
COT XML  
```python
# pretty print requires lxml dependency
xml_b: bytes = cot_model.to_xml(pretty_print=True)
xml_s: str = xml_b.decode()
```
```xml
<event type="a-f-G-U-C-I" version="2.0" uid="c56af374-52f6-4c8a-bd1d-8f48e7ebb21b" how="m-g" time="2024-10-12T20:42:31.12Z" start="2024-10-12T20:42:31.12Z" stale="2024-10-12T20:47:31.12Z">
  <point lat="38.711" lon="-77.147" hae="10.0" le="10.0" ce="5.0"/>
  <detail>
    <contact callsign="Delta1" endpoint="192.168.0.100:4242:tcp"/>
    <__group name="Cyan" role="Team Member"/>
  </detail>
</event>
```
COT PROTOBUF  
```python
proto = bytes(cot_model)
```
```python
b'\xbf\x01\xbf\x12\xb3\x01\n\x0ba-f-G-U-C-I*$c56af374-52f6-4c8a-bd1d-8f48e7ebb21b0\xd0\xde\xdf\x93\xa828\xd0\xde\xdf\x93\xa82@\xb0\x86\xf2\x93\xa82J\x03m-gQ^\xbaI\x0c\x02[C@Y\xc5 \xb0rhIS\xc0a\x00\x00\x00\x00\x00\x00$@i\x00\x00\x00\x00\x00\x00\x14@q\x00\x00\x00\x00\x00\x00$@z7\x12 \n\x16192.168.0.100:4242:tcp\x12\x06Delta1\x1a\x13\n\x04Cyan\x12\x0bTeam Member'
```

## Custom Detail Extension

The below handles custom detail tags.  
```python
from pydantic_xml import attr, element
from typing import Optional
from cotdantic import *


class CustomElement(CotBase, tag='target_description'):
	hair_color: str = attr()
	eye_color: str = attr()


class CustomDetail(Detail):
	description: Optional[CustomElement] = element(default=None)


class CustomEvent(EventBase[CustomDetail]):
	pass

```
Same usage schema for xml and protobuf.  
See tests for more details.  
```python
custom_event = CustomEvent(...)
xml = custom_event.to_xml()
proto = bytes(custom_event)
CustomEvent.from_bytes(proto)
```

Alternativly, if the extention is simplistic, the following can be used to add custom detail elements.  
The below raw_xml will be added to the protobuf and XML.  
```
detail = Detail()
detail.raw_xml = b"<target_description hair_color="red" eye_color="brown"/>"
```

## Raw XML
The protobuf xml detail string is stored in Detail.raw_xml.  
The raw_xml field contains all the XML tags not defined by the model.  
These tags are added back when encoded to protobuf or XML.  


## Cot Types

Development of the available cot types is not comprehensive.  
Eventually all cot types should be accessable from the following type-completing syntax.  
```python
from cotdantic import atom
print(atom.friend.ground.unit.combat.infantry)
```
```
a-f-G-U-C-I
```
