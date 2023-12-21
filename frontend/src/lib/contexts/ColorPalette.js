import React from "react";
import PropTypes from "prop-types";

export const defaultPalette = {
    primary: '#6554C0', // '#879ee7'
    success: '#36B37E',
    info: '#B3BAC5',
    warning: '#FFAB00',
    danger: '#FF5630',
    light: '#F4F5F7',
    medium: '#a9a9a9',
    dark: '#444',
    // row background (any number)
    twenty: {
        0: '#a9a9a94a', 
        1: '#ffffff'},
    // reason arrows & highlights (any number)
    highlight: {
        0: '#d48521',
        1: '#9a8298',
        2: '#e0e4ac',
        3: '#98f4e2',
        4: '#21d485',
    },
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
