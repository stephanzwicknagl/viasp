import React from "react";
import PropTypes from "prop-types";

// #const _color_primary = "#0052CC".
// #const _color_secondary = "#6554C0".
// #const _color_success = "#36B37E".
// #const _color_info = "#B3BAC5".
// #const _color_warning = "#FFAB00".
// #const _color_danger = "#FF5630".
// #const _color_light = "#F4F5F7".
export const defaultPalette = {
    primary: "#0052CC",
    secondary: "#6554C0",
    success: "#36B37E",
    info: "#B3BAC5",
    warning: "#FFAB00",
    danger: "#FF5630",
    light: "#F4F5F7",
    medium: "#a9a9a9",
    dark: "#444",
    // node border colors
    ten: { dark: "#0052CC", bright: "#0052CC"}, 
    // row background (arbitrary number and names)
    twenty: { dark: "#a9a9a94a", bright: "#ffffff" },
    // text color of node, detail sidebar, row header (dark) and detail sidebar atoms (bright)
    thirty: { dark: "#444", bright: "#FFFFFF"},
    // recursive node supernode background (dark) and border (bright)
    fourty: { dark: "#0052CC", bright: "#0052CC" },
    // detail sidebar atom background (dark) and border (bright)
    fifty: { dark: "#0052CC" },
    // background color of node, detail sidebar, row header
    sixty: { dark: "#F6F4F3" },
    // edge color (dark) and edge to clingraph color (bright)
    seventy: { dark: "#444", bright: "#444" },
    // arbitrary number of colors to highlight explanations
    highlight: { 0: "#d48521", 1: "#9a8298", 2: "#e0e4ac", 3: "#98f4e2", 4: "#21d485" },
    // currently not used
    error:     {ten: "#EB4A4E", thirty: "#4C191A", sixty: "#FCE8E8"},
    warn:      {ten: "#FF9800", thirty: "#653300", sixty: "#FFF1DF"}
};

const ColorPaletteContext = React.createContext([]);
export const updateColorPalette = (custom_colors) => {
    if ("ten" in custom_colors) {
        defaultPalette.ten = custom_colors.ten;
    }
    if ("twenty" in custom_colors) {
        defaultPalette.twenty = custom_colors.twenty;
    }
    if ("thirty" in custom_colors) {
        defaultPalette.thirty = custom_colors.thirty;
    }
    if ("fourty" in custom_colors) {
        defaultPalette.fourty = custom_colors.fourty;
    }
    if ("fifty" in custom_colors) {
        defaultPalette.fifty = custom_colors.fifty;
    }
    if ("sixty" in custom_colors) {
        defaultPalette.sixty = custom_colors.sixty;
    }
    if ("seventy" in custom_colors) {
        defaultPalette.seventy = custom_colors.seventy;
    }
    if ("highlight" in custom_colors) {
        defaultPalette.highlight = custom_colors.highlight;
    }
    if ("error" in custom_colors) {
        defaultPalette.error = custom_colors.error;
    }
    if ("warn" in custom_colors) {
        defaultPalette.warn = custom_colors.warn;
    }
    React.useContext(ColorPaletteContext)
    return defaultPalette;
};

export const useColorPalette = () => React.useContext(ColorPaletteContext);
export const ColorPaletteProvider = ({children, colorPalette}) => {
    const updatedColorPalette = !colorPalette ? defaultPalette : updateColorPalette(colorPalette)
    return <ColorPaletteContext.Provider value={updatedColorPalette}>{children}</ColorPaletteContext.Provider>
}

ColorPaletteProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
    /**
     * The color palette to update the color palette with
     */
    colorPalette: PropTypes.exact({
        ten: PropTypes.object,
        twenty: PropTypes.object,
        thirty: PropTypes.object,
        fourty: PropTypes.object,
        fifty: PropTypes.object,
        sixty: PropTypes.object,
        seventy: PropTypes.object,
        highlight: PropTypes.object,
        error: PropTypes.object,
        warn: PropTypes.object
    })
}
