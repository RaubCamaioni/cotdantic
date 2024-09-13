from coursor_on_target import (
    Point,
    Contact,
    Detail,
    Alias,
    Event,
    model2proto,
    proto2model,
)


def generate_cot():
    point = Point(lat=38.696644, lon=-77.140433)
    contact = Contact(callsign="DogMan", endpoint="172.16.0.128:4242:tcp")
    detail = Detail(
        contact=contact,
        uid=Alias(Droid="SpecialBoy"),
    )
    event = Event(
        type="a-f-G-U-C-I",
        point=point,
        detail=detail,
    )
    event.type = "a-f-A-M-H-Q-r"

    xml = event.to_xml()

    xml_reconstruct = Event.from_xml(xml)

    return xml_reconstruct, xml


if __name__ == "__main__":

    event, xml = generate_cot()
    proto = model2proto(event)
    recon = proto2model(proto)

    print("Original Model")
    print(event, "\n")
    print("Reconstructed Model")
    print(recon, "\n")
    print("Original XML")
    print(xml, "\n")
    print("Reconstructed XML")
    print(recon.to_xml(), "\n")
    print("Proto from Takproto")
    print(proto, "\n")
