This folder is the default folder for the experiments. More information about the examples and all the files related to the examples can be found from `/examples`.

To use your own experiment you can use this folder with these easy steps:
- Add your experiment files in .yaml format here
- Add used FMUs in the fmu folder or define the correct path in the experiment file
- If used, add the description to external servers and the path in the experiment file

```powershell
uv run fmuil run "my_experiment.yaml"
```
Optionally you can delete the example experiment here and run:

```powershell
uv run fmuil run-all
```

Or you can run the experiments by defining the experiment config folder by yourself:
```powershell
uv run fmuil -d "path/to/experiments" run "my_experiment.yaml"
```
Be sure that the paths are correctly setup to your FMUs and external servers.

