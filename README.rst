=========
Salt Fuse
=========

Salt is a powerful infrastructure framework, allowing a master (or masters) to
control a group of minions, by issuing remote execution calls. The Salt Fuse
project takes advantage of this power by allowing the user to treat remote
minions' filesystems as if they were locally mounted on the Salt Master.

This project is in a very early state. The interface is expected to change, as
early development continues. Eventually, we plan to reach a state of stability,
but until then, it is definitely not recommended to run this project in
production.

Requirements
============
This is a bleeding edge project which requires at least Salt 2014.1 RC1 to be
installed on any minion which it connects to.

http://saltstack.com/

The fusepy project (available via pip) must also be installed on the system
that creates the Fuse mount.

https://github.com/terencehonles/fusepy

Execution
=========
Create the directory which will hold the mountpoint. The root of this
filesystem shows a list of minions. Inside each minion's directory is the root
of that minion's filesystem.

.. code-block:: bash

    sudo mkdir -p /media/salt/
    sudo salt-fuse /media/salt/

Road Map
========
The accomplishment of the following features will determine the accompanying
release versions:

0.5.0
    Use the fuse mountpoint as a filesystem browser for Windows-based minions,
    starting with the driver letter (i.e., /media/salt/minion_id/C/WINNT/, etc).

0.6.0
    Configure alternate mountpoints for explicitly configured minions, outside
    of the standard root (i.e., /media/salt/minion_alias/somedir/ points to
    /path/to/dir/ on the minion).

0.7.0
    Allow certain files from the minions to be cached locally, rather than
    accessed using network I/O.

With the release of 0.7.0, the salt-fuse project will move from alpha status
to beta status. Releases after that point may contain new features, but the
general focus will be on stability.
