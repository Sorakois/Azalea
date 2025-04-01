''' 
We can "curl" this website
    # https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#
    # to see source code: view-source:https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#
to get ALL the html code.
(or justs go and copy/paste the source code)

We can parse through the HTML to find names, and all materials we need for the /build command.
All the data is there, it's just a matter of, well, parse it and get what we need!
'''

from bs4 import BeautifulSoup

# This is the url to the HSR meta sheet guide
# Made by community members, scraped by us!
sheet_url = "view-source:https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRsm60jYo8MdHWimjvY42wE8-j-0NBwG9-KutpNcQbylhhBiKBpGmUm1x3CXExthl2EB438RdMWdeT3/pubhtml#"

# Make a BS object so we can parse the data
build_soup = BeautifulSoup(open(sheet_url))

# For Google Sheets specifically, all the data we need to scrape
# Will be found in <tr> ... </tr> and nowhere else.
# Makes sense if you think about it!

# findAll will return a ResultSet instance.
# Similar to a list, but has BS unique methods.
# We can convert with list() if needed, though!
# Output should look like [<tr></tr>, <tr></tr>, ...]
buildBowl = build_soup.findAll('tr')
