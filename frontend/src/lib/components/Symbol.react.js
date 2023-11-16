import React, { useState } from "react";
import { make_atoms_string } from "../utils/index";
import './symbol.css';
import PropTypes from "prop-types";
import { SYMBOLIDENTIFIER } from "../types/propTypes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";

function useHighlightedSymbolToCreateClassName(symbol) {
    let classNames = "symbol";
    let style = null;
    const [compareHighlightedSymbol, ,] = useHighlightedSymbol();


    const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol);
    const j = compareHighlightedSymbol.map(item => item.src).indexOf(symbol);
    if (i !== -1) {
        classNames += " mark_symbol";
        // all colors where item.tgt is equal to symbol
        let colors = compareHighlightedSymbol.map(item => item.tgt).map((item, index) => item === symbol ? index : -1).filter(item => item !== -1).map(item => compareHighlightedSymbol[item].color).reverse();
        let gradientStops = colors.map((color, index, array) => {
            let start = (index / array.length) * 100;
            let end = ((index + 1) / array.length) * 100;
            return `${color} ${start}%, ${color} ${end}%`;
        }).join(', ');
        style = { background: `linear-gradient(-45deg, ${gradientStops})` };
    }
    else if (j !== -1) {
        classNames += " mark_symbol";
    }
    return [classNames, style]
}

export function Symbol(props) {
    const { symbolIdentifier, isSubnode, reasons, handleClick } = props;
    const [isHovered, setIsHovered] = useState(false);
    const [isClicked, setIsClicked] = useState(false);
    const colorPalette = useColorPalette();

    let atomString = make_atoms_string(symbolIdentifier.symbol)
    let suffix = `_${isSubnode ? "sub" : "main"}`
    let [classNames1, style1] = useHighlightedSymbolToCreateClassName(symbolIdentifier.uuid);
    atomString = atomString.length === 0 ? "" : atomString;

    if (reasons !== undefined && reasons.length !== 0 && isHovered) {
        style1 = { backgroundColor: colorPalette.success };
    }
    if (reasons !== undefined && reasons.length !== 0 && isClicked) {
        style1 = { backgroundColor: colorPalette.info };
    }

    const handleMouseEnter = () => setIsHovered(true);
    const handleMouseLeave = () => setIsHovered(false);
    const handleMouseDown = () => setIsClicked(true);
    const handleMouseUp = () => setIsClicked(false);

    return (<div 
            className={classNames1} 
            id={symbolIdentifier.uuid + suffix} 
            style={style1} 
            onClick={(e) => handleClick(e, symbolIdentifier)} 
            onMouseEnter={handleMouseEnter} 
            onMouseLeave={handleMouseLeave} 
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}>
                {atomString}
            </div>);
}

Symbol.propTypes = {
    /**
     * The symbolidentifier of the symbol to display
     */
    symbolIdentifier: SYMBOLIDENTIFIER,
    /**
     * If the symbol is a subnode
     */
    isSubnode: PropTypes.bool,
    /**
     * All symbols that are currently highlighted
     */
    highlightedSymbols: PropTypes.array,
    /**
     * The reasons of the symbol
     */
    reasons: PropTypes.array,
    /**
     * The function to be called if the symbol is clicked on
     */
    handleClick: PropTypes.func,

}

