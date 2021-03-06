Pyyaledoorman
=============

|PyPI| |Python Version| |License|

|Read the Docs| |Tests| |Codecov|

|pre-commit| |Black|

.. |PyPI| image:: https://img.shields.io/pypi/v/pyyaledoorman.svg
   :target: https://pypi.org/project/pyyaledoorman/
   :alt: PyPI
.. |Python Version| image:: https://img.shields.io/pypi/pyversions/pyyaledoorman
   :target: https://pypi.org/project/pyyaledoorman
   :alt: Python Version
.. |License| image:: https://img.shields.io/pypi/l/pyyaledoorman
   :target: https://opensource.org/licenses/MIT
   :alt: License
.. |Read the Docs| image:: https://img.shields.io/readthedocs/pyyaledoorman/latest.svg?label=Read%20the%20Docs
   :target: https://pyyaledoorman.readthedocs.io/
   :alt: Read the documentation at https://pyyaledoorman.readthedocs.io/
.. |Tests| image:: https://github.com/espenfjo/pyyaledoorman/workflows/Tests/badge.svg
   :target: https://github.com/espenfjo/pyyaledoorman/actions?workflow=Tests
   :alt: Tests
.. |Codecov| image:: https://codecov.io/gh/espenfjo/pyyaledoorman/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/espenfjo/pyyaledoorman
   :alt: Codecov
.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit
.. |Black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Black

A Python library for interfacing with the Yale Doorman Home API.

Features
--------

* Read whether lock is unlocked, locked, or door open
* Locking / Unlocking
* Enabling / Disabling auto lock
* Reading Volume level, Language, Auto lock disabled/enabled



Requirements
------------

* Yale Doorman home user account.


Installation
------------

You can install *Pyyaledoorman* via pip_ from PyPI_:

.. code:: console

   $ pip install pyyaledoorman


Usage
-----

Please see `Usage <Usage_>`_ for details.

.. code-example
.. code-block:: python

    import pyyaledoorman
    import aiohttp
    import asyncio
    import pyyaledoorman


    async def main():
        async with aiohttp.ClientSession() as session:
            client = pyyaledoorman.Client(
                "username",
                "password",
                session=session,
            )
            assert await client.login() == True
            await client.update_devices()

            for device in client.devices:
                print(device.name)
                await device.disable_autolock()
                await device.unlock(pincode="123456")


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

.. code-example-end

Contributing
------------

Contributions are very welcome.
To learn more, see the `Contributor Guide`_.


License
-------

Distributed under the terms of the `MIT license`_,
*Pyyaledoorman* is free and open source software.


Issues
------

If you encounter any problems,
please `file an issue`_ along with a detailed description.


Credits
-------

This project was generated from `@cjolowicz`_'s `Hypermodern Python Cookiecutter`_ template.

.. _@cjolowicz: https://github.com/cjolowicz
.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _MIT license: https://opensource.org/licenses/MIT
.. _PyPI: https://pypi.org/
.. _Hypermodern Python Cookiecutter: https://github.com/cjolowicz/cookiecutter-hypermodern-python
.. _file an issue: https://github.com/espenfjo/pyyaledoorman/issues
.. _pip: https://pip.pypa.io/
.. github-only
.. _Contributor Guide: CONTRIBUTING.rst
.. _Usage: https://pyyaledoorman.readthedocs.io/en/latest/usage.html
