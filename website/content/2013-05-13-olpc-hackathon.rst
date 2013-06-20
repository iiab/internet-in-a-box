OLPC Hackathon
##############

:date: 2013-05-13

.. image:: |filename|/images/IMG_20130512_212124.jpg

I've been working with a really great group of half a dozen OLPC 
volunteers up here in a big farmhouse in Ontario, Canada.

This group is developing a server configuration called School Server 
XS-CE.  Their server provides DHCP, web filtering, chat, NAT firewall, 
backup, and other services for schools using the OLPC XO laptops.  Their 
baseline hardware is to install on a spare OLPC XO Laptop itself with a 
USB Ethernet dongle for upstream.

They are very keen to integrate Internet-in-a-Box.

I have IIAB running on an XO Laptop with data on a USB hard drive, and a 
written procedure for installing it on the School Server.

However, IIAB is not yet ready to be packaged and deployed in this way, 
on the same machine as the School Server.  It is easier for us to deploy 
as a stand-alone network appliance which the School Server discovers on 
the network and links to until we are more mature.  The OLPC guys have 
written a CGI script which detects if an IIAB is on the LAN and provides 
a link to it.

The new version of School Server is set to be deployed in the next few 
months.  There are 10,000 older School Servers already deployed in the 
world serving maybe a million kids, so this is a large market for us.

We are generating a lot of interest.
