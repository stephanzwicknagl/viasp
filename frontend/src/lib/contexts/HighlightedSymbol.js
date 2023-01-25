import React from "react";
import PropTypes from "prop-types";
import { useColorPalette } from "../contexts/ColorPalette";

const defaultHighlightedSymbol = [];

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);
    const colorPalette = useColorPalette();
    const colorArray = Object.values(colorPalette.highlight);

    function getNextColor(l, arrowsColors){
        var c = JSON.stringify(colorArray[l % colorArray.length])
        if (arrowsColors.indexOf(c) === -1 || l >= colorArray.length){
            return c
        }
        else{
            return getNextColor(l+1, arrowsColors)
        }
    }

    function toggleHighlightedSymbol(arrows) {
        var arrowsSrcTgt = [];
        var arrowsColors = [];
        highlightedSymbol.forEach(item => {
            arrowsSrcTgt.push(JSON.stringify({"src":item.src, "tgt":item.tgt}));
            arrowsColors.push(JSON.stringify(item.color));
        })
        const c = getNextColor(new Set(highlightedSymbol.map(item => item.src)).size, arrowsColors);

        arrows.forEach(a => {
            var value = JSON.stringify(a);
            var index = arrowsSrcTgt.indexOf(value);

            if (index === -1) {
                arrowsSrcTgt.push(JSON.stringify(a));
                arrowsColors.push(c);
            } else {
                arrowsSrcTgt.splice(index, 1);
                arrowsColors.splice(index, 1);
                // call update height
            }
        })
        setHighlightedSymbol(
            arrowsSrcTgt.map((item, i) => {
                var obj = JSON.parse(item);
                obj.color = JSON.parse(arrowsColors[i]);
                return obj;
        }));
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
