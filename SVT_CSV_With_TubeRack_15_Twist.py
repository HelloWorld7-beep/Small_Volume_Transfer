from opentrons import protocol_api

import csv, json
import math

#Note that initial volume is in mililiters?
csv_volume_data_raw = """
Initial_Wells,Initial_Volume,Liquid_Name,Description,Color
A1,0.5,Water,This is water,#00FF00
A2,0.5,Dye,This is dyed pink water,#FFC0CB

"""

csv_transfer_data_raw = """
Source_Well,Destination_Well,Transfer_Volume
A1,A2,15
A2,A6,15
"""

metadata = {
    "apiLevel": "2.16",
    "protocolName": "Small_Volume_Transfer_With_CSV",
    "description": """The goal is to make it so that we can change the protocol for transferring small volumes, with 
    volumes, wells, etc. without having to make a whole new protocol with the opentron protocol editor. Therefore, right 
    now I want to try to make it so that the python program can use CSV file data""",
    "author": "Abigail Lin"
    }

#Protocol context - https://docs.opentrons.com/v2/tutorial.html lines 29-102 aka the end
def run(protocol: protocol_api.ProtocolContext):
    #Loading modules lines 31-39
    #Load heating/cooling module and aluminum block
    #module_name = OT-2 module names (https://docs.opentrons.com/v2/new_modules.html#), location = slot num
    temp_mod = protocol.load_module(
        module_name="temperature module gen2", location="3"
    )
    temp_tubes = temp_mod.load_labware(
        "opentrons_24_aluminumblock_nest_1.5ml_snapcap"
    )

    #Load the tube rack line 41-42
    tube_rack = protocol.load_labware("opentrons_15_tuberack_falcon_15ml_conical", 5)


    #Load thermocycler line 45-46
    tc_mod = protocol.load_module(module_name="thermocyclerModuleV2")

    #Load the labware with its api name, look it up in labware library - https://labware.opentrons.com/ lines 48-52
    #After the api name, put comma and then which slot it is in on the Opentron, namely 1-11
    tips = protocol.load_labware(load_name="opentrons_96_tiprack_20ul", location=1)
    plate = tc_mod.load_labware("nest_96_wellplate_100ul_pcr_full_skirt", 10)
    left_pipette = protocol.load_instrument(instrument_name="p20_single_gen2", mount="left", tip_racks=[tips])

    #Open thermocycler lid line 54-55
    tc_mod.open_lid()

    #Code from 57-78 is to define initial starting volumes that we manually put into robot
    #Code to read from csv to "define intial volumes"
    #Discard the blank first line of csv
    csv_iv_data = csv_volume_data_raw.splitlines()[1:]
    csv_iv_reader = csv.DictReader(csv_iv_data)
    for csv_row in csv_iv_reader:
        #Define variables from CSV columns
        liquid_well = csv_row['Initial_Wells']
        liquid_volume = float(csv_row['Initial_Volume'])
        liquid_name = csv_row['Liquid_Name']
        liquid_description = csv_row['Description']
        liquid_color = csv_row['Color']

        #Now, configure the liquids in the protocol *Note for future can also add description/color
        current_liquid = protocol.define_liquid(
            name=liquid_name,
            description=liquid_description,
            display_color=liquid_color
        )

        #Configure the volumes in the wells (For this specific program, wells are in temp module. Can change)
        tube_rack[liquid_well].load_liquid(liquid=current_liquid, volume=liquid_volume)

    #Define the starting tip for the protocol, starts from here and goes to next available one after line 80-81
    left_pipette.starting_tip = tips.well('E1')

    #Code to read from csv to "transfer volumes" 83-the end
    #Discard the blank first line of csv
    csv_data = csv_transfer_data_raw.splitlines()[1:]
    csv_reader = csv.DictReader(csv_data)
    for csv_row in csv_reader:

        #Define variables from CSV columns
        source_well = csv_row['Source_Well']
        destination_well = csv_row['Destination_Well']
        transfer_volume = float(csv_row['Transfer_Volume'])

        #Now, start the volume transfer
        #Pick up the next tip, will always pick up the next available tip
        left_pipette.pick_up_tip()
        #Aspirate [take in] liquid, with this format (amount in microliters, well location)
        left_pipette.aspirate(transfer_volume, tube_rack[source_well].top(z=-35))
        #Dispense liquid, with this format (amount in microliters, well location)
        left_pipette.dispense(transfer_volume, plate[destination_well])
        #Discard the tip
        left_pipette.drop_tip()



