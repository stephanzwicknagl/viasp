import React from "react";
import PropTypes from "prop-types";

const defaultHighlightedSymbol = [];

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);

    function addHighlightedSymbol(arrows) {
        if (arrows) {
            // remove duplicates from concatenation using stringify to compare the arrays
            const newHighlightedSymbol = Array.from(new Set([...highlightedSymbol, arrows].map(JSON.stringify)), JSON.parse)
            setHighlightedSymbol(newHighlightedSymbol);
        }
    };


    return <HighlightedSymbolContext.Provider
        value={[highlightedSymbol, addHighlightedSymbol, setHighlightedSymbol]}>{children}</HighlightedSymbolContext.Provider>
}

HighlightedSymbolProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
