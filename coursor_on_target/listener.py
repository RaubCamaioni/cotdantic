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


def cot_listener():

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--address", type=str, default="239.2.3.1")
    parser.add_argument("--port", type=int, default=6969)
    parser.add_argument("--interface", type=str, default="0.0.0.0")
    args = parser.parse_args()

    address = args.address
    port = args.port
    interface = args.interface

    print("Multicast COT Listener:")
    print(f"  address: {address}")
    print(f"  port: {port}")
    print(f"  interface: {interface}")

    print("=" * 100)
    with MulticastListener(address, port, interface) as mcl:

        mcl.add_observer(lambda data, server: print_cot(data))

        while True:
            time.sleep(30)
