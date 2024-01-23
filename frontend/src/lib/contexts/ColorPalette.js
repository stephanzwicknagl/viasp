import React from "react";
import PropTypes from "prop-types";

export const ColorPaletteContext = React.createContext([]);

export const useColorPalette = () => React.useContext(ColorPaletteContext);
export const ColorPaletteProvider = ({children, colorPalette}) => {
    return (
        <ColorPaletteContext.Provider value={colorPalette}>
            {children}
        </ColorPaletteContext.Provider>
    );
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
        primary: PropTypes.string,
        light: PropTypes.string,
        dark: PropTypes.string,
        infoBackground: PropTypes.string,
        rowShading: PropTypes.objectOf(PropTypes.string),
        explanationSuccess: PropTypes.string,
        explanationHighlights: PropTypes.objectOf(PropTypes.string),
    }),
};
