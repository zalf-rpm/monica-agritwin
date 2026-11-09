#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# Authors:
# Michael Berg-Mohnicke <michael.berg@zalf.de>
#
# Maintainers:
# Currently maintained by the authors.
#
# This file has been created at the Institute of
# Landscape Systems Analysis at the ZALF.
# Copyright (C: Leibniz Centre for Agricultural Landscape Research (ZALF)

from collections import defaultdict
import csv
import os
import sys
import zmq

PATHS = {
    "re-local-remote": {
        "path-to-projects-dir": "./data/germany/",
        "path-to-csv-output-dir": "D:/monica_agritwin/out/csv-out/"
    },
    "remoteConsumer-remoteMonica": {
        "path-to-projects-dir": "/project/monica-agritwin/",
        "path-to-csv-output-dir": "/out/csv-out/"
    }
}

def heat_stress_cycles(msg):
    meta = msg["customId"]
    params = meta["heat_parameters"]
    begin = params["BeginSensitivePhaseHeatStress"]
    end = params["EndSensitivePhaseHeatStress"]
    critical = params["CriticalTemperatureHeatStress"]
    daily = {}
    for section in msg.get("data", []):
        if section.get("origSpec") in ('"daily"', 'daily'):
            for day in section.get("results", []):
                daily[(day["CM-count"], day["Date"])] = day
    totals = defaultdict(float)
    if not daily:
        raise ValueError("Missing daily heat-stress outputs")
    for (cycle, _), day in daily.items():
        # Calculate stress during the sensitive phase
        if day.get("Crop") and begin <= day["TempSum"] < end:
            tphoto = day["Tmax"] - (day["Tmax"] - day["Tmin"]) / 4.0
            totals[cycle] += max(0.0, tphoto - critical)
    allowed = meta.get("crop_years")
    for cycle, values in create_output(msg).items():
        if "Year" in values and (allowed is None or int(values["Year"]) in allowed):
            yield cycle, int(values["Year"]), totals[cycle]  # cycle number, year, accumulated heat stress


def aggregate_heat_stress(msg, aggregates):
    """Accumulate cell totals by setup, year, cycle, NUTS3 and soil type."""
    meta = msg["customId"]
    for cycle, year, total in heat_stress_cycles(msg):
        groups = aggregates[(meta["setup_id"], year, cycle)]
        key = (meta["nuts_id"], meta["soil_type"])
        total_and_count = groups.setdefault(key, [0.0, 0])
        total_and_count[0] += total
        total_and_count[1] += 1


def write_heat_stress_csv(aggregates, output_dir):
    """Write mean per NUTS3 region/soil pair, including zero-stress cells."""
    for (setup_id, year, cycle), groups in aggregates.items():
        directory = os.path.join(output_dir, str(setup_id))
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"heat-stress_{year}_{cycle}.csv")
        with open(path, "w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow(["SumStressTT", "Region", "SoilType"])
            for (region, soil_type), (total, count) in sorted(
                    groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
                writer.writerow([total / count, region, soil_type])


def create_output(msg):
    cm_count_to_vals = defaultdict(dict)
    for data in msg.get("data", []):
        results = data.get("results", [])

        is_daily_section = data.get("origSpec", "") in ('"daily"', 'daily')

        if is_daily_section:
            continue

        for vals in results:
            if "CM-count" in vals:
                cm_count_to_vals[vals["CM-count"]].update(vals)

    if not cm_count_to_vals:
        return cm_count_to_vals
    last_cmc = max(cm_count_to_vals)
    if "Year" not in cm_count_to_vals[last_cmc]:
        cm_count_to_vals.pop(last_cmc)

    return cm_count_to_vals


def run_consumer(leave_after_finished_run=True, server={"server": None, "port": None}, shared_id=None):
    """collect data from workers"""

    config = {
        "mode": "re-local-remote",
        "port": server["port"] if server["port"] else "7778",
        "server": server["server"] if server["server"] else "login01.cluster.zalf.de",
        "start-row": "0",
        "end-row": "-1",
        "shared_id": shared_id,
        "timeout": 600000  # 10 minutes
    }

    if len(sys.argv) > 1 and __name__ == "__main__":
        for arg in sys.argv[1:]:
            k, v = arg.split("=")
            if k in config:
                config[k] = v

    paths = PATHS[config["mode"]]

    if not "csv-out" in config:
        config["csv-out"] = paths["path-to-csv-output-dir"]

    print("consumer config:", config)

    context = zmq.Context()
    if config["shared_id"]:
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY, config["shared_id"])
    else:
        socket = context.socket(zmq.PULL)

    socket.connect("tcp://" + config["server"] + ":" + config["port"])
    socket.RCVTIMEO = config["timeout"]
    leave = False

    heat_aggregates = defaultdict(dict)

    def process_message(msg):
        if len(msg["errors"]) > 0:
            print("There were errors in message:", msg, "\nSkipping message!")
            return

        leave = False

        custom_id = msg["customId"]
        is_nodata = custom_id["nodata"]

        if not is_nodata:
            aggregate_heat_stress(msg, heat_aggregates)

        return leave

    try:
        while not leave:
            try:
                msg = socket.recv_json()
                leave = process_message(msg)
            except zmq.error.Again as _e:
                print('no response from the server (with "timeout"=%d ms) ' % socket.RCVTIMEO)
                break
            except Exception as e:
                print("Exception:", e)
    finally:
        write_heat_stress_csv(heat_aggregates, config["csv-out"])
        socket.close()
        context.term()

    print("exiting run_consumer()")


if __name__ == "__main__":
    run_consumer()
