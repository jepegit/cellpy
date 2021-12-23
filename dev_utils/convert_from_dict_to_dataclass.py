from cellpy import prms
# import boxing

translator = {
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


should_be_inside_ticks = [
    "str"
]


def main():
    print("STARTING:")
    boxed = [d for d in dir(prms) if (not d.startswith("_")) and (d[0].isupper())]

    for boxed_object_str in boxed:
        print(boxed_object_str.center(80, "-"))
        the_actual_box = getattr(prms, boxed_object_str)
        if isinstance(the_actual_box, dict):
            print("@dataclass")
            print(f"class {boxed_object_str}:")
            for k, v in the_actual_box.items():
                type_hint = translator.get(str(type(v)), None)
                if not type_hint:
                    type_hint = f"**{type(v)}**"
                if type_hint in should_be_inside_ticks:
                    v = f"'{v}'"
                print(f"    {k}: {type_hint} = {v}")
            print(2*"\n")


if __name__ == "__main__":
    main()
