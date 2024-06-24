=================
Color Palette
=================

The color Palette of viASP's frontend is defined by the file `/server/colorPalette.json`.

The default file contains the following JSON object:

.. code-block:: JSON

    {
        "primary": "rgba(103, 153, 247, 1)",
        "light": "rgba(255, 255, 255, 1)",
        "dark": "rgba(68, 68, 68, 1)",
        "warn": "rgba(255, 193, 7, 1)",
        "error": "rgba(244, 67, 54, 1)",
        "infoBackground": "rgba(215, 255, 171,  1)",
        "rowShading": [
            "rgba(255, 255, 255, 0.5)",
            "rgba(50, 149, 255, 0.10)"
        ],
        "explanationSuccess": "rgba(103, 153, 247, 1)", 
        "explanationHighlights": [
            "rgba(137,207,118, 1)",
            "rgba(204,195,126, 1)",
            "rgba(201,134,140, 1)"
        ]
    }

To permanently change the colors used in a viASP installation, edit the file at the site packages directory of your environment. Use the command `which viasp` to find the directory.