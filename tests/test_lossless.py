from coursor_on_target import (
    Point,
    Contact,
    Detail,
    Alias,
    Event,
    Takv,
    Group,
    Status,
    Link,
    PrecisionLocation,
    model2proto,
    proto2model,
)


def default_cot():

    point = Point(
        lat=38.696644,
        lon=-77.140433,
        hae=10,
        ce=5.0,
        le=10.0,
    )

    contact = Contact(
        callsign="DogMan",
        endpoint="172.16.0.128:4242:tcp",
        phone="+12223334444",
    )

    takv = Takv(
        device="virtual",
        platform="virtual",
        os="linux",
        version="1.0.0",
    )

    group = Group(
        name="John",
        role="SquadLeader",
    )

    status = Status(
        battery=50,
    )

    precisionLocation = PrecisionLocation(
        altsrc="gps",
        geopointsrc="m-g",
    )

    link = Link(
        parent_callsign="Dave",
        relation="p-l",
    )

    detail = Detail(
        contact=contact,
        takv=takv,
        group=group,
        status=status,
        precisionlocation=precisionLocation,
        link=link,
        alias=Alias(Droid="SpecialBoy"),
    )

    event = Event(
        type="a-f-G-U-C-I",
        point=point,
        detail=detail,
    )

    return event


def test_xml_lossless():
    xml_src = default_cot().to_xml()
    event = Event.from_xml(xml_src)
    xml_dst = event.to_xml()
    assert xml_src == xml_dst


def test_model_lossless():
    event_src = default_cot()
    xml = event_src.to_xml()
    event_dst = Event.from_xml(xml)
    assert event_src == event_dst


def test_proto_lossless():
    event_src = default_cot()
    # takproto does not support contact.phone
    event_src.detail.contact.phone = None

    proto = model2proto(event_src)
    event_dst = proto2model(proto)

    assert event_src == event_dst


if __name__ == "__main__":
    test_xml_lossless()
    test_model_lossless()
    test_proto_lossless()
