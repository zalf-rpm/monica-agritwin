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


class IrrigationManager:
    def __init__(self, irrigated_crops_map="irrigated_crops.json"):
        self.irrigated_crops_map = irrigated_crops_map
        with open(irrigated_crops_map) as file:
            self.irrigated_crops_map = json.load(file)

    def should_be_irrigated_by_crop_id(self, crop_id):
        # iterate over the crops and cultivars in the irrigated crops map
        for specie in self.irrigated_crops_map["crops"]:
            print(f"Checking species: {specie['SpeciesName']}")
            for cultivar in specie["Cultivars"]:
                # check if the crop id is in the list of crop ids
                if isinstance(cultivar["CropID"], list):
                    # if crop ID is a list, check each crop ID in the list
                    # if the crop ID is in the list, return the irrigated value
                    if crop_id in cultivar["CropID"]:
                        print(f'{crop_id} is irrigated.')
                        return cultivar["Irrigated"]
                else:
                    # check if the crop ID passed in is equal to the crop ID in irrigated_crops.json
                    if crop_id == cultivar["CropID"]:
                        print(f'{crop_id} is irrigated.')
                        return cultivar["Irrigated"]

        # return False if the crop type based on crop ID should not be irrigated
        print(f'{crop_id} is not irrigated.')
        return False

    def should_be_irrigated_by_cultivar_name(self, cultivar_name):
        # iterate over the crops and cultivars in the irrigated crops map
        for specie in self.irrigated_crops_map["crops"]:
            print(f"Checking species: {specie['SpeciesName']}")
            for cultivar in specie["Cultivars"]:
                # check if the cultivar name passed in is equal to the crop ID in irrigated_crops.json
                if cultivar_name == cultivar["CultivarName"]:
                    print(f'{cultivar_name} is irrigated.')
                    return cultivar["Irrigated"]

        # return False if the crop type based on cultivar name should not be irrigated
        print(f'{cultivar_name} is not irrigated.')
        return False


if __name__ == "__main__":
    # test the irrigation manager
    irrigation_module = IrrigationManager("irrigated_crops.json")
    # test the should_be_irrigated_by_crop_id function
    # assert irrigation_module.should_be_irrigated_by_crop_id("SM") is True
    # assert irrigation_module.should_be_irrigated_by_crop_id("MEP") is True
    # assert irrigation_module.should_be_irrigated_by_crop_id("ZR") is True
    # assert irrigation_module.should_be_irrigated_by_crop_id("WW") is True
    # assert irrigation_module.should_be_irrigated_by_crop_id("WW_sfix_hauto") is True
    # assert irrigation_module.should_be_irrigated_by_crop_id("WR") is False
    # test the should_be_irrigated_by_cultivar_name function
    # assert irrigation_module.should_be_irrigated_by_cultivar_name("Silage Maize") is True
    # assert irrigation_module.should_be_irrigated_by_cultivar_name("Moderate Early Potato") is True
    # assert irrigation_module.should_be_irrigated_by_cultivar_name("Sugar Beet") is True
    # assert irrigation_module.should_be_irrigated_by_cultivar_name("Winter Wheat") is True
    # assert irrigation_module.should_be_irrigated_by_cultivar_name("Winter Rye") is False
