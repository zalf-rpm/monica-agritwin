#!/usr/bin/python
# -*- coding: UTF-8

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/. */

# Authors:
# Rachel Escueta <rachel.escueta@zalf.de>
#
# Maintainers:
# Currently maintained by the authors.
#
# This file has been created at ZALF.
# Copyright: Leibniz Centre for Agricultural Landscape Research (ZALF)

import json
import os
import glob
import re
from datetime import datetime, timedelta
import numpy as np
from pyproj import CRS, Transformer

class IrrigationManager:
    def __init__(self, irrigated_crops_map="irrigated_crops.json"):
        self.irrigated_crops_map = irrigated_crops_map
        with open(irrigated_crops_map) as file:
            self.irrigated_crops_map = json.load(file)

    def should_be_irrigated_by_crop_id(self, crop_id):
        # iterate over the crops and cultivars in the irrigated crops map
        for specie in self.irrigated_crops_map["crops"]:
            # print(f"Checking species: {specie['SpeciesName']}")
            for cultivar in specie["Cultivars"]:
                # check if the crop id is in the list of crop ids
                if isinstance(cultivar["CropID"], list):
                    # if crop ID is a list, check each crop ID in the list
                    # if the crop ID is in the list, return the irrigated value
                    if crop_id in cultivar["CropID"]:
                        # print(f'{crop_id} is irrigated.')
                        return cultivar["Irrigated"]
                else:
                    # check if the crop ID passed in is equal to the crop ID in irrigated_crops.json
                    if crop_id == cultivar["CropID"]:
                        # print(f'{crop_id} is irrigated.')
                        return cultivar["Irrigated"]

        # return False if the crop type based on crop ID should not be irrigated
        # print(f'{crop_id} is not irrigated.')
        return False

    def should_be_irrigated_by_cultivar_name(self, cultivar_name):
        # iterate over the crops and cultivars in the irrigated crops map
        for specie in self.irrigated_crops_map["crops"]:
            # print(f"Checking species: {specie['SpeciesName']}")
            for cultivar in specie["Cultivars"]:
                # check if the cultivar name passed in is equal to the crop ID in irrigated_crops.json
                if cultivar_name == cultivar["CultivarName"]:
                    # print(f'{cultivar_name} is irrigated.')
                    return cultivar["Irrigated"]

        # return False if the crop type based on cultivar name should not be irrigated
        # print(f'{cultivar_name} is not irrigated.')
        return False

    def configure_grid_series(self, irr_folder_abs, soil_crs, soil_crs_to_x_transformers, Mrunlib, period_days=14,
                              spacing_days=3, preload=True):
        """ Configure and preload a time series of irrigation grids from the given folder."""
        self._irr_folder_abs = irr_folder_abs
        self._period_days = period_days
        self._spacing_days = spacing_days

        self._irr_files = _find_irrigation_grids(irr_folder_abs)

        # Precompute periods (window and event dates)
        self._irr_periods = []
        for last_date, fp in self._irr_files:
            wstart, wend, event_dates = _build_irrigation_schedule(last_date, period_days=self._period_days,
                                                                   spacing_days=self._spacing_days)
            self._irr_periods.append({
                "last_date": last_date,
                "file": fp,
                "window_start": wstart,
                "window_end": wend,
                "event_dates": event_dates
            })

        self._grid_cache = _IrrigationGridCache(soil_crs, soil_crs_to_x_transformers, Mrunlib)

        if preload:
            for last_date, fp in self._irr_files:
                self._grid_cache.get_interp(fp)

    def build_irrigation_worksteps_for_cell(self, sr, sh, sim_start, sim_end, irrig_start=(6, 1), irrig_end=(8, 31)):
        """ Returns list of irrigation worksteps for the cell"""
        if not hasattr(self, "_irr_periods"):
            raise RuntimeError("IrrigationManager not configured. Call configure_grid_series(...) first.")

        def _get_period_plan(sim_start_, sim_end_, irrig_start_, irrig_end_):
            key = (sim_start_, sim_end_, irrig_start_, irrig_end_, self._period_days)

            if not hasattr(self, "_period_plan_cache"):
                self._period_plan_cache = {}
            if key in self._period_plan_cache:
                return self._period_plan_cache[key]

            # Build irrigation windows once
            irrig_windows = []
            for y in range(sim_start_.year, sim_end_.year + 1):
                w0 = datetime(y, irrig_start_[0], irrig_start_[1]).date()
                w1 = datetime(y, irrig_end_[0], irrig_end_[1]).date()
                irrig_windows.append((w0, w1))

            # Pre-filter periods based on sim window
            relevant_periods = [p for p in self._irr_periods if p["window_end"] >= sim_start_ and p["window_start"] <= sim_end_]

            # Function to calculate overlapping days between grid's 14-day window and irrigation windows
            def overlap_days(start_a, end_a, start_b, end_b):
                overlap_start = max(start_a, start_b)
                overlap_end = min(end_a, end_b)
                if overlap_end < overlap_start:
                    return 0
                return (overlap_end - overlap_start).days + 1

            # Function to check if a date is within any irrigation window
            def in_irrigation_window(d):
                # Since irrig_windows is small, we can just check year
                for wstart, wend in irrig_windows:
                    if wstart.year == d.year:
                        return wstart <= d <= wend
                return False

            plan = []
            for p in relevant_periods:
                # Calculate overlap between the irrigation window and the grid's 14-day window
                irrigation_window_overlap = 0
                # Only check windows that might overlap with this period (same year)
                for wstart, wend in irrig_windows:
                    if wstart.year == p["window_start"].year or wend.year == p["window_end"].year:
                        irrigation_window_overlap += overlap_days(p["window_start"], p["window_end"], wstart, wend)

                irrigation_window_overlap = min(irrigation_window_overlap, self._period_days)
                if irrigation_window_overlap <= 0:
                    continue

                overlap_factor = irrigation_window_overlap / float(self._period_days)

                # Select irrigation event dates within the simulation window and irrigation windows
                dates = [d for d in p["event_dates"] if sim_start_ <= d <= sim_end_ and in_irrigation_window(d)]
                if not dates:
                    continue

                plan.append({
                    "file": p["file"],
                    "overlap_factor": overlap_factor,
                    "dates": dates,
                })

            self._period_plan_cache[key] = plan
            return plan

        worksteps = []
        scheduled_dates = set()

        plan = _get_period_plan(sim_start, sim_end, irrig_start, irrig_end)

        # Cache transformed coordinates
        transformed_xy = {}

        for item in plan:
            # Get grid, CRS, and nodata for this irrigation grid
            irr_crs, grid_geom, grid = self._grid_cache.get_interp(item["file"])

            # Transform soil coordinates to irrigation grid CRS once per CRS and reuse
            if irr_crs in transformed_xy:
                rr, rh = transformed_xy[irr_crs]
            else:
                rr, rh = self._grid_cache.transform_to_irr_crs(irr_crs, sr, sh)
                transformed_xy[irr_crs] = (rr, rh)

            # Read irrigation amount for this cell from the grid
            total_mm = self._grid_cache.value_mm_transformed(grid_geom, grid, rr, rh)
            if total_mm is None or total_mm <= 0:
                continue

            # Scale total irrigation amount based on overlap with irrigation windows
            scaled_total = total_mm * item["overlap_factor"]
            if scaled_total <= 0:
                continue

            # Select irrigation event dates within the simulation window and irrigation windows
            dates_to_use = [d for d in item["dates"] if d not in scheduled_dates]
            if not dates_to_use:
                continue

            # Distribute total irrigation amount
            per_event_mm = scaled_total / len(dates_to_use)

            for d in dates_to_use:
                worksteps.append(_make_irrigation_workstep(d, per_event_mm))
                scheduled_dates.add(d)

        worksteps.sort(key=lambda ws: ws.get("date", "9999-12-31"))
        return worksteps


# Regex pattern to extract date from irrigation file name, for example: BB_iwu_2017-04-21_100_25832_etrs89-utm32n.asc
_IRR_DATE_RE = re.compile(r".*_(\d{4}-\d{2}-\d{2})_.*\.asc$", re.IGNORECASE)

def _find_irrigation_grids(folder_abs):
    """Find all irrigation grid files in the given folder and extract their dates."""
    files = sorted(glob.glob(os.path.join(folder_abs, "*.asc")))
    dated = []
    for fp in files:
        # Extract date from filename using regex
        m = _IRR_DATE_RE.match(fp.replace("\\", "/"))
        if not m:
            continue
        last_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        dated.append((last_date, fp))
    dated.sort(key=lambda x: x[0])
    if not dated:
        raise RuntimeError(f"No irrigation grids found with parsable dates in: {folder_abs}")
    return dated

def _build_irrigation_schedule(last_date, period_days=14, spacing_days=3):
    """
    Build a list of irrigation dates occurring every 3 days within a 14-day window ending on last_date.
    last_date is the final irrigation date of the 14-day window.
    Irrigation event happens every 3 days, going backward from last_date, within a 14-day window.
    """
    window_start = last_date - timedelta(days=period_days - 1)

    dates = []
    offset = 0
    while offset <= (period_days - 1):
        # Calculate the irrigation date by stepping backward from the last date in the window
        d = last_date - timedelta(days=offset)
        # Stop if the calculated date falls before the window start
        if d < window_start:
            break
        dates.append(d)
        offset += spacing_days

    dates.sort()
    return window_start, last_date, dates

def _make_irrigation_workstep(d, amount_mm):
    """Create an irrigation workstep dictionary for the given date and amount in mm."""
    return {
        "type": "Irrigation",
        "date": d.isoformat(),
        "amount": [float(amount_mm), "mm"]
    }

class _IrrigationGridCache:
    """
    Lazy-loads ASC grids and builds interpolators. Caches per file path.
    Requires Mrunlib methods to read header and create interpolator.
    """
    def __init__(self, soil_crs, soil_crs_to_x_transformers, Mrunlib):
        self.soil_crs = soil_crs
        self.soil_crs_to_x_transformers = soil_crs_to_x_transformers
        self.Mrunlib = Mrunlib
        self.cache = {}
        self._loads = 0

    def _get_interp(self, fp):
        if fp in self.cache:
            return self.cache[fp]

        self._loads += 1

        # Extract EPSG code from filename
        parts = os.path.basename(fp).split("_")
        if len(parts) < 5:
            raise RuntimeError(f"Unexpected irrigation filename format (need EPSG at index 4): {fp}")
        epsg_code = int(parts[4])
        irr_crs = CRS.from_epsg(epsg_code)

        if irr_crs not in self.soil_crs_to_x_transformers:
            self.soil_crs_to_x_transformers[irr_crs] = Transformer.from_crs(self.soil_crs, irr_crs, always_xy=True)

        meta, _ = self.Mrunlib.read_header(fp)
        grid = np.loadtxt(fp, dtype=float, skiprows=6)
        nodata = float(meta["nodata_value"])

        cs = float(meta["cellsize"])
        grid_geom = (
            int(meta["ncols"]),
            int(meta["nrows"]),
            cs,
            1.0 / cs,
            float(meta["xllcorner"]),
            float(meta["yllcorner"]),
            nodata
        )

        self.cache[fp] = (irr_crs, grid_geom, grid)
        return self.cache[fp]

    def get_interp(self, fp):
        return self._get_interp(fp)

    def transform_to_irr_crs(self, irr_crs, sr, sh):
        if irr_crs == self.soil_crs:
            return sr, sh
        transformer = self.soil_crs_to_x_transformers[irr_crs]
        rr, rh = transformer.transform(sr, sh)
        return rr, rh

    @staticmethod
    def value_mm_transformed(grid_geom, grid, rr, rh):
        if not hasattr(_IrrigationGridCache, "_interp_calls"):
            _IrrigationGridCache._interp_calls = 0
        _IrrigationGridCache._interp_calls += 1

        ncols, nrows, cs, inv_cs, xll, yll, nodata = grid_geom

        col = int((rr - xll) * inv_cs)
        if col < 0 or col >= ncols:
            return None

        row_from_bottom = int((rh - yll) * inv_cs)
        row = (nrows - 1) - row_from_bottom
        if row < 0 or row >= nrows:
            return None

        v = float(grid[row, col])
        if v == nodata:
            return None
        return v


if __name__ == "__main__":
    irrigation_module = IrrigationManager("irrigated_crops.json")
