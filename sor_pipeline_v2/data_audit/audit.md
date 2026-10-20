
# Counties to audit: 
| GEOID | County Name |
| :--- | :--- |
| 12086 | Miami-Dade, FL |
| 48427 | Starr, TX |
| 36061 | New York (Manhattan), NY |
| 48301 | Loving, TX |
| 72127 | San Juan, PR |
| 31005 | Arthur, NE |
| 46102 | Oglala Lakota, SD |

# Election data source

The election data was sourced from the MIT Election Data and Science Lab at the Harvard Dataverse website (doi:10.7910/DVN/VOQCHQ), with Universal Numerical Fingerprint (UNF): "6:VKZJHPbIwGBnmWCslEFbtw==". Programmatic download is gated behind a guestbook form, so I downloaded the source manually from the website in its original CSV format ("countypres_2000-2024.csv"). The pipeline verifies the file's MD5 against the checksum published in the dataset's Dataverse metadata on every load. Upon downloading the data, I cleaned it as follows. I first filtered the file to the 2020 and 2016 US presidential races, keeping only Democratic and Republican votes. I dropped the non-county reporting units that carry no FIPS code, namely statewide write-ins, overseas/UOCAVA ballots, and Rhode Island's federal precinct. I zero-padded the county FIPS codes to five-digit GEOIDs. I folded Kansas City's separately reported return (pseudo-FIPS 2938000) into Jackson County, MO to match census geography. I excluded Alaska because its returns are reported by election district rather than by the census boroughs the pipeline uses. I dropped the defunct Bedford City, VA, which merged into Bedford County in 2013 but remains in the file as a vestigial zero-vote 2016 row. Finally, I summed each county's votes, letting TOTAL rows take precedence over vote-mode splits because summing both would double-count. The result is one row per county with four columns: Democratic and Republican presidential votes for 2020 and 2016.
