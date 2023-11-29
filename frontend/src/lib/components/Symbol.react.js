import React, { useState } from "react";
import { make_atoms_string } from "../utils/index";
import './symbol.css';
import PropTypes from "prop-types";
import { SYMBOLIDENTIFIER } from "../types/propTypes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";


export function Symbol(props) {
    const { symbolIdentifier, isSubnode, handleClick } = props;
    const [isHovered, setIsHovered] = useState(false);
    const [isClicked, setIsClicked] = useState(false);
    const colorPalette = useColorPalette();

    let atomString = make_atoms_string(symbolIdentifier.symbol)
    const suffix = `_${isSubnode ? "sub" : "main"}`
    let classNames = "symbol";
    let style = null;
    const { highlightedSymbol: compareHighlightedSymbol } = useHighlightedSymbol();

    const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbolIdentifier.uuid);
    const j = compareHighlightedSymbol.map(item => item.src).indexOf(symbolIdentifier.uuid);
    if (i !== -1) {
        classNames += " mark_symbol";
        // all colors where item.tgt is equal to symbol
        const colors = compareHighlightedSymbol.map(item => item.tgt).map((item, index) => item === symbolIdentifier.uuid ? index : -1).filter(item => item !== -1).map(item => compareHighlightedSymbol[item].color).reverse();
        const gradientStops = colors.map((color, index, array) => {
            const start = (index / array.length) * 100;
            const end = ((index + 1) / array.length) * 100;
            return `${color} ${start}%, ${color} ${end}%`;
        }).join(', ');
        style = { background: `linear-gradient(-45deg, ${gradientStops})` };
    }
    else if (j !== -1) {
        classNames += " mark_symbol";
    }

    atomString = atomString.length === 0 ? "" : atomString;

    if (symbolIdentifier.has_reason && isHovered) {
        style = { backgroundColor: colorPalette.success };
    }
    if (symbolIdentifier.has_reason && isClicked) {
        style = { backgroundColor: colorPalette.info };
    }

    const handleMouseEnter = () => setIsHovered(true);
    const handleMouseLeave = () => setIsHovered(false);
    const handleMouseDown = () => setIsClicked(true);
    const handleMouseUp = () => setIsClicked(false);

    return (<div 
            className={classNames} 
            id={symbolIdentifier.uuid + suffix} 
            style={style} 
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
     * The function to be called if the symbol is clicked on
     */
    handleClick: PropTypes.func,

}

