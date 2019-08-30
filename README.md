## Requirements

Graphviz Python library

## Usage
You can run this script from the command line:
```
dependency_graph.py folder output filename [-h] [-f {bmp,gif,jpg,png,pdf,svg}] [-v] [-c]
```

```
positional arguments:
  folder                Path to the folder to scan
  output                Path of the output files without the extension
  filename              Name of the output file without extension

optional arguments:
  -h, --help            show this help message and exit
  -f {bmp,gif,jpg,png,pdf,svg}, --format {bmp,gif,jpg,png,pdf,svg}
                        Format of the output
  -v, --view            View the graph
  -c, --cluster         Create a cluster for each subfolder
```