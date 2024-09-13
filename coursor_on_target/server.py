def print_cot(data: bytes):

    proto = None

    if is_xml(data):
        proto = xml2proto(data)

    if is_proto(data):
        proto = data

    if proto is not None:
        print("========================================================")
        print("proto:")
        print(proto, "\n")
        print("xml:")
        print(models.proto2model(proto).to_xml(pretty_print=True).decode())


if __name__ == "__main__":

    print("Starting Multicast Listener: \n")
    with MulticastListener("239.2.3.1", 6969, "0.0.0.0") as mcl:

        mcl.add_observer(lambda data, server: print_cot(data))

        while True:
            time.sleep(30)

    print("Exiting")
