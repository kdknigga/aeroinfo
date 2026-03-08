                      Federal Aviation
                      Administration


Readme
Date:           February 19, 2026

To:             Users of the Aeronautical Information Service (AIS) 28 Day NASR Subscription

From:           Aeronautical Information Services

Subject:       Comma-Separated Values (CSV) files




There have been requests from users internal and external for an alternative to the flat text fixed
length legacy subscriber files. The CSV files documented here are an attempt to meet this need
of a more user-friendly data file. There is a full complement of the legacy subscriber data coded
as CSV. Each CSV grouping is accompanied by a DATA LAYOUT document and a CSV
DATA STRUCTURE file. See the Data Layout Document and CSV Data Structure File for
further information on what data (including data types, max length, nullable, how displayed and
organized) is contained in each. For those looking to transition from TXTs to CSVs, we have
provided a Legacy TXT to CSV Mapping Document. You can Download it from a link at the
top of the Preview and Current 28 Day NASR Subscription page.

Since CSV subscriber files are a new product, we may be making minor changes to the files
through 2024 as user input is incorporated. The data within the files is valid data and
operationally usable - like the legacy txt. Only the structure of the file may change. Like we do
with the current TXT subscriber files, we will provide advance notice of format changes prior to
release.

DATUM

The CSV subscriber files do not cite a datum for geodetic coordinates. All US coordinate
information provided currently references NAD 83.

SUNSETTING OF LEGACY .TXT SUBSCRIBER FILES
FAA is in the process of sunsetting the legacy .txt NASR subscriber files. The timeframe for
sunsetting .txt subscriber files is targeted for the 24 Dec 2026 AIRAC cycle. The .txt format
NASR subscriber files will be replaced with a set of .csv format subscriber files, which are
currently available. A Legacy TXT to CSV Mapping Document is available for download via the
main 28-Day Subscription page to ease transition.
NOTE: An enhancement to the NASR database is scheduled for release this year, however, a
date has yet to be determined. Once a date is confirmed, Users of the NASR Subscriber Files will
be notified. After this next NASR release, .txt subscriber files will no longer contain new data
entrants in NASR. New data entrants will be available only in .csv subscriber files.


AIR TRAFFIC CONTROL COMMUNICATION CSV files – ATC_*.csv

The ATC_*.csv files were designed from a deconstruction of the legacy TWR.txt and AFF.txt
Subscriber Files. ATC_*.csv files are not a complete replacement but a logical grouping of
Tower specific data, Radio Call and Operator Data from TWR1 record, Services from TWR4
record, ATIS from TWR9 record, APCH/DEP Primary/Secondary Operator Hours from TWR2
record, ARTCC/CERAP data from AFF1 record, Remarks from the TWR6 record and
ARTCC/CERAP remarks from AFF2.

The ATC_*.csv consists of the following files: ATC_BASE.csv, ATC_ATIS.csv, ATC_SVC.csv
and ATC_RMK.csv.

AIRPORT CSV files – APT_*.csv

COMING FORMAT CHANGE: AIRPORT (APT_RWY.csv) PAVEMENT
CLASSIFICATION FIELD CHANGE – Software changes to incorporate Pavement
Classification Rating (PCR) in the APT_RWY.csv NASR Subscriber File are currently planned
for a future release of the NASR Subscriber Files. A new “PAVEMENT CLASSIFICATION”
column will be added to the APT_RWY.csv subscriber file which will denote either “PCN” or
“PCR”. With the transition towards utilizing the PCR method for rating the strength of an airport
runway, the current PCN fields will reflect either PCN values or PCR values (but not both), or
null. For PCN or PCR, the PCN/PCR number is concatenated with the Pavement type, Subgrade
Strength, Tire Pressure, and Evaluation Method. Since PCR Number allows for up to 4
characters, the PCN/PCR Number field will increase from 3 characters to 4 characters. Initial
population of the new "PAVEMENT CLASSIFICATION" data field has yet to be determined.
Therefore, the current practice of displaying PCN values in the data fields and PCR values in a
reference remark may continue after the deployment of the NASR enhancement until the fields
can be properly populated and the reference remarks removed.

UPDATE for 11/27/25: AIRPORT (APT_BASE.csv) NEW FUEL TYPES – Three new fuel
types are available in the .csv subscriber files beginning with the 27 November 2025 AIRAC
cycle.
   • H – Hydrogen
   • G100UL – Unleaded Grade 100 gasoline. Note: G100 in the .txt subscriber file is the
        same as G100UL in the .csv subscriber file
   • 100R - Unleaded Grade 100 gasoline
NOTE: G100 and G100UL are the same fuel types. Due to character limit constraints associated
with the .txt subscriber file format, G100UL has been truncated to G100.
UPDATE for 12/26/24: AIRPORT (APT_BASE.csv) BASED AIRCRAFT AND ANNUAL
OPERATIONS DATA – The based aircraft and annual operations data fields found in the
APT_BASE.csv data set have been removed from the APT_BASE.csv file beginning with the
December 26, 2024 effective cycle. These fields in the CSV APT_BASE.csv subscriber file are
NULL beginning with the 09/05/2024 effective cycle.

UPDATE for 09/05/24: AIRPORT (APT_BASE.csv) BASED AIRCRAFT AND ANNUAL
OPERATIONS DATA – The based aircraft and annual operations data in the APT_BASE.csv
data set, elements A90-96 and A100-105, has been removed from the NASR database and is no
longer contained in NASR Subscriber files as of the September 5, 2024 effective date. These
fields in the CSV APT_BASE.csv subscriber file are NULL. Information regarding based
aircraft can be found at the National Based Aircraft Inventory Program located on the web at
https://basedaircraft.com/ . Information on aircraft operations is available from FAA’s FAA
Aviation System Performance Metrics https://aspm.faa.gov.

The APT_*.csv files were designed as an alternative file type/layout to the legacy APT.txt
subscriber file. It contains the full complement of data that is found in the APT.txt, with the
exception of any frequency data which is now located in the FRQ.csv. Data, while comparable
to the legacy APT.txt, is in some cases organized and presented in a different way. The
APT_*.csv files contain data that was not previously included in APT.txt subscriber – e.g. all
airport contact information, not just OWNER/MANAGER, all Fuel Types, etc.

The APT_*.csv consists of the following files: APT_ARS.csv, APT_ATT.csv, APT_BASE.csv,
APT_CON.csv, APT_RMK.csv, APT_RWY.csv and APT_RWY_END.csv.

AIRSPACE FIXES CSV files – FIX_*.csv

COMING FORMAT CHANGE: FIX (FIX_BASE.csv, FIX_CHRT.csv) NEW CHARTING
TYPE – A new ATS Airway Designation in the AWY_BASE.csv NASR Subscriber File is
planned for a future release of the NASR Subscriber Files. SP = SPECIAL ROUTE Designation
and description will be added to the AWY_BASE.csv Subscriber File. "Special, non-regulatory
(non-Part 95) ZK Routes are low-level, IFR, performance-based (RNAV) navigation routes
primarily used by Helicopter Air Ambulance operators. They are not included on public charts.
You may not file or use these routes without approval from FAA Flight Standards. These Special
airways will be updated on a 56-day cycle.". Fixes that are part of these routes will be denoted
with a "SPECIAL ENROUTE" charting type in FIX_BASE.csv under "CHARTS" and in
FIX_CHRT.csv under "CHARTING TYPE DESC".

The FIX_*.csv files were designed as an alternative file type/layout to the legacy FIX.txt
subscriber file. It contains the full complement of data that is found in the FIX.txt. Data, while
comparable to the legacy FIX.txt, is in some cases organized and presented in a different way.

The FIX_*.csv consists of the following files: FIX_BASE.csv, FIX_CHRT.csv and
FIX_NAV.csv.

AIRWAY CSV files – AWY_*.csv
COMING FORMAT CHANGE: ATS NON-REGULATORY AIRWAYS (AWY_BASE.csv)
ATS AIRWAY DESIGNATION ADDITION – A new ATS Airway Designation in the
AWY_BASE.csv NASR Subscriber File is planned for a future release of the NASR Subscriber
Files. SP = SPECIAL ROUTE Designation and description will be added to the
AWY_BASE.csv Subscriber File. "Special, non-regulatory (non-Part 95) ZK Routes are low-
level, IFR, performance-based (RNAV) navigation routes primarily used by Helicopter Air
Ambulance operators. They are not included on public charts. You may not file or use these
routes without approval from FAA Flight Standards. These Special airways will be updated on a
56-day cycle.".

UPDATE for 09/04/25: Beginning with the August 7, 2025 effective date, four AK Capstone Routes
were added to the AWY_*.csv file. Users must have specific FAA authorization, through Operation
Specifications or Letter of Authorization, obtained from Flight Standards to use the following routes:
R2010, R2015, R2020, R2025. The aircraft’s lateral deviation display scaling must support the RNP
1 EnRoute Operations.

UPDATE for 09/05/24: A new CSV that merges AWY_SEG.csv and AWY_ALT.csv called
AWY_SEG_ALT.csv has been added to the AWY_*.zip grouping. AWY_SEG.csv and
AWY_ALT.csv have been removed. Also, MEA_GAP description in the AWY Layout
Document was updated to include the “N” value.

This is an Enroute Charting file that is only generated new every 56 days.

The AWY_*.csv files were designed as an alternative file type/layout to the legacy AWY.txt and
ATS.txt subscriber files. It does not contain the full complement of data that is in the AWY.txt
and ATS.txt. Several data items removed as non-essential. A new column called
REGULATORY added to be able to combine the two files. Airways designated as
REGULATORY “Y” correspond to AWY.txt and REGULATORY “N” correspond to ATS.txt.
Data, while comparable to the legacy AWY.txt and ATS.txt, is in some cases organized and
presented in a different way.

The AWY_*.csv consists of the following files: AWY_BASE.csv and AWY_SEG_ALT.csv.

ARTCC BOUNDARY DATA CSV files – ARB_*.csv

This is an Enroute Charting file that is only generated new every 56 days.

The ARB_*.csv files were designed as an alternative file type/layout to the legacy ARB.txt
subscriber file and the legacy AFF1 record of the AFF.txt subscriber file. It contains the full
complement of data that is found in the ARB.txt and info specific to ARTCCs found in the AFF1
record of the AFF.txt. Data, while comparable to the legacy ARB.txt and AFF.txt, is in some
cases organized and presented in a different way.

The ARB_*.csv consists of the following files: ARB_BASE.csv and ARB_SEG.csv.

ASOS/AWOS CSV file – AWOS.csv
The AWOS.csv file was designed as an alternative file type/layout to the legacy AWOS.txt
subscriber file. It contains the full complement of data that is found in the AWOS.txt with the
exception of the frequency data which can be found in FRQ.csv. Data, while comparable to the
legacy AWOS.txt, is in some cases organized and presented in a different way.

CLASS AIRSPACE CSV file – CLS_ARSP.csv

The CLS_ARSP.csv was designed from a deconstruction of the legacy TWR.txt Subscriber File
as a logical grouping of the data found in the TWR8 record - CLASS B/C/D/E AIRSPACE AND
AIRSPACE HOURS DATA.

CODED DEPARTURE ROUTES CSV file – CDR.csv

This is an Enroute Charting file that is only generated new every 56 days.

The CDR.csv was designed to replace the legacy CDR.txt Subscriber File. Data while
comparable to the legacy CDR.txt also includes a header row and six additional columns -
ACNTR, TCNTRs, CoordReq, Play, NavEqp and Length.

COMMUNICATIONS OUTLET FACILITIES CSV file – COM.csv

The COM.csv file was designed as a logical grouping of all Communications Outlet Facilities
found in the legacy COM.txt and AFF.txt subscriber files. It contains the full complement of
data that is found in the COM.txt as well as RCAG data from the legacy AFF.txt subscriber file.
Data, while comparable to the legacy COM.txt and AFF.txt, is in some cases organized and
presented in a different way.

FLIGHT SERVICE STATIONS CSV files – FSS_*.csv

The FSS_*.csv files were designed as an alternative file type/layout to the legacy FSS.txt
subscriber file. It does not contain the full complement of data that is in the FSS.txt. FSS
frequency data moved to FRQ.csv. FSS.txt items that are redundant because they are contained
in other legacy subscriber products are not included here. Owner and Operator information
removed as all US FSS are FAA owned and operated. Data, while comparable to the legacy
FSS.txt, is in some cases organized and presented in a different way.

The FSS_*.csv consists of the following files: FSS_BASE.csv and FSS_RMK.csv.

FREQUENCY CSV file – FRQ.csv

The FRQ.csv was designed as a comprehensive frequency data file. It is a consolidation of the
frequency, use, and airport servicing that is currently reported in the TWR.txt and AFF.txt legacy
subscriber files, specifically in the TWR3, TWR7, AFF3 and AFF4 records. It also includes
RCO from COM.txt, GCO/CTAF/UNICOM from RMK record type in the APT.txt,
ASOS/AWOS from AWOS.txt and FSS/RADIO from FSS.txt.
HOLDING PATTERN CSV files – HPF_*.csv

The HPF_*.csv files were designed as an alternative file type/layout to the legacy HPF.txt
subscriber file. It contains the full complement of data that is found in the HPF.txt. Data, while
comparable to the legacy HPF.txt, is in some cases organized and presented in a different way.

The HPF_*.csv consists of the following files: HPF_BASE.csv, HPF_CHRT.csv,
HPF_RMK.csv and HPF_SPD_ALT.csv.

INSTRUMENT LANDING SYSTEM CSV files – ILS_*.csv

The ILS_*.csv files were designed as an alternative file type/layout to the legacy ILS.txt
subscriber file. It contains the full complement of data that is found in the ILS.txt. It does not,
however, contain DECOMMISIONED Systems or Components. Data, while comparable to the
legacy ILS.txt, is in some cases organized and presented in a different way.

The ILS_*.csv consists of the following files: ILS_BASE.csv, ILS_DME.csv, ILS_GS.csv,
ILS_MKR.csv and ILS_RMK.csv.

LOCATION IDENTIFIER DATA CSV file – LID.csv

The LID.csv file was designed as an alternative file type/layout to the legacy LID.txt subscriber
file. It contains the full complement of data that is found in the LID.txt. Data, while comparable
to the legacy LID.txt, is in some cases organized and presented in a different way.

MILITARY OPERATIONS CSV file – MIL_OPS.csv

The MIL_OPS.csv was designed from a deconstruction of the legacy TWR.txt Subscriber File as
a logical grouping of military data found in the TWR1 and TWR2 records.

MILITARY TRAINING ROUTE CSV files – MTR_*.csv

This is an Enroute Charting file that is only generated new every 56 days.

The MTR_*.csv files were designed as an alternative file type/layout to the legacy MTR.txt
subscriber file. It contains the full complement of data that is found in the MTR.txt. Data, while
comparable to the legacy MTR.txt, is in some cases organized and presented in a different way.

The MTR_*.csv consists of the following files: MTR_BASE.csv, MTR_AGY.csv,
MTR_PT.csv, MTR_SOP.csv, MTR_TERR.csv and MTR_WDTH.csv

MISCELLANEOUS ACTIVITY AREA CSV files – MAA_*.csv

The MAA_*.csv files were designed as an alternative file type/layout to the legacy MAA.txt
subscriber file. It contains the full complement of data that is found in the MAA.txt. Data, while
comparable to the legacy MAA.txt, is in some cases organized and presented in a different way.
The MAA_*.csv consists of the following files: MAA_BASE.csv, MAA_CON.csv, MAA_RMK
and MAA_SHP.csv.

NAVIGATION AID CSV files – NAV_*.csv

The NAV_*.csv files were designed as an alternative file type/layout to the legacy NAV.txt
subscriber file. It contains the full complement of data that is found in the NAV.txt. It does not,
however, contain DECOMMISIONED NAVAIDs. Data, while comparable to the legacy
NAV.txt, is in some cases organized and presented in a different way.

The NAV_*.csv consists of the following files: NAV_BASE.csv, NAV_CKPT.csv and
NAV_RMK.csv.

PARACHUTE JUMP AREA CSV files – PJA_*.csv

This is an Enroute Charting file that is only generated new every 56 days.

The PJA_*.csv files were designed as an alternative file type/layout to the legacy PJA.txt
subscriber file. It contains the full complement of data that is found in the PJA.txt. Data, while
comparable to the legacy PJA.txt, is in some cases organized and presented in a different way.

The PJA_*.csv consists of the following files: PJA_BASE.csv and PJA_CON.csv.

PREFERRED ROUTE CSV files – PFR_*.csv

COMING FORMAT CHANGE: PREFERRED ROUTES (PFR_BASE.csv,
PFR_RMT_FMT.csv) INCREASED DESIGNATOR, DESCRIPTION, AND AIRCRAFT
FIELD SIZE – Software changes to increase the field size of the "Designator" field, the “Special
Area Description” field, and the "Aircraft" field for all PFR route types in the PFR_BASE.csv
and PFR_RMT_FMT.csv NASR Subscriber Files are currently planned for a future release of the
NASR Subscriber Files (for PFR_RMT_FMT.csv, only the “Special Area Description” and
"Aircraft" fields apply). In the Designator field, the number of characters allowed will increase
from 5 characters to 16 characters. The “Special Area Description” field will increase from 75
characters to 150 characters. The "Aircraft" field will increase to allow up to 100 characters.

This is an Enroute Charting file that is only generated new every 56 days.

The PFR_*.csv files are designed as an alternative file type/layout to the legacy PFR.txt
subscriber file. It contains the full complement of data that is found in the legacy PFR.txt
subscriber file. Data, while comparable to the legacy PFR.txt, is in some cases organized and
presented in a different way.

The PFR_*.csv consists of the following files: PFR_BASE.csv, PFR_SEG.csv and
PFR_RMT_FMT.csv.

RADAR CSV file – RDR.csv
The RDR.csv was designed from a deconstruction of the legacy TWR.txt Subscriber File as a
logical grouping of radar data found in the TWR5 record.

STANDARD DEPARTURE PROCEDURE CSV files – DP_*.csv

UPDATE for 09/05/24: The RWY_END_ID field in the DP_APT.csv file previously contained a
null value when there was no applicable runway end identifier. A null assumed all runway ends at a
given airport. The null value has been amended to ‘ALL’ to facilitate using the field as part of the
primary key. The DP_CSV_DATA_STRUCTURE.csv has been amended to reflect ‘No’ for
‘Nullable’.

This is an Enroute Charting file that is only generated new every 56 days.

The DP_*.csv files were designed as an alternative file type/layout of the Departure Procedure
(DP) information from the legacy STARDP.txt subscriber file. It contains a full complement of
the DP data that is in the STARDP.txt. Data, while comparable to the legacy STARDP.txt, is in
some cases organized and presented in a different way.

The DP_*.csv consists of the following files: DP_BASE.csv, DP_APT.csv and DP_RTE.csv.

STANDARD TERMINAL ARRIVAL CSV files – STAR_*.csv

UPDATE for 09/05/24: The RWY_END_ID field in the STAR_APT.csv file previously contained a
null value when there was no applicable runway end identifier. A null assumed all runway ends at a
given airport. The null value has been amended to ‘ALL’ to facilitate using the field as part of the
primary key. The STAR_CSV_DATA_STRUCTURE.csv has been amended to reflect ‘No’ for
‘Nullable’.

This is an Enroute Charting file that is only generated new every 56 days.

The STAR_*.csv files were designed as an alternative file type/layout of the Standard Terminal
Arrival (STAR) information from the legacy STARDP.txt subscriber file. It contains a full
complement of the STAR data that is in the STARDP.txt. Data, while comparable to the legacy
STARDP.txt, is in some cases organized and presented in a different way.

The STAR_*.csv consists of the following files: STAR_BASE.csv, STAR_APT.csv and
STAR_RTE.csv.

WEATHER REPORTING LOCATIONS CSV files – WXL_*.csv

This is an Enroute Charting file that is only generated new every 56 days.

The WXL_*.csv files were designed as an alternative file type/layout to the legacy WXL.txt
subscriber file. It contains the full complement of data that is found in the WXL.txt. Data, while
comparable to the legacy WXL.txt, is in some cases organized and presented in a different way.

The WXL_*.csv consists of the following files: WXL_BASE.csv and WXL_SVC.csv.
Feedback greatly appreciated. Please enter your feedback in the Aeronautical Information
Portal. https://nfdc.faa.gov/nfdcApps/controllers/PublicSecurity/nfdcLogin


                                        Published by the
February 2026                U.S. DEPARTMENT OF TRANSPORTATION                         AIS
