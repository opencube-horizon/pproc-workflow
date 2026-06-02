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
    elif "us" in duration_str:
        return float(duration_str.rstrip("us")) / 1000000
    try:
        strip_s = duration_str.rstrip("s")
        duration = float(strip_s)
    except ValueError:
        assert "m" in strip_s
        minutes, seconds = map(float, strip_s.split("m"))
        duration = 60 * minutes + seconds
    return duration


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
        in_secs = np.asarray(list(map(duration_in_sec, key_items[duration_index][1])))[
            function_occurrences
        ]
        avg_function_time = np.mean(in_secs)
        std_function_time = np.std(in_secs)
        print(
            f"Function {function}, occurrences {np.sum(function_occurrences)}, average {avg_function_time:.3f}s, stdev {std_function_time:.3f}s."
        )
        if function in ["transfer", "efi", "sot"]:
            np.savetxt(f"{output_dir}/{function}.txt", in_secs)


def parse_console_log(output_dir):
    read = []
    write = []
    with open(f"{output_dir}/console.log") as console_log:
        for line in console_log:
            if "RETRIEVE" in line:
                log_bytes = float(search("size: (.+?) bytes", line))
                log_time = float(search("wall time: (.+?) s", line))
                read.append(log_bytes / log_time)
            if "WRITE" in line:
                log_bytes = float(search("size: (.+?) bytes", line))
                log_time = float(search("wall time: (.+?) s", line))
                write.append(log_bytes / log_time)

    mean_read = np.mean(read)
    std_read = np.std(read)
    mean_write = np.mean(write)
    std_write = np.std(write)
    np.savetxt(f"{output_dir}/read_rate.txt", np.asarray(read)/10**6)
    np.savetxt(f"{output_dir}/write_rate.txt", np.asarray(write)/10**6)
    print("\nConsole Log")
    print(
        f"    Function read, occurrences {len(read)}, average rate {mean_read:.3f} bytes/s ({mean_read/10**6:.3f} MB/s), stdev rate {std_read:.3f} bytes/s ({std_read/10**6:.3f} MB/s)"
    )
    print(
        f"    Function write, occurrences {len(write)}, average rate {mean_write:.3f} bytes/s ({mean_write/10**6:.3f} MB/s), stdev rate {std_write:.3f} bytes/s ({std_write/10**6:.3f} MB/s)"
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
