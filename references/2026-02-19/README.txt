AIS subscriber files effective date February 19, 2026.

Dear Subscribers,

For the February 19, 2026 subscriber files, the files incorporate data
published in the daily National Flight Data Digest (NFDD) through

    NFDD 012 dated 01/20/2026.

The February 19, 2026 cycle is a 28 Day Change Notice Cycle subscriber set.

By FAA policy and order, some NASR resources, generally categorized as
"Enroute", are only updated on a 56 day charting basis. The following legacy
text subscriber files are included in the 28 day "Change Notice" subscriber
set, but will not contain new data: ARB, ATS, AWY, CDR, MTR, PFR, PJA, STARDP,
and WXL. They will be the same files produced for the previous 56 day AIRAC
cycle. The SAA AIXM 5.0 set file and the AWY AIXM 5.1 file will be updated on
the 56 day major cycle.

AIRAC CYCLE PERIOD: 28 DAY CLARIFICATION

    We are now issuing these products on a 28 day cycle periodicity.
    Subscriber files have previously reported according to a 56 day AIRAC
    cycle periodicity.

    The subscriber file sets will be posted 28 days prior to the effective
    date. The files will contain data that is updated for that cycle and has
    met the cutoff for entry.

    As these subscriber files are complete snapshots of their respective
    resource areas, any updates published in a "Change Notice" set will also
    be included in the next 56 day major cycle set. If your business processes
    are based on a 56 day cycle, you can continue to use the 56 day major
    cycle products and will not be missing data.

DATUM

    The legacy text subscriber files do not cite a datum for geodetic
    coordinates. All US coordinates information provided is currently
    reference NAD 83.

-------------------------------------------------------------------------------
COMING FORMAT CHANGES:

AIRPORT (APT.txt) PAVEMENT CLASSIFICATION FIELD CHANGE

    Software changes to incorporate Pavement Classification Rating (PCR) in
    the APT.txt NASR Subscriber File are currently planned for a future
    release of the NASR Subscriber Files. A new “PAVEMENT CLASSIFICATION”
    column will be added to the APT.txt subscriber file which will denote
    either “PCN” or “PCR”. With the transition towards utilizing the PCR
    method for rating the strength of an airport runway, the current PCN
    fields will reflect either PCN values or PCR values (but not both), or
    null. For PCN or PCR, the PCN/PCR number is concatenated with the
    Pavement type, Subgrade Strength, Tire Pressure, and Evaluation Method.
    Since PCR Number allows for up to 4 characters, the PCN/PCR Number
    field will increase from 3 characters to 4 characters. Initial
    population of the new "PAVEMENT CLASSIFICATION" data field has yet to
    be determined. Therefore, the current practice of displaying PCN values
    in the data fields and PCR values in a reference remark may continue
    after the deployment of the NASR enhancement until the fields can be
    properly populated and the reference remarks removed.


AIRWAY (ATS.txt, AWY.txt) MEA GAP COLUMN ADDED

    Software changes to include an MEA GAP column to the AWY.txt are
    planned for a future release of the NASR Subscriber Files. Currently,
    when the MEA GAP field for a segment is "UNUSABLE", a reference
    remark of "UNUSABLE" is added. A new MEA GAP column will be added to the
    AWY.txt that contains "N" for 'No MEA', "U" for "UNUSABLE", or null.
    Similar to the MEA Value, the value for this field will be entered on
    each segment until the Next MEA Point is reached.

ATS NON-REGULATORY AIRWAYS (ATS.txt) ATS AIRWAY DESIGNATION ADDITION

    A new ATS Airway Designation in the ATS.txt NASR Subscriber File is
    planned for a future release of the NASR Subscriber Files.
    SP = SPECIAL ROUTE Designation and description will be added to the
    ATS.txt Subscriber File. "Special, non-regulatory (non-Part 95) ZK Routes
    are low-level, IFR, performance-based (RNAV) navigation routes primarily
    used by Helicopter Air Ambulance operators. They are not included on
    public charts. You may not file or use these routes without approval
    from FAA Flight Standards. These Special airways will be updated on a
    56-day cycle.".

FIX (FIX.txt) NEW CHARTING TYPE

    A new ATS Airway Designation in the ATS.txt NASR Subscriber File is
    planned for a future release of the NASR Subscriber Files.
    SP = SPECIAL ROUTE Designation and description will be added to the
    ATS.txt Subscriber File. "Special, non-regulatory (non-Part 95) ZK Routes
    are low-level, IFR, performance-based (RNAV) navigation routes primarily
    used by Helicopter Air Ambulance operators. They are not included on
    public charts. You may not file or use these routes without approval from
    FAA Flight Standards. These Special airways will be updated on a 56-day
    cycle.". Fixes that are part of these routes will be denoted with a
    "SPECIAL ENROUTE" charting type.

PREFERRED ROUTES (PFR.txt) INCR. DESIGNATOR, DESCRIPTION, & AIRCRAFT FLD SIZE

   Software changes to increase the field size of the "Designator" field,
   the “Special Area Description” field, and the "Aircraft" field for all PFR
   route types in the PFR.txt NASR Subscriber File are currently planned for a
   future release of the NASR Subscriber Files. In the Designator field, the
   number of characters allowed will increase from 5 characters to 16
   characters. The “Special Area Description” field will increase from 75
   characters to 150 characters. The "Aircraft" field will increase to allow
   up to 100 characters.

PREFERRED ROUTES (PFR.txt) RENAME HSD/LSD PREFERRED ROUTE TYPES

    A software change to rename the "HSD" and "LSD" Preferred Route types
    in the PFR.txt NASR Subscriber File is planned for a future release of
    the NASR Subscriber Files. The code and description for the "HSD" and
    "LSD" Preferred Route types will change. The High Altitude Single
    Direction Preferred Routes (HSD) and Low Altitude Single Direction
    Preferred Routes (LSD) will be retitled as High Altitude Preferred
    Direction (HPD) and Low Altitude Preferred Direction (LPD), respectively.

-------------------------------------------------------------------------------

ATS NON-REGULATORY AIRWAYS (ATS.txt) ADDITION OF AK CAPSTONE ROUTES

    Beginning with the August 7, 2025 effective date, four AK Capstone Routes
    were added to the ATS.txt file. Users must have specific FAA authorization,
    through Operation Specifications or Letter of Authorization, obtained from
    Flight Standards to use the following routes: R2010, R2015, R2020, R2025.
    The aircraft’s lateral deviation display scaling must support the RNP 1
    EnRoute Operations.

SUNSETTING OF LEGACY .TXT SUBSCRIBER FILES

    FAA is in the process of sunsetting the legacy .txt NASR subscriber files.
    The timeframe for sunsetting .txt subscriber files is targeted for the
    24 Dec 2026 AIRAC cycle. The .txt format NASR subscriber files will be
    replaced with a set of .csv format subscriber files, which are currently
    available. A Legacy TXT to CSV Mapping Document is available for download
    via the main 28-Day Subscription page to ease transition.

    NOTE: An enhancement to the NASR database is scheduled for release this
    year, however, a date has yet to be determined. Once a date is confirmed,
    Users of the NASR Subscriber Files will be notified. After this next NASR
    release, .txt subscriber files will no longer contain new data entrants in
    NASR. New data entrants will be available only in .csv subscriber files.

AIRWAY DYNAMIC MAGNETIC VARIATION (ATS.txt, AWY.txt)

    The airway dynamic magnetic variation (SEGMENT MAGNETIC COURSE and SEGMENT
    MAGNETIC COURSE - OPPOSITE DIRECTION) is recalculated yearly, based on
    the magnetic epoch. The updates will be published on the next 56 Day Major
    Cycle following the first 56 day Major Cycle whose data processing period
    falls fully within the calendar year. For 2026, this will be the May 14, 2026
    effective date.

AIRWAY MAXIMUM AUTHORIZED ALTITUDE DATA (AWY.txt)
    Starting with the May 16, 2024 effective cycle.
    The airway point to point Maximum Authorized Altitude (MAA) for Victor (V)
    and Colored Airways (A,B,G,R) will be fully populated when Altitude data
    is present for a given Point.  Currently, a null assumes 17500.

AIRWAY MAXIMUM AUTHORIZED ALTITUDE DATA (AWY.txt)
    Effective July 11, 2024, The Maximum Authorized Altitude (MAA) for 19 Hawaii
    Victor (V) Airways is changed from 17500 to 45000.

ARTCC BOUNDARY (ARB.txt) CLARIFICATION

    Some of the ARTCC boundaries defined by the ARTCC facility are composed of
    more than a single closed shape. Due to the format constraints and naming
    conventions of the legacy ARB file it is not possible to publish each
    shape separately. In these cases it is necessary to read the point
    description text for the key phrase "TO POINT OF BEGINNING" to identify
    where the shape returns to the beginning and forms a closed shape. This is
    currently found in the ZMA BDRY, ZAN BDRY, ZNY HIGH, and ZOA UTA
    boundaries. This is not a change to the file, it is only clarification of
    the practice that has existed for years.

ATS NON-REGULATORY AIRWAYS (ATS.txt) PREFERRED DIRECTION INFORMATION

    All U.S. airways are bidirectional. There are some airways that Air
    Traffic Control (ATC) prefers traffic flow in one direction. However, ATC
    may clear traffic in either direction as needed. Preferred directionality
    for all airways in the NAS will be published in the High Single Direction
    (HSD) Preferred IFR Route (PFR.txt). For clarity in defining preferred
    routing for ATS airways the following change will be made in NASR:

    The preferred direction reference for nine non-regulatory ATS airways in
    the ats.txt file was indicated in the "Mea Dir" column and the "Remarks
    Text" column in Rec Type RMK. Effective 23 Feb 2023, the direction
    information was removed from the ats.txt subscriber file and added in
    the Preferred Route (pfr.txt) subscriber file in a PFR_TYPE HSD (High
    Single Direction) preferred route.

    NOTE: In order to maintain consistency in NASR all references, titles, and
    headings to SINGLE DIRECTION will be removed and or retitled to
    indicate PREFERRED DIRECTION in a future release.

AIRPORT (APT.txt) NEW FUEL TYPES

    Three new fuel types are available in the .txt NASR subscriber files
    beginning with the 27 November 2025 AIRAC cycle.

    H – Hydrogen
    G100 – Unleaded Grade 100 gasoline. Note: G100 is the same as G100UL in
           the .csv subscriber file
    100R - Unleaded Grade 100 gasoline

    NOTE: G100 and G100UL are the same fuel type. Due to character limit
    constraints associated with the .txt subscriber file format, G100UL has been
    truncated to G100.

AIRPORT (APT.txt) BASED AIRCRAFT AND ANNUAL OPERATIONS DATA

    The based aircraft and annual operations data in the apt.txt data set,
    elements A90-96 and A100-105, has been removed from the NASR database and
    is no longer contained in NASR Subscriber files as of the September 5,
    2024 effective date. These fields in the legacy apt.txt subscriber file
    are NULL. Information regarding based aircraft can be found at the
    National Based Aircraft Inventory Program located on the web at
    https://basedaircraft.com/. Information on aircraft operations is available
    from FAA's FAA Aviation System Performance Metrics https://aspm.faa.gov.

AIRPORT (APT.txt) RUNWAY END GRADIENT DATA, BEACON, ARFF

    The runway end gradient data in the apt.txt data set, element E40,
    contained erroneous and incomplete data and should not be used for any
    purpose. All runway end gradient data has been removed as of the April 25,
    2019 effective date NASR Subscriber files. The runway end gradient data
    field will publish with null values while Aeronautical Information
    Services works to ensure all runway end gradient data can be safely
    repopulated.

AIRPORT (APT.txt) RUNWAY SURFACE TREATMENT

    The RWY record contains information on Runway Surface Treatment and has
    allowed for a null entry.  For data consistency, null will be modified to
    "NONE" with the exception of pseudo runways (those containing "X").

    Effective with the 15 June 2023 cycle, Runway Surface Treatment in the RWY
    record of the APT.txt subscriber should only contain null for pseudo
    runways.

TOWER (TWR.txt) FREQUENCY SCRUB

    The frequency number and sectorization data are concatenated together for
    output to the TWR subscriber file in TWR3 & TWR7 records. There was no set
    delimiter between the end of a frequency number and start of the
    sectorization data. A semicolon has been prepended to the sectorization
    field in NASR so that the concatenated export will contain the semicolon
    as a set delimiter between frequency number and sectorization data.

TOWER (TWR.txt) NUMBER OF HOURS OF DAILY OPERATION AND REGULARITY

    The TWR1 record contains two fields, both identified as element number
    TA55, that summarize the number of daily hours (e.g 16) and weekly
    regularity (e.g WDO). At some point, this data will be removed. The
    previously announced date of December 31, 2020 has been delayed. When this
    data is removed, the columns will remain in the layout, but the data will
    be blank. This does not change the actual hours of operation data that
    will continue to be published in the TWR2 records.

TOWER (TWR.txt) RADAR SCRUB

    The TWR5 record contains information on existence of RADAR and the Type
    of RADAR at the Facility.  RADAR Types are being reviewed and RADAR Type
    Numbers will no longer be included with short range RADAR information.
    For example, ASR-11 will be ASR.

    Effective with the 13 July 2023 cycle, TYPE OF RADAR AT THE TOWER fields
    in the TWR5 records will no longer include RADAR Type Number.

NAVAID (NAV.txt) NAVAID MAGNETIC VARIATION AND RADIAL RESTRICTIONS

    The magnetic variation value for DME only NAVAIDs will report as null
    (or blank) since the stand alone DME NAVAID does not provide azimuth
    information.
    (NOTE: DME, VOT AND FM NAVAID TYPES DO NOT HAVE MAG VAR. ANY VALUE IN THIS
    COLUMN FOR THOSE NAVAID TYPES SHOULD BE IGNORED.)

    NAVAID radial restrictions are identified by flight inspection and are
    published as NAVAID remarks. When there are restrictions on stand-alone
    DME only NAVAIDs, the restrictions reference true north. A note has been
    added to the NAV_rf.txt format definition explaining the radial remark
    information, and the use of a "T" designation to indicate "true north" for
    the radials in a DME only remark.
    NOTE: STAND-ALONE DME RESTRICTIONS: THERE IS A NEED TO DIFFERENTIATE
    BETWEEN RESTRICTION RADIALS AT VOR/DMES, VORTAC, AND RESTRICTION RADIALS
    REFERENCED TO TRUE NORTH AT STAND-ALONE DMES. THE T AFTER THE RADIAL
    REPRESENTS TRUE NORTH.
    EX: DME UNUSBL 080T-125T BLW 10000FT)

LOCATION IDENTIFIER (LID.txt) CANADIAN DATA

    The LID 3 'CAN' records which contain location identifiers of Canadian
    customs points of entry, airports, meteorological stations and navigational
    aids are no longer included in the LID.txt subscriber file starting
    with the November 3, 2022 AIRAC cycle.

    Refer to current Canadian charts and flight information publications for
    information within Canadian airspace.

ILS (ILS.txt) PUBLISHED DISTANCES SCRUB

    The ILS subscriber file publishes many distance or measurements of
    components relative to various positions on the runway. This is in
    addition to actual coordinate position data. These distances were
    originally added to support FAA Flight Inspection, who no longer use this
    data from NASR.

    Effective with the April 20, 2023 AIRAC cycle, these distances are no
    longer maintained in NASR. The format of the ILS.txt file has not
    changed, but the attributes in these columns are nulled. Coordinates
    and elevation of the equipment remains.

    Specific attributes that are now nulled:
        Localizer
        o Dist From AER
        o Dist From Centerline
        o Dir From Centerline
        o Dist From Rwy Stop
        o Dir From Rwy Stop
        o Code indicating source of distance information
        o Course Width
        o Course Width at Threshold

        Glide Slope
        o Dist From AER
        o Dist From Centerline
        o Dir From Centerline
        o Rwy Elev Adjacent to GS
        o Code indicating source of distance information

        DME
        o Dist From AER
        o Dist From Centerline
        o Dir From Centerline
        o Dist From Runway Stop
        o Code indicating source of distance information

        Inner/Middle/Outer Marker
        o Dist From AER
        o Dist From Centerline
        o Dir From Centerline
        o Code indicating source of distance information

    The format of the ILS.txt file will not change, but the attributes in
    these columns will be nulled.

NEW CSV FORMAT SUBSCRIBER PRODUCTS FOR ASSESSMENT

    There have been requests from users internal and external for an
    alternative to the flat text fixed length legacy subscriber files. The
    comma delimited CSV files documented here are an attempt to meet that need.

    A full complement of subscriber data coded as CSV is now available.
    All data contained within legacy txt subscriber files are now available
    in CSV format.

    There is a DATA LAYOUT document and CSV DATA STRUCTURE file for each
    resource grouping which gives more in-depth detail. See the Data Layout
    Document and CSV Data Structure file for further information on what data
    (including data types, max length, how displayed and organized) is contained
    in each.

    There is also a CSV_Readme.doc file specific for the new CSV
    products. It highlights latest updates to these products, based on
    feedback and usage analysis, along with organization and presentation
    differences from the legacy .txt subscriber files.

    Current CSV products available include:

        AERONAUTICAL BOUNDARY SEGMENTS CSV - ARB_*.csv
        AIR TRAFFIC CONTROL COMM CSV - ATC_*.csv
        AIRPORT CSV - APT_*.csv
        AIRSPACE FIXES CSV - FIX_*.csv
        AIRWAY CSC - AWY_*.csv
        ASOS/AWOS CSV - AWOS.csv
        CLASS AIRSPACE CSV - CLS_ARSP.csv
        CODED DEPARTURE ROUTES CSV - CDR.csv
        COMMUNICATIONS OUTLET FACILITIES - COM.csv
        DEPARTURE PROCEDURE CSV - DP_*.csv
        FLIGHT SERVICE STATIONS - FSS_*.csv
        FREQUENCY CSV - FRQ.csv
        HOLDING PATTERN CSV - HPF_*.csv
        INSTRUMENT LANDING SYSTEM CSV - ILS_*.csv
        LOCATION IDENTIFIERS CSV - LID.csv
        MILITARY OPERATIONS CSV - MIL_OPS.csv
        MILITARY TRAINING ROUTE CSV - MTR_*.csv
        MISCELLANEOUS ACTIVITY AREA CSV - MAA_*.csv
        NAVIGATION AID CSV - NAV_*.csv
        PARACHUTE JUMP AREA CSV - PJA_*.csv
        PREFERRED ROUTE CSV - PFR_*.csv
        RADAR CSV - RDR.csv
        STANDARD TERMINAL ARRIVAL CSV - STAR_*.csv
        WEATHER REPORTING LOCATIONS CSV - WXL_*.csv

AIXM SUBSCRIBER FILES ARE BEING PRODUCED:

    AIXM 5.1 versions of the Navigation Aid, Airport, ASOS/AWOS, and Airway
    subscriber files are now produced. These products can be found in the
    "AIXM Data" section of the  NASR Subscription listing.

    The XML schema definition and FAA extensions are placed in a folder named
    AIXM\AIXM_5.1\AIXM

    "Frequently asked questions" documents are placed in a folder named
    AIXM\AIXM_5.1\FAQs

    Mappings of data attributes from the .txt file to the AIXM products are
    placed in a folder named AIXM\AIXM_5.1\mappings

    The actual data files are zipped and placed in a folder named
    AIXM\AIXM_5.1\XML-Subscriber-Files

    NAVAID_AIXM
    The AIXM5.1 Navigation Aid subscriber file contains data also published in
    both the NAV.txt and ILS.txt legacy subscriber files. Both the legacy
    NAV.txt and ILS.txt products and the new AIXM product will be produced
    concurrently.

    APT_AIXM
    The AIXM5.1 Airport subscriber file contains the data also produced in the
    legacy APT.txt subscriber file. Both products are produced in parallel. An
    updated Airport_DataTypes.xsd file is included in the \extension folder
    reference documents.

    AWOS_AIXM
    The AIXM5.1 ASOS/AWOS subscriber file contains the data also produced in
    the legacy AWOS.txt subscriber file. Both products are produced in
    parallel.

    AWY_AIXM
    The AIXM5.1 AIRWAY subscriber file contains the data also produced in the
    legacy AWY.txt subscriber file. Both products are produced in parallel. An
    updated Airway_DataTypes.xsd file is included in the \extension folder
    reference documents.

SPECIAL ACTIVITY AIRSPACE (SAA)

    An AIXM subscriber product called Special Activity Airspace (SAA),
    containing data for all operational Special Use Area (SUA) and 16 National
    Security Areas is produced. It is an XML product based on Aeronautical
    Information Exchange Model version 5.0 (AIXM5). Information on AIXM can be
    found at http://www.aixm.aero.

    The latest XML schema definition files for the SAA subscriber product
    can be found within the download.

    The AIXM SAA product can be found in the "AIXM Data" section of the NASR
    Subscription listing. The subscriber data is zipped with the schema
    information, inside a zip file named "SaaSubscriberFile.zip".

Other Notes:

FOREIGN DATA

    These subscriber files contain limited information on non-US resources,
    primarily for context. These should not be considered official source.
    Refer to current Canadian charts and flight information publications for
    information within Canadian airspace.

REMINDER:

All of the subscriber files are available free of charge from the
Aeronautical Data/NFDC website located at
https://www.faa.gov/air_traffic/flight_info/aeronav/aero_data/NASR_Subscription/.
It is not necessary to register in order to access or download the files.
However, in order to receive email alerts when the new subscriber set becomes
available, users must register at
https://nfdc.faa.gov/nfdcApps/controllers/PublicSecurity/register
There is no cost to register. Users can select all or individual files to
download.


Your comments or suggestions can be directed to Aeronautical Information
Services at the following contact points:

    Telephone:  1-800-638-8972

    email: 9-AMC-Aerochart@faa.gov







History:

ARTCC FACILITIES (AFF.txt) RADAR RECORDS

    The AFF1 record has contained basic information on ARTCC associated
    facilities, including the base ARTCC, CERAP, RCAG, and RADAR sites
    (ARSR and SECRA). The RADAR site information was minimal, essentially site
    name, state, and association to one or more ARTCCs. This information will
    no longer be maintained in NASR.

    Effective with the 29 December 2022 cycle, AFF1 records for ARSR and SECRA
    sites are no longer included.
