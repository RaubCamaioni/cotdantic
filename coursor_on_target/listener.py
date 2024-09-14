from .converters import is_xml, xml2proto, is_proto, proto2model
from .multicast import MulticastListener
import time


def print_cot(data: bytes):

    proto = None

    if is_xml(data):
        proto = xml2proto(data)

    if is_proto(data):
        proto = data

    if proto is not None:
        model = proto2model(proto)
        xml = model.to_xml()

        print(f"proto: bytes: {len(proto)}")
        print(proto, "\n")
        print(f"xml: bytes: {len(xml)}")
        print(model.to_xml(pretty_print=True).decode().strip())
        print("=" * 100)


def error_observer(data, server):
    raise ValueError("value error inside of observer!")


def cot_listener():

    print("=" * 100)
    with MulticastListener("239.2.3.1", 6969, "0.0.0.0") as mcl:

        mcl.add_observer(lambda data, server: print_cot(data))
        mcl.add_observer(error_observer)

        while True:
            time.sleep(30)
