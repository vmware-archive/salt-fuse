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
Create the directory which will hold the mountpoint. In future versions, this
driver is intended to be used as a minion filesystem browser. Until that
happens, minions must be mounted individually. For instance, assuming your
minion's name is `alton`:

.. code-block::

    sudo mkdir -p /media/salt/alton/
    sudo salt-fuse / /media/salt/alton/ alton

Road Map
========
The accomplishment of the following features will determine the accompanying
release versions:

0.4.0
    Use the fuse mountpoint as a filesystem browser for Linux-based minions
    (i.e., /media/salt/minion_id/<minion's root>).

0.5.0
    Use the fuse mountpoint as a filesystem browser for Windows-based minions,
    starting with the driver letter (i.e., /media/salt/minion_id/C/WINNT/, etc).

0.6.0
    Configure alternate mountpoints for explicitly configured minions, outside
    of the standard root (i.e., /media/salt/minion_alias/somedir/ points to
    /path/to/dir/ on the minion)

With the release of 0.6.0, the salt-fuse project will move from alpha status
to beta status. Releases after that point may contain new features, but the
general focus will be on stability.
