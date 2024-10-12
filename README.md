# COT(PY)DANTIC

Pythonic implimentation of COT generation (xml/protobuf).
Provides pydantic models with type completion / verification.

Allows easy transformation between xml and protobuf.

## Resources

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
The messages are converted to human readable XML and printed to console.  
```
cot-listener --address 239.2.3.1 --port 6969 --interface 0.0.0.0
```

A docker build is included for multicast docker testing.  
For multicast to reach inside a docker network=host must be set.  

## Usage: Construction

Object based creation of COT model.  
Many fields have default values.  
Many COT messages do not requires all fields.  
Fields that are set to None are not encoded to XML.  

Creation of COT python model  
```python
from cotdantic import *
from uuid import uuid4

point = Point(lat=38.711, lon=-77.147, hae=10, ce=5.0, le=10.0)
contact = Contact(
    callsign="Delta1",
    endpoint="192.168.0.100:4242:tcp",
    phone="+12223334444",
)
takv = Takv(
    device="virtual",
    platform="virtual",
    os="linux",
    version="1.0.0",
)
group = Group(name="squad_1", role="SquadLeader")
status = Status(battery=50)
precision_location = PrecisionLocation(altsrc="gps", geopointsrc="m-g")
link = Link(parent_callsign="DeltaPlatoon", relation="p-l")
alias = Alias(Droid="special_system")
detail = Detail(
    contact=contact,
    takv=takv,
    group=group,
    status=status,
    precision_location=precision_location,
    link=link,
    alias=alias,
)
cot_model = Event(
    uuid=str(uuid4()),
    type="a-f-G-U-C-I",
    point=point,
    detail=detail,
)
```
COT Model  
```
version=2.0 type='a-f-G-U-C-I' uid='3ba95f96-b621-4a37-957d-cf1a13d24937' how='m-g' time='2024-09-24T16:30:18.14Z' start='2024-09-24T16:30:18.14Z' stale='2024-09-24T16:35:18.14Z' point=Point(lat=38.711, lon=-77.147, hae=10.0, le=10.0, ce=5.0) detail=Detail(contact=Contact(callsign='Delta1', endpoint='192.168.0.100:4242:tcp', phone='+12223334444'), takv=Takv(device='virtual', platform='virtual', os='linux', version='1.0.0'), group=Group(name='squad_1', role='SquadLeader'), status=Status(battery=50), precisionlocation=PrecisionLocation(geopointsrc='m-g', altsrc='gps'), link=Link(relation='p-l', parent_callsign='DeltaPlatoon'), alias=Alias(Droid='special_system'))
```

## Usage: Conversion

All examples use cot_model object created in first example.  

COT XML  
```python
# pretty print requires lxml dependency
xml_b: bytes = cot_model.to_xml(pretty_print=True)
xml_s: str = xml_b.decode()
```
```xml
<event version="2.0" type="a-f-G-U-C-I" uid="3ba95f96-b621-4a37-957d-cf1a13d24937" how="m-g" time="2024-09-24T16:30:18.14Z" start="2024-09-24T16:30:18.14Z" stale="2024-09-24T16:35:18.14Z">
  <point lat="38.711" lon="-77.147" hae="10.0" le="10.0" ce="5.0"/>
  <detail>
    <contact callsign="Delta1" endpoint="192.168.0.100:4242:tcp" phone="+12223334444"/>
    <takv device="virtual" platform="virtual" os="linux" version="1.0.0"/>
    <__group name="squad_1" role="SquadLeader"/>
    <status battery="50"/>
    <precisionlocation geopointsrc="m-g" altsrc="gps"/>
    <link relation="p-l" parent_callsign="DeltaPlatoon"/>
    <uid Droid="special_system"/>
  </detail>
</event>
```
COT PROTOBUF  
```python
proto = bytes(cot_model)
cot_model2 = Event.from_bytes(proto)
```
```python
b'\xbf\x01\xbf\x12\xbf\x02\n\x0ba-f-G-U-C-I*$3ba95f96-b621-4a37-957d-cf1a13d249370\x9c\x9c\xfa\xa6\xa228\x9c\x9c\xfa\xa6\xa22@\xfc\xc3\x8c\xa7\xa22J\x03m-gQ^\xbaI\x0c\x02[C@Y\xc5 \xb0rhIS\xc0a\x00\x00\x00\x00\x00\x00$@i\x00\x00\x00\x00\x00\x00\x14@q\x00\x00\x00\x00\x00\x00$@z\xc2\x01\nT<link relation="p-l" parent_callsign="DeltaPlatoon" /><uid Droid="special_system" />\x12 \n\x16192.168.0.100:4242:tcp\x12\x06Delta1\x1a\x16\n\x07squad_1\x12\x0bSquadLeader"\n\n\x03m-g\x12\x03gps*\x02\x0822 \n\x07virtual\x12\x07virtual\x1a\x05linux"\x051.0.0'
```

## Usage: Custom Detail

The below handles custom detail tags.  
```python
from cotdantic import *
from typing import Optional

class CustomElement(BaseXmlModel, tag="target_description"):
    hair_color: str = attr()
    eye_color: str = attr()

class CustomDetail(Detail):
    description: Optional[CustomElement] = element(default=None)

class CustomEvent(EventBase[CustomDetail]):
    pass

```
Same usage schema for xml and protobuf.  
```python
custom_event = CustomEvent(...)
xml = custom_event.to_xml()
proto = bytes(custom_event)
CustomEvent.from_bytes(proto)
```

## Cot Types

Development of the available cot types is not comprehensive.  
Eventually all cot types should be accessable from the following type-completing syntax.  
```python
from cotdantic.cot_types import COT_TYPES
print(COT_TYPES.atom.faker.air.present.military)
```
```
a.k.A.P.M
```
