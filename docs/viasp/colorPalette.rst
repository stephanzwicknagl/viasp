=================
Color Palette
=================

The color Palette of viASP's frontend is defined by the file `backend/src/viasp/server/static/colorPalette.json`.

The default file contains the following JSON object:

.. code-block:: JSON

    {
        "primary": "#879ee7",
        "light": "#F4F5FA",
        "dark": "#444",
        "infoBackground": "#B3BAC5",
        "rowShading": {
            "0": "#a9a9a92f",
            "1": "#ffffff"
        },
        "explanationSuccess": "#36B37E", 
        "explanationHighlights": {
            "0": "#d48521",
            "1": "#9a8298",
            "2": "#e0e4ac",
            "3": "#98f4e2",
            "4": "#21d485"
        }
    }

To permanently change the colors used in a viASP installation, edit the file at the site packages directory of your environment. Use the command `which viasp` to find the directory.