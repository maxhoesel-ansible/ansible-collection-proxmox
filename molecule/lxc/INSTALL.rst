*******
Docker driver installation guide
*******

Requirements
============

* Vagrant >= 2
* Virtualbox >= 6
* Packer >= 1.6
* proxmoxer
* requests

Note about PVE and Vagrant
==========================

As this project is based around provisioning containers in Proxmox, a proper virtual machine is required, hence the need for Vagrant + Virtualbox.
A proxmox VE Vagrant box will be built automatically when installing test dependencies

Please ensure that the requirements above are met before running molecule.

Install
=======

Please refer to the `Virtual environment`_ documentation for installation best
practices. If not using a virtual environment, please consider passing the
widely recommended `'--user' flag`_ when invoking ``pip``.

.. _Virtual environment: https://virtualenv.pypa.io/en/latest/
.. _'--user' flag: https://packaging.python.org/tutorials/installing-packages/#installing-to-the-user-site

.. code-block:: bash
    $ sudo apt install vagrant virtualbox packer
    $ python3 -m pip install molecule molecule-vagrant proxmoxer requests
