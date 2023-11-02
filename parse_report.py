import sys
import argparse
import re
from bs4 import BeautifulSoup
import json
import numpy as np


def find_key_values(key, dic):
    res = None
    for search_key, search_items in dic.items():
        if search_key == key:
            res = search_items
        if isinstance(search_items, dict):
            res = find_key_values(key, search_items)
        elif isinstance(search_items, list):
            for item in search_items:
                if isinstance(item, dict):
                    res = find_key_values(key, item)
                    if res is not None:
                        break
        if res is not None:
            return res
    return None


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory containing performance report and logs",
    )
    arg = parser.parse_args(args)

    with open(f"{arg.output_dir}/performance_report.html") as fp:
        soup = BeautifulSoup(fp, "html.parser")

    report_body = soup.body.script.string
    duration = float(re.search("; Duration:(.+?) &", report_body).group(1).rstrip("s"))
    number_of_tasks = int(re.search("; number of tasks:(.+?) &", report_body).group(1))
    compute_duration = float(
        re.search("; compute time:(.+?) &", report_body).group(1).rstrip("s")
    )
    transfer_duration = float(
        re.search("; transfer time:(.+?) &", report_body).group(1).rstrip("s")
    )
    number_of_workers = int(re.search("; Workers:(.+?) &", report_body).group(1))
    print(
        f"""
    Performance Report 
        Duration: {duration}s
        Number of Tasks: {number_of_tasks}
        Compute Duration: {compute_duration}s
        Transfer Duration: {transfer_duration}s
        Number of Workers: {number_of_workers}
    """
    )
    report_dict = json.loads(report_body)
    task_stream = report_dict[list(report_dict.keys())[0]]["roots"][0]["attributes"][
        "tabs"
    ][1]["attributes"]
    assert task_stream["title"] == "Task Stream"
    key_items = find_key_values("entries", task_stream)
    columns = [item[0] for item in key_items]

    for function in ["retrieve@cd", "retrieve@(.)f", "efi", "sot", "write", "transfer"]:
        name_index = columns.index("name")
        duration_index = columns.index("duration")
        function_occurrences = np.array(
            [re.search(f"^{function}", x) is not None for x in key_items[name_index][1]]
        )
        avg_function_time = (
            np.mean(np.array(key_items[duration_index][1])[function_occurrences]) / 1000
        )
        print(
            f"Function {function}, occurrences {np.sum(function_occurrences)}, average {avg_function_time:.3f}s."
        )

    # Can capture transfer time, efi and sot computation time but not read and write rates in terms of MB/s
    # For final benchmark need to turn off control, do separate runs with varying window sizes


if __name__ == "__main__":
    main(sys.argv[1:])
