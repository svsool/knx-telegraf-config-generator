import natsort
import json

from config import knx_driver_dpt_types_path


# Run: Array.from(new Set([...$0.querySelectorAll('tbody tr')].map(node => node.children[0]).slice(1, ).map(node => node.textContent.split('.')[0]))); # noqa
# https://www.promotic.eu/en/pmdoc/Subsystems/Comm/PmDrivers/KNXDTypes.htm
known_dpt_prefixes = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '17', '18', '19', '20', '21', '22', '23', '25', '26', '27', '29', '30', '31', '200', '201', '202', '203', '204', '205', '206', '207', '209', '210', '211', '212', '213', '214', '215', '216', '217', '218', '219', '220', '221', '222', '223', '224', '225', '229', '230', '231', '232', '234', '235', '236', '237', '238', '239', '240', '241'] # noqa


def parse_driver_dpt_types():
    dpt_list = []

    # driver dpt types were grep'ed from here https://github.com/vapourismo/knx-go/blob/master/knx/dpt
    with open(knx_driver_dpt_types_path, "r") as f:
        lines = map(str.rstrip, f.readlines())
        sorted_lines = natsort.natsorted(lines)

        for line in sorted_lines:
            dpt = line.replace("DPT_", "")

            dpt_prefix_found = False

            for known_dpt_prefix in known_dpt_prefixes:
                if not dpt.startswith(known_dpt_prefix):
                    continue

                dpt_prefix_found = True

            if not dpt_prefix_found:
                print("Unknown dpt prefix", dpt)

            if dpt_prefix_found:
                dpt_formatted = "{:.3f}".format(int(dpt) / 1000)

                dpt_list.append(dpt_formatted)

    return dpt_list


if __name__ == "__main__":
    dpt_types = parse_driver_dpt_types()

    print(
        json.dumps(
            dpt_types,
            ensure_ascii=False,
        )
    )
