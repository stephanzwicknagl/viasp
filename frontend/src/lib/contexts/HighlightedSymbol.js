import React from "react";
import PropTypes from "prop-types";

const defaultHighlightedSymbol = null;

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);


    return <HighlightedSymbolContext.Provider
        value={[highlightedSymbol, setHighlightedSymbol]}>{children}</HighlightedSymbolContext.Provider>
}

HighlightedSymbolProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
