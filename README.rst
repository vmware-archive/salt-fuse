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
    sudo python2 salt-fuse.py / /media/salt/alton/ alton
