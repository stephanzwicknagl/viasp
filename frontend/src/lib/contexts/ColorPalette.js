import React from "react";
import PropTypes from "prop-types";

export const defaultPalette = {
    // node border colors
    ten: {dark: "#3FA7D1", bright: "#3FA7E1"}, 
    // row background (arbitrary number and names)
    twenty: { dark: "#a9a9a94a", bright: "#ffffff" },
    // text color of node, detail sidebar, row header (dark) and detail sidebar atoms (bright)
    thirty: { dark: "#444", bright: "#F6F4F3"},
    // recursive node supernode background (dark) and border (bright)
    fourty: { dark: "#3FA7D1", bright: "#3FA7D1" },
    // detail sidebar atom background (dark) and border (bright)
    fifty:  { dark: "#3FA7D1" },
    // background color of node, detail sidebar, row header
    sixty: { dark: "#F6F4F3" },
    // edge color (dark) and edge to clingraph color (bright)
    seventy: { dark: "#000000", bright: "#000000" },
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
