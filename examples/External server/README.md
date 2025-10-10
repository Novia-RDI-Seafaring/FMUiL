## Example 3: External server
This example has been made to show how to run the simulator connected to external OPC UA servers. The external server is configured in `examples/External server/servers/example_server.yaml`. Simply run the `example_server.py` and afterward run the experiment:

```
uv run fmuil -d "examples\External server" run "exp3_external_server.yaml"
```