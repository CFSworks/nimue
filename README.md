Nimue
=====

Nimue is a simple Python script for jailbreaking Sony Bravia TVs.

Intended audience
-----------------

This is largely obsolete; shortly after this script was first published, Sony
released firmware version `aa0206pf`, which was forcibly installed and closed
the target service on the TV.

To that end, this repository is kept largely for historical and educational
reasons. However, should you have a TV that is affected, this script is useful
in getting a root shell on the TV.

Affected TVs
------------

Any Sony Bravia TV, which has not had a firmware update since 2012, and which
has TCP port 12345 open, should be affected.

How to use
----------

Download the repository to your local computer, and run the 'nimue.py' script
under Python 2.7(!), passing as first argument the IP address of the TV on your
local network that you wish to access. Note that the exploit opens other TCP
connections; for best results, ensure no firewall between your computer and the
TV.

Once the exploit is done, you will be given a port to connect to on Telnet.
Note that the Telnet service is not secured; it gives a root shell immediately.
