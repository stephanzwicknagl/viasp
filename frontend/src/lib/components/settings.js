import React from "react";
import {useColorPalette} from "../contexts/ColorPalette";
import {useHighlightedSymbol} from "../contexts/HighlightedSymbol";
import './settings.css'


function makeClassNameFromMarkedSymbol(highlightedSymbol) {
    let className = `noselect toggle_part unselected ${highlightedSymbol.length === 0 ? "fadeOut" : "fadeIn"}`;
    return className;
}

function ClearMarked() {
    const [highlightedSymbol,, setHighlightedSymbol] = useHighlightedSymbol()
    const colorPalette = useColorPalette();
    const className = makeClassNameFromMarkedSymbol(highlightedSymbol)

    return <span onClick={() => setHighlightedSymbol([])}
                 className={className}
                 style={{ backgroundColor: colorPalette.success}}>
            clear marked symbols</span>
}

export function Settings() {

    return <div className="settings noselect" >
                <ClearMarked/>
            </div>
}
