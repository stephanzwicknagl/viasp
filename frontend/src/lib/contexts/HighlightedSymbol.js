import React from "react";
import PropTypes from "prop-types";

const defaultHighlightedSymbol = [];

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);

    function toggleHighlightedSymbol(arrows) {
        if (arrows) {
            // stringify to compare the arrays
            var array = highlightedSymbol.map((item) => JSON.stringify(item));
            var value = JSON.stringify(arrows);
            var index = array.indexOf(value);

            if (index === -1) {
                array.push(value);
            } else {
                array.splice(index, 1);
            }
            setHighlightedSymbol(Array.from(array, JSON.parse));
        }
    };


    return <HighlightedSymbolContext.Provider
        value={[highlightedSymbol, toggleHighlightedSymbol, setHighlightedSymbol]}>{children}</HighlightedSymbolContext.Provider>
}

HighlightedSymbolProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
