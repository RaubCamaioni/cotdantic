from coursor_on_target import (
    Point,
    Contact,
    Detail,
    Alias,
    Event,
    model2proto,
    proto2model,
)


def create_cot_model():

    point = Point(
        lat=38.696644,
        lon=-77.140433,
    )

    contact = Contact(
        callsign="DogMan",
        endpoint="172.16.0.128:4242:tcp",
    )

    detail = Detail(
        contact=contact,
        uid=Alias(Droid="SpecialBoy"),
    )

    event = Event(
        type="a-f-G-U-C-I",
        point=point,
        detail=detail,
    )

    return event


if __name__ == "__main__":

    event = create_cot_model()
    event_xml = event.to_xml()

    protobuf = model2proto(event)
    event_reconstructed = proto2model(protobuf)

    print("Original Model")
    print(event, "\n")
    print("Reconstructed Model")
    print(event_reconstructed, "\n")
    print("Original XML")
    print(event_xml, "\n")
    print("Reconstructed XML")
    print(event_reconstructed.to_xml(), "\n")
    print("Proto from Takproto")
    print(protobuf, "\n")
