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


def search(function_str, text):
    return re.search(function_str, text).group(1)


def duration_in_sec(duration_str):
    if "ms" in duration_str:
        return float(duration_str.rstrip("ms")) / 1000
    return float(duration_str.rstrip("s"))


def parse_performance_report(output_dir: str):
    with open(f"{output_dir}/performance_report.html") as fp:
        soup = BeautifulSoup(fp, "html.parser")

    report_body = soup.body.script.string
    duration = duration_in_sec(search("; Duration:(.+?) &", report_body))
    number_of_tasks = int(search("; number of tasks:(.+?) &", report_body))
    compute_duration = duration_in_sec(search("; compute time:(.+?) &", report_body))
    transfer_duration = duration_in_sec(search("; transfer time:(.+?) &", report_body))
    number_of_workers = int(search("; Workers:(.+?) &", report_body))
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
    name_index = columns.index("name")
    duration_index = columns.index("duration_text")

    for function in [
        "retrieve@type=cd",
        "retrieve@type=(.)f",
        "efi",
        "sot",
        "write",
        "transfer",
    ]:
        function_occurrences = np.array(
            [re.search(f"^{function}", x) is not None for x in key_items[name_index][1]]
        )
        avg_function_time = np.mean(
            np.asarray(list(map(duration_in_sec, key_items[duration_index][1])))[
                function_occurrences
            ]
        )
        print(
            f"Function {function}, occurrences {np.sum(function_occurrences)}, average {avg_function_time:.3f}s."
        )


def parse_console_log(output_dir):
    read = []
    write = []
    with open(f"{output_dir}/console.log") as console_log:
        for line in console_log:
            if line.startswith("retrieve"):
                log_bytes = float(search("memory: (.+?) bytes", line))
                log_time = float(search("wall time: (.+?) s", line))
                read.append(log_bytes / log_time)
            if line.startswith("write"):
                log_bytes = float(search("memory: (.+?) bytes", line))
                log_time = float(search("wall time: (.+?) s", line))
                write.append(log_bytes / log_time)

    mean_read = np.mean(read)
    mean_write = np.mean(write)
    print("\nConsole Log")
    print(f"    Average read rate {mean_read:.3f} bytes/s ({mean_read/10**6:.3f} MB/s)")
    print(
        f"    Average write rate {np.mean(write):.3f} bytes/s ({mean_write/10**6:.3f} MB/s)"
    )


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_dir",
        type=str,
        help="Directory containing performance report and logs",
    )
    arg = parser.parse_args(args)

    parse_performance_report(arg.output_dir)
    parse_console_log(arg.output_dir)

    # For final benchmark need to turn off control, do separate runs with varying window sizes


if __name__ == "__main__":
    main(sys.argv[1:])
