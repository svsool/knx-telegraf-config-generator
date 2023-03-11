import os
import sys
import natsort
import json

from xknxproject import XKNXProj
from operator import itemgetter

from config import knx_project_path, group_addresses_output_path


def ensure_project_exists(path):
    if not os.path.isfile(path):
        print("❗️KNX project does not exist please ensure to copy it by this path %s!" % path)

        sys.exit(1)


def parse_knx_project(project_path):
    return XKNXProj(project_path).parse()


def write_group_addresses(knx_project):
    with open(group_addresses_output_path, "w") as file:
        group_addresses = knx_project["group_addresses"].values()

        file.write(
            json.dumps(
                natsort.natsorted(group_addresses, key=itemgetter("address")),
                indent=2,
                ensure_ascii=False,
            )
        )

        return group_addresses


def main():
    # Run pre-condition checks

    ensure_project_exists(knx_project_path)

    # Parse KNX Project

    print("🔄 Start reading KNX project into memory from %s...\n" % knx_project_path)

    knx_project = parse_knx_project(knx_project_path)

    print("🎉 Reading KNX project finished!\n")

    # Write Group Addresses

    print("🔄 About to start writing group addresses...\n")

    group_addresses_result = write_group_addresses(knx_project)

    print(
        "✅ %s Group addresses were written to" % len(group_addresses_result),
        group_addresses_output_path,
        )


if __name__ == "__main__":
    main()
