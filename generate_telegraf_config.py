import json
import toml
import tempfile
import os
import sys

from config import (
    telegraf_config_output_path,
    group_addresses_output_path,
    knx_service_address,
    knx_service_type,
    ignore_missing_dpt_subtypes,
    ignored_addresses,
    ignored_dpt_types,
    dpt_types_whitelist,
    dpt_subtype_default_value,
)


def ensure_group_addresses_output_exists(path):
    if not os.path.isfile(path):
        print(
            "❗️Group addresses output does not exist at",
            path,
            ", please ensure to run `python extract_group_addresses.py` first!",
        )

        sys.exit(1)


def read_group_addresses(path):
    with open(path, "r") as f:
        return json.load(f)


def should_ignore_address_or_dpt(address, dpt):
    should_ignore = False

    if len(dpt_types_whitelist) > 0 and dpt not in dpt_types_whitelist:
        should_ignore = True

    for ignore_address in ignored_addresses:
        if address.startswith(ignore_address):
            should_ignore = True
            break

    for ignored_dpt_type in ignored_dpt_types:
        if dpt.startswith(ignored_dpt_type):
            should_ignore = True
            break

    return should_ignore


def generate_measurements(group_addresses):
    measurements = {}

    stats = {
        "no_dpt_addresses_count": 0,
        "no_dpt_subtype_addresses_count": 0,
        "ignored_addresses_count": 0,
    }

    for ga in group_addresses:
        try:
            name = ga["name"]
            address = ga["address"]
            dpt = f"{ga['dpt_type']['main']}.{ga['dpt_type'].get('sub', dpt_subtype_default_value):03}"
            dpt_formatted = "(%s)" % dpt

            # Ignore logic

            if should_ignore_address_or_dpt(address, dpt):
                stats["ignored_addresses_count"] += 1

                print(
                    address,
                    dpt_formatted,
                    name,
                    "| Info 📌 - Ignoring address explicitly",
                )

                continue

            # Handle missing dpt subtype

            if not ga["dpt_type"].get("sub"):
                stats["no_dpt_subtype_addresses_count"] += 1

                if ignore_missing_dpt_subtypes:
                    continue

                print(
                    address,
                    dpt_formatted,
                    name,
                    "| Warning 🚧 - Missing datapoint subtype was replaced with a default value",
                    '"%s"!' % dpt_subtype_default_value,
                    )

            # Populate measurements

            if address not in measurements:
                measurements[address] = {
                    "name": name,
                    "addresses": [address],
                    "dpt": dpt,
                }
            else:
                measurements[address]["addresses"].append(address)
        except TypeError:
            stats["no_dpt_addresses_count"] += 1

            print(
                ga["address"],
                ga["name"] if ga["name"] != "-" else "No Address Name",
                "| Error ⛔ - No datapoint found for the address!",
            )

    return measurements.values(), stats


def print_stats(measurements, stats):
    print("\n🎉", len(measurements), "group addresses were parsed")
    print("⛔", stats["no_dpt_addresses_count"], "addresses without datapoint type")
    print("🚧", stats["no_dpt_subtype_addresses_count"], "addresses without datapoint subtype")

    if stats["ignored_addresses_count"]:
        print("🚧", stats["ignored_addresses_count"], "ignored addresses")

    print(
        "📈",
        len(measurements)
        + stats["no_dpt_addresses_count"]
        + stats["no_dpt_subtype_addresses_count"]
        + stats["ignored_addresses_count"],
        "addresses in total\n",
        )


def generate_telegraf_config(measurements):
    telegraf_config = {
        "inputs": {
            "knx_listener": {
                "service_type": knx_service_type,
                "service_address": knx_service_address,
                "measurement": [],
            }
        }
    }

    for data in measurements:
        telegraf_config["inputs"]["knx_listener"]["measurement"].append(data)

    return telegraf_config


def write_telegraf_config(telegraf_config, path):
    with open(path, "w") as f:
        toml.dump(telegraf_config, f)


def post_process_telegraf_config(path):
    telegraf_config_temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

    # Remove trailing commas and other

    with open(path, "r") as f:
        for line in f:
            if "[inputs.knx_listener]" in line:
                line = line.replace("[inputs.knx_listener]", "[[inputs.knx_listener]]")
            if "addresses" in line:
                line = line.replace(",]", " ]")

            telegraf_config_temp_file.write(line)

    telegraf_config_temp_file.close()

    os.replace(telegraf_config_temp_file.name, path)


def main():
    # Run pre-condition checks

    ensure_group_addresses_output_exists(group_addresses_output_path)

    # Read Group Addresses

    print(
        "🔄 Start reading group addresses into memory from %s...\n"
        % group_addresses_output_path
    )

    group_addresses = read_group_addresses(group_addresses_output_path)

    print("🎉 Reading group addresses finished!\n")

    # Generate Measurements and Print Stats

    print("🔄 Start parsing group addresses...\n")

    measurements, stats = generate_measurements(group_addresses)

    print_stats(measurements, stats)

    # Generate Telegraf Config

    print("🔄 Start generating telegraf config file...")

    telegraf_config = generate_telegraf_config(measurements)

    # Write Telegraf Config

    write_telegraf_config(telegraf_config, telegraf_config_output_path)

    # Post-process Telegraf Config

    post_process_telegraf_config(telegraf_config_output_path)

    print("\n✅ Telegraf config file was written to", telegraf_config_output_path)


if __name__ == "__main__":
    main()
