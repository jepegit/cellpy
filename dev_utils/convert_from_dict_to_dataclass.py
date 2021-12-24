from cellpy import prms
# import boxing

type_translator = {
    "<class 'bool'>": "bool",
    "<class 'NoneType'>": "str",
    "<class 'str'>": "str",
    "<class 'int'>": "int",
    "<class 'float'>": "float",
    "<class 'box.box_list.BoxList'>": "list",
    "<class 'tuple'>": "tuple",
    "<class 'box.box.Box'>": "dict",
    "<class 'dict'>": "dict",
    "<class 'ruamel.yaml.scalarfloat.ScalarFloat'>": "float",

}

value_translator = {
    "'None'": None
}

should_be_inside_ticks = [
    "str"
]


def main():
    print("STARTING:")
    boxed = [d for d in dir(prms) if (not d.startswith("_")) and (d[0].isupper())]

    parse_the_things(boxed)


def parse_the_things(things_to_parse, the_module=prms):
    for thing in things_to_parse:
        print(thing.center(80, "-"))
        the_actual_thing = getattr(the_module, thing)
        if isinstance(the_actual_thing, dict):
            print("@dataclass")
            print(f"class {thing}:")
            for k, v in the_actual_thing.items():
                type_hint = type_translator.get(str(type(v)), None)
                if not type_hint:
                    type_hint = f"**{type(v)}**"
                if type_hint in should_be_inside_ticks:
                    v = f"'{v}'"
                else:
                    v = str(v)
                v = value_translator.get(v, v)
                print(f"    {k}: {type_hint} = {v}")
            print(2 * "\n")


if __name__ == "__main__":
    main()
