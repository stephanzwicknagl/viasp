import React, { useState } from "react";
import { make_atoms_string } from "../utils/index";
import './symbol.css';
import PropTypes from "prop-types";
import { SYMBOLIDENTIFIER } from "../types/propTypes";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";


export function Symbol(props) {
    const { symbolIdentifier, isSubnode, handleClick } = props;
    const [isHovered, setIsHovered] = useState(false);

    let atomString = make_atoms_string(symbolIdentifier.symbol)
    const suffix = `_${isSubnode ? "sub" : "main"}`
    let classNames = "symbol";
    let style = null;
    const {highlightedSymbol: compareHighlightedSymbol, getNextHoverColor} =
        useHighlightedSymbol();

    const combinedIndices = compareHighlightedSymbol
        .flatMap((item, index) =>
            [item.tgt, item.src].includes(symbolIdentifier.uuid) ? index : []
        )
        .filter((value, index, self) => self.indexOf(value) === index);

    if (combinedIndices.length > 0) {
        classNames += ' mark_symbol';
        const uniqueColors = [
            ...new Set(
                combinedIndices.map(
                    (index) => compareHighlightedSymbol[index].color
                ).reverse()
            ),
        ];

        const gradientStops = uniqueColors
            .map((color, index, array) => {
                const start = (index / array.length) * 100;
                const end = ((index + 1) / array.length) * 100;
                return `${color} ${start}%, ${color} ${end}%`;
            })
            .join(', ');
        style = {background: `linear-gradient(-45deg, ${gradientStops})`};
    }

    atomString = atomString.length === 0 ? "" : atomString;

    if (symbolIdentifier.has_reason && isHovered) {
        style = getNextHoverColor(
            compareHighlightedSymbol,
            symbolIdentifier.uuid
        );
    }

    const handleMouseEnter = () => setIsHovered(true);
    const handleMouseLeave = () => setIsHovered(false);

    return (<span 
            className={classNames} 
            id={symbolIdentifier.uuid + suffix} 
            style={style} 
            onClick={(e) => handleClick(e, symbolIdentifier)} 
            onMouseEnter={handleMouseEnter} 
            onMouseLeave={handleMouseLeave}>
                {atomString}
            </span>);
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

