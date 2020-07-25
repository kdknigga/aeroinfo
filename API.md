# api.aeronautical.info

## General Notes on Usage

**If you plan on building something that uses this API please note the "dev" in the URL.**  This is not a "production-grade" service and is run on a shoestring budget.  On the other hand, though, it's had pretty darned good uptime and it's offered completely free of charge to you.  If you are interested in using the API I provide for anything important, please [let me know](mailto:kris+aeroinfo@knigga.com) and maybe we can work out some arrangement for a paid, "production-grade" service.  Further, if you would be so kind, please include the parameter `appid` in your query string with a value that uniquely identifies your application.  For example, for my app [loggingnight](https://loggingnight.org/) I pass `appid=loggingnight` in the query string.  Knowing what applications use my service is both interesting to me and also helps me justify the expense to myself.  :)

Currently you can query for airport, runway, and runway end information.

What's a runway end?  Well, the FAA breaks a normal runway into two parts: base end and reciprocal end.  For an example, runway "18/36" has a base end of "18" and a reciprocal end of "36".  In the FAA's data set, some attributes belong to a runway as a whole and some attributes belong to runway ends.

All queries are done with HTTP GETs and query strings.  I don't do anything with POSTs or any other methods at the moment.

Query strings can be broken down into two parts: identifying what you want to search for, and specifying what information you want to see.  I'll show examples below.

## How to query airport information
The required query string parameter to search for an airport is `airport`.  It accepts either FAA or ICAO airport identifers and returns basic airport information.

* https://api.aeronautical.info/dev/?airport=ORD
* https://api.aeronautical.info/dev/?airport=KJFK

All of the interesting information is grouped into attribute sets based on the groupings found in the FAA's NASR subscription text file.  To see them, add `include` parameters for the groups you want.

* https://api.aeronautical.info/dev/?airport=ORD&include=demographic
* https://api.aeronautical.info/dev/?airport=ORD&include=ownership
* https://api.aeronautical.info/dev/?airport=ORD&include=demographic&include=ownership

Currently available attribute groups:
* demographic
* ownership
* geographic
* faaservices
* fedstatus
* inspection
* aptservices
* facilities
* basedaircraft
* annualops
* additional
* remarks
* runways
* attendance

## How to query runway information
To get information for a specific runway, you just need to add one more parameter to the query string in addition to `airport`: `runway`.

* https://api.aeronautical.info/dev/?airport=ORD&runway=10C%2F28C

You may notice that runway names usually have a forward-slash in them.  This needs to be urlencoded as `%2F`.  This is annoying, so you have the option to specify only one end of the runway.

* https://api.aeronautical.info/dev/?airport=ORD&runway=10C

`include` parameter groups for runways are:
* additional
* runway_ends

Yeah, runways don't have all that much interesting information.  Most of the interesting stuff is in runway_ends.

## How to query runway end information
Now we have three required query string parameters: `airport`, `runway`, and `runway_end`.

* https://api.aeronautical.info/dev/?airport=ORD&runway=10C%2F28C&runway_end=10C
* https://api.aeronautical.info/dev/?airport=ORD&runway=10C&runway_end=10C
* https://api.aeronautical.info/dev/?airport=ORD&runway=10C&runway_end=28C

You'll notice that even though we abbreviated the `runway` name from "10C/28C" to just "10C", we can still specify a `runway_end` of "28C" and get the information for that end of the runway.

`include` parameter groups for runway ends are:
* geographic
* lighting
* object
* additional
