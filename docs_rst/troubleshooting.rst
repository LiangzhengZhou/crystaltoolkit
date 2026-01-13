===============
Troubleshooting
===============

This page is intended to help developers of Crystal Toolkit.

Headless screenshots with Playwright
-----------------------------------

If you want to save a PNG that matches the Dash web view, you can use
``crystal_toolkit/apps/examples/write_cif_screenshot_headless.py`` to start a
Dash server and drive a headless Chromium instance that captures the screenshot.

Playwright needs a browser binary. If ``playwright install chromium`` fails
(for example because your environment blocks downloads), you have two options:

1. **Use a system-installed Chromium/Chrome** and pass its path with
   ``--browser-path``. You can also set ``PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1``
   during installation to avoid download attempts.
2. **Configure a download mirror** by setting ``PLAYWRIGHT_DOWNLOAD_HOST`` to a
   reachable host in your environment.

Example:

.. code-block:: bash

   PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 pip install playwright
   python crystal_toolkit/apps/examples/write_cif_screenshot_headless.py \
     your_structure.cif structure_dash.png \
     --browser-path /usr/bin/chromium
