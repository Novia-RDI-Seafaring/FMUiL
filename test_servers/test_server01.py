import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.methods import uamethod


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:7500/freeopcua/server/")

    # set up our own namespace, not really necessary but should as spec
    # uri = "http://examples.freeopcua.github.io"
    idx = 3

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    myobj = await server.nodes.objects.add_object(idx, "sample_opc_object")
    var = "custom_variable"
    myvar = await myobj.add_variable(nodeid=ua.NodeId(var), bname=var, val=0.0)
    myvarid = await myobj.add_variable(nodeid=ua.NodeId(Identifier= 4, NamespaceIndex=5), bname=var, val=0.0)
    # Set MyVariable to be writable by clients
    await myvar.set_writable()
    await myvarid.set_writable()
    
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            new_val = await myvarid.get_value() + 0.1
            _logger.info("Set value of %s to %.1f", myvarid, new_val)
            await myvarid.write_value(new_val)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)