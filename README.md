# sip-packager

## Description:
The program produces a minimum profile CSIP package that can be delivered to an e-archive system if it adheres to the E-ARK specifications **CSIP v.2.1.0**, **SIP v.2.1.0** and **CITS-ERMS v.2.10**.

The specifications include a folder structure within a ZIP-file along with at least two metadatafiles, mets.xml and erms.xml that describe the delivery of the SIP and its representations with metadata from the **KLASSA 2.1** classification schema for records management in the public sector.

### Who is the program for?
The program is mainly intended for people in the regional or municipal sectors in Sweden who work with e-archiving and digital preservation.

The specifications that this program adheres to in the creation of Submission information packages were appointed as FGS Paketstruktur 2.0 and FGS för Ärende 2.0 by the national archives, Riksarkivet, in 2023.

## Why is this program needed?

Although the specifications have been appointed for over three years, very few systems or other methods exist that produces SIPs according to these standards(!!). Most of the time, FGS Paketstruktur 1.2 (or even the unappointed project version) is being used alongside FGS för Ärende 1.0. And that's for when an actual standard is being used and not a strictly local description. It is also common that organizations create csv-files and then map that data on to elements from FGS för Ärende 1.0.

The purpose of this program is to make it a little easier for archival institutions in Sweden to actually begin making use of these standards. The program also removes **most** of the manual work with preparing material for delivery. No more manually typing data into csv *(just a few lines in JSON)*!

## How the program works:
The program currently uses a command-line interface (CLI) to run the programs:

* csip_structure.py (obligatory)
* normalize_filenames.py (optional)
* cits_erms.py (obligatory)
* mets.py (obligatory)
* package_to_zip.py (obligatory)

as default when the the program:

* run_sip_packager.py

is ran through the CLI.

### Commands:

#### To run the entire suite:
Type:<br>
`python -m src.cli.run_sip_packager`<br>
when in the project root, `..\sip-packager` and the programs will be run in the correct order. You will be promted to answer a "y/n" terminal prompt to run or skip the optional program.

#### To run each program as standalone:
All core generator programs (csip_structure, cits_erms, mets, package_to_zip) and the tool (normalize_filenames) can also be ran as standalone and breaking with the default paths given in run_config.json. Note however that they require the CSIP folder structure (as argument for --root) in order to be ran properly.

They all take the first command-line argument, `--root`, as a replacement for "sip_root".

They all take the command-line argument, `-o` or `--output` as a replacement for "erms_input".

#### enter debug-mode
If something goes wrong when you attempt to run a program, add:<br>
`-v` or `--verbose` <br>as a command-line argument when running the program. This puts you in debug mode where you will get more info about what succeeds and what fails when you attempt to run the program.

## Before you start!
To run the programs properly, you do have to perform **some** manual typing and do a little bit of setup.

### pre-existing folder structure
To run the program successfully, it requires that you can provide a folder structure with the names of the folders corresponding to classification designations from Klassa 2.1, such as "1.1.1" or "3.6.5" and so on. Directly under these folders there should be files. Each folder will be created as an aggregation element of type "class" in the erms.xml file. All files under the folder will be structured as child record elements to that particular aggregation element.

#### example folder structure:

![](/docs/example_structure.png)

### external libraries
Besides needing python, the project also requires you to install some external libraries.

#### lxml

to install, run<br> `pip install lxml`

#### pandas

to install, run<br> `pip install pandas`

### run_config.json
In the subfolder /config there is a configuration file called "run_config.json". It holds three key-value pairs that are part of the setup of the program.

* The first pair gives a path to where you want the SIP package to be created.

* The second pair gives the path to the root folder of your input.

* The third pair is a safety measure that tells the program how many files it *can* take as a maximum. This value is set to 1000 as default, but you can change it anytime you want.

### klassa_processer.json
In the subfolder config there is a configuration file called "klassa_processer.json". This file holds key-value pairs for **ALL** areas of operations (verksamhetsområden, VO, in swedish) and groups of processes (processgrupper, PG, in swedish) from Klassa 2.1 with the designation as key and description as value. The program cits-erms.py checks the name of the folder to look up its corresponding key in the JSON-file and gives the value of the key as the value of that aggregations description element.

### submission_agreement.json
In the subfolder config/profiles there is a configuration file called "submission_agreement.json". This file holds 17 key value pairs and is used to give values to the mets-file that describes a few fields regarding the submission that might change between each delivery. Each key-value pair maps to a corresponding element in CSIP. Read through the CSIP and SIP specifications if any pair is not self-explanatory.


## Additional tools:
Apart from the core program to create a valid CSIP package there are two additional tools included in this project in the subfolder src/tools:

* normalize_filenames.py

* extract_klassa.py

### normalize_filenames.py
This program is run as an option, but could be used as a standalone tool for changing out the common swedish characters, 'ä', 'å' and 'ö' as well as whitespaces in filenames. It is included in this project since Riksarkivet, in all iterations of FGS för paktestruktur have had the additinal requirement that only the following characters are allowed:<br>
`a..z, A..Z, 0..9, ”-” and ”_”`

The program replaces whitespace with "_" and äÄ with aA, åÅ with aA and öÖ with oO.

### extract_klassa.py
This program is only used as a standalone tool. It can be used wholly outside of the scope of this project as well, and the main impetus for making the program is that there is a real lack of publically available, machine readable data regarding the classification of information in the public sector in sweden.

Most regional or municipal agencies uses some variant of either KLASSA (made public through SKR) or VerkSAM (developed by Sydarkivera). This program just uses the basic KLASSA 2.1 as default, but most public agencies have made at least some local changed to that classification schema.

This program allows you to easily produce a json-file that is adapted to your local classifications so long as you can provide a cleaned up XLSX-file that is structured like the file "Klassa_2_1.xlsx" found in the subfolder /config.

The program takes the file "Klassa_2_1.xlsx" as default, but this can be overwritten by using a command-line argument. If you want to extract data from another XLSX-file, place it in the config subfolder and give its filename as a command-line argument. For instance, if you have a file called "klassa_local.xlsx" in the config folder run:<br>
`python -m src.tools.extract klassa.py "klassa_local.xlsx"`<br>to overwrite the default file to be read.

In order for this project to be truly useful, it would require more data based on the classification of the information, such as access restrictions, retention policies and so forth. With this data in a machine-readable format it could then be mapped to metadata elements in the erms.xml file simple based off of the name of the folder that the file is in!

## About
This repository was originally handed in as my final project for the CS50x course in 2026.

