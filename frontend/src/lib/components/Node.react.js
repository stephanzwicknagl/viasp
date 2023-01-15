import React from "react";
import {make_atoms_string} from "../utils/index";
import './node.css'
import PropTypes from "prop-types";
import {hideNode, showNode, useShownNodes} from "../contexts/ShownNodes";
import {useColorPalette} from "../contexts/ColorPalette";
import {useHighlightedNode} from "../contexts/HighlightedNode";
import {useHighlightedSymbol} from "../contexts/HighlightedSymbol";
import {useSettings} from "../contexts/Settings";
import {NODE, SYMBOLIDENTIFIER} from "../types/propTypes";
import {useFilters} from "../contexts/Filters";


function any(iterable) {
    for (let index = 0; index < iterable.length; index++) {
        if (iterable[index]) {
            return true;
        }
    }
    return false;
}

function Symbol(props) {
    const { symbolId } = props;
    let atomString = make_atoms_string(symbolId.symbol)
    atomString = atomString.length === 0 ? "" : atomString;
    return <div className={"symbol"} id={symbolId.uuid}>{atomString}</div>
}

Symbol.propTypes = {
    /**
     * The symbolidentifier of the symbol to display
     */
    symbolId: SYMBOLIDENTIFIER
}

function useHighlightedSymbolToCreateClassName(compareHighlightedSymbol, symbol) {
    let classNames = `mouse_over_symbol`;
    let style = null;

    const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol);
    const j = compareHighlightedSymbol.map(item => item.src).indexOf(symbol);
    if (i !== -1) {
        classNames = `mouse_over_symbol mark_symbol`;
        style = {"backgroundColor": compareHighlightedSymbol[i].color};
    }
    else if (j !== -1) {
        classNames = `mouse_over_symbol mark_symbol`;
    }
    return [classNames, style]
}

function NodeContent(props) {

    const {state} = useSettings();
    const {node} = props;
    const colorPalette = useColorPalette();
    const [{activeFilters},] = useFilters();
    const [highlightedSymbol, toggleHighlightedSymbol,] = useHighlightedSymbol();

    let contentToShow;
    if (state.show_all) {
        contentToShow = node.atoms;
    } else {
        contentToShow = node.diff;
    }

    function symbolShouldBeShown(symbolId) {
        return activeFilters.length === 0 || any(activeFilters.filter(filter => filter._type === "Signature")
            .map(filter => filter.name === symbolId.symbol.name && filter.args === symbolId.symbol.arguments.length));
    }

    function handleClick(e, src) {
        e.stopPropagation();

        const reasons = node.reason[make_atoms_string(src.symbol)];
        if (reasons){
            reasons.map(tgt => {
                const childDiv = document.getElementById(tgt.uuid);
                const childRect= childDiv.getBoundingClientRect();
                const parentDiv = childDiv.parentElement.parentElement.parentElement.parentElement;
                const parentDiv1 = childDiv.parentElement.parentElement;

                const parentRect = parentDiv.getBoundingClientRect();
                if (childRect.bottom > parentRect.bottom) {
                    console.log(`Symbol: ${tgt.uuid} is NOT visible`);
                    // console.log("The parent Div is:", parentDiv1);
                    // console.log("The target is ", tgt);
                    const tgthtml = `<div class="mouse_over_symbol"><div class="symbol" id="${tgt.uuid}">${make_atoms_string(tgt.symbol)}</div></div>`;
                    let newInnerHtml = parentDiv1.innerHTML
                            .replace(tgthtml, "");
                    newInnerHtml = `<div class="mouse_over_symbol mark_symbol"><div class="symbol" id="${tgt.uuid}">${make_atoms_string(tgt.symbol)}</div></div>`.concat(newInnerHtml);
                    parentDiv1.innerHTML = newInnerHtml;
                } else {
                    // setIsBelowParentBorder(false);
                    console.log(`Symbol: ${tgt.uuid} is visible`)
                }
            })
            toggleHighlightedSymbol(reasons.map(tgt => { if (tgt.uuid) return { "src": src.uuid, "tgt": tgt.uuid }; else return null }), highlightedSymbol);
        }
    }

    const classNames2 = `set_value`
    const containerNames = `set_container`
    let renderedSymbols = contentToShow.filter(symbol => 
                symbolShouldBeShown(symbol)).map(s => {
                    const [classNames1, style1] = useHighlightedSymbolToCreateClassName(highlightedSymbol, s.uuid);
                    return <div className={classNames1} style={style1} onClick={(e) => handleClick(e,s)}>
                        <Symbol key={JSON.stringify(s)} symbolId={s} />
                        </div>})

    return <div className={containerNames} style={{"color": colorPalette.thirty.bright}}>
        <span className={classNames2}>{renderedSymbols.length > 0 ? renderedSymbols : ""}</span>
    </div>
}

NodeContent.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * If the Node will overflow vertically
     */
    overflowV: PropTypes.bool
}

function RecursionButton(props) {
    const {node} = props;

    function handleClick(e) {
        e.stopPropagation();
        console.log("Clicked on recursion button")
    }

    return <div className={"recursion_button"} onClick={handleClick}>
        {!node.recursive ? null:
            <div className={"recursion_button_text"}>R</div>
        }
    </div>
}

function useHighlightedNodeToCreateClassName(node) {
    const [highlightedNode,] = useHighlightedNode()
    let classNames = `node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`

    React.useEffect(() => {
            classNames = `node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`
        }, [node.uuid, highlightedNode]
    )
    return classNames
}

export function Node(props) {
    const {node, notifyClick, showMini} = props;
    const [isOverflowV, setIsOverflowV] = React.useState(false);
    const colorPalette = useColorPalette();
    const [, dispatch] = useShownNodes();
    const {state} = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const parentRef = React.useRef(null);
    const [parentRect, setParentRect] = React.useState(null);

    React.useEffect(() => {
        // Get the bounding rectangle for the previous element
        let rect = parentRef.current.getBoundingClientRect();
        setParentRect(rect);

        // Use the bounding rectangle to do something...
    }, [parentRef]);


    const ref = React.useCallback(x => {
        if (x !== null) {
            setIsOverflowV(x.scrollHeight > x.offsetHeight + 2);
        }
    }, [state]);
    React.useEffect(() => {
        dispatch(showNode(node.uuid))
        return () => {
            dispatch(hideNode(node.uuid))
        }
    }, [])
    React.useEffect(() => {

    })


    return <div className={classNames}
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}
                id={node.uuid} onClick={() => notifyClick(node)} ref={parentRef}>
        {showMini ? <div style={{"backgroundColor": colorPalette.ten.dark, "color": colorPalette.ten.dark}}
                         className={"mini"}/> :
            <div className={"set_too_high"} ref={ref}><NodeContent node={node} parentRect={parentRect} /><RecursionButton node={node} /></div>}
        {!showMini && isOverflowV ?
            <div style={{"backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark}}
                 className={"noselect bauchbinde"}>...</div> : null}
    </div>
}

Node.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * The function to be called if the facts are clicked on
     */
    notifyClick: PropTypes.func,
    /**
     * If true, shows the minified node without displaying its symbols
     */
    showMini: PropTypes.bool,
}

