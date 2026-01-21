import yaml
import argparse


def yaml_transclude(node):
    """
    Recursive function to transclude referenced YAML files. The file path provided by the extend key's value is loaded
    then the key value pair with the extend key is removed. Then the loaded YAML is loaded in place of the removed pair.
    :param node:
    :return: None
    """
    for node_key, node_value in node.items():
        if "extend" in node_key:
            file_name = node_value
            # remove the key value pair with the extend key
            del node[node_key]
            with open(file_name, "r") as f:
                project_settings = yaml.safe_load(f)
                # overwrite the data from the loaded YAML
                project_settings.update(node)
                # recursive call to replace extend in the loaded project settings
                yaml_transclude(project_settings)
                # then overwrite the new changes back to the original node
                node.update(project_settings)
            break
        elif type(node_value) is dict:
            yaml_transclude(node_value)


def generate_yaml(file_path, output_file_name):
    with open(file_path, "r") as project_file:
        project_data = yaml.safe_load(project_file)

    # call the transclude function to update the project_data
    yaml_transclude(project_data)
    with open(output_file_name, "w") as output_file:
        yaml.dump(project_data, output_file, sort_keys=False)


def parse_arguments():
    parser = argparse.ArgumentParser(prog="Settings Configurator")
    parser.add_argument(
        "-f", "--file", type=str, metavar="<file_path>", help="target path to YAML file"
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        metavar="<file_name>",
        help="output file name (default: %(default)s)",
        default="output.yaml",
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    if args.file:
        generate_yaml(args.file, args.out)


if __name__ == "__main__":
    main()
