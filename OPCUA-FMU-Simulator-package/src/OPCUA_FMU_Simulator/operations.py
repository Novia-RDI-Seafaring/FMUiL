import operator
"""
Used to interpret the inputs given in the config.yaml files
as it allows the usage of strings as operators ie "+, -, etc..."
"""
ops = { 
    "+": operator.add, 
    "-": operator.sub, 
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge
}
