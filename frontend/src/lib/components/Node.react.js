import React from "react";
import { make_atoms_string } from "../utils/index";
import './node.css'
import PropTypes, { symbol } from "prop-types";
import { hideNode, showNode, useShownNodes } from "../contexts/ShownNodes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useHighlightedNode } from "../contexts/HighlightedNode";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useSettings } from "../contexts/Settings";
import { NODE, SYMBOLIDENTIFIER } from "../types/propTypes";
import { useFilters } from "../contexts/Filters";
import AnimateHeight from 'react-animate-height';
import { useAnimationUpdater } from "../contexts/AnimationUpdater";


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
        style = { "backgroundColor": compareHighlightedSymbol[i].color };
    }
    else if (j !== -1) {
        classNames = `mouse_over_symbol mark_symbol`;
    }
    return [classNames, style]
}

function NodeContent(props) {

    const { state } = useSettings();
    const { node, setHeight, parentID, setIsOverflowV, expandNode } = props;
    const colorPalette = useColorPalette();
    const [{ activeFilters },] = useFilters();
    const [highlightedSymbol, toggleHighlightedSymbol,] = useHighlightedSymbol();
    const standardNodeHeight = 80;
    const minimumNodeHeight = 34;

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
        if (reasons.every(tgt => tgt !== null)) {
            toggleHighlightedSymbol(reasons.map(tgt => { return { "src": src.uuid, "tgt": tgt.uuid } }), highlightedSymbol);
        }
    }

    function symbolVisibilityManager(compareHighlightedSymbol, symbol) {
        const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol.uuid);
        const childRect = document.getElementById(symbol.uuid).getBoundingClientRect();
        const parentRect = document.getElementById(parentID).getBoundingClientRect();
        return { "fittingHeight": childRect.bottom - parentRect.top, "isMarked": i !== -1 };
    }

    function visibilityManager() {
        var allHeights = contentToShow
            .filter(symbol => symbolShouldBeShown(symbol))
            .map(s => symbolVisibilityManager(highlightedSymbol, s));
        var markedItems = allHeights.filter(item => item.isMarked);
        var maxSymbolHeight = Math.max(minimumNodeHeight, ...allHeights.map(item => item.fittingHeight))

        if (expandNode) {
            setHeight(maxSymbolHeight);
            setIsOverflowV(false)
        }
        else { // marked node is under the fold
            if (markedItems.length && any(markedItems.map(item => item.fittingHeight > standardNodeHeight))) {
                setHeight(height => {
                    Math.max(height, Math.max(...markedItems.map(item => item.fittingHeight)));
                    setIsOverflowV(maxSymbolHeight > height)
                });
            }
            else { // marked node is not under the fold
                setHeight(height => Math.max(height, Math.min(standardNodeHeight, maxSymbolHeight)));
                setIsOverflowV(maxSymbolHeight > standardNodeHeight)
            }
        };
    }

    React.useEffect(() => {
        visibilityManager();
        onFullyLoaded(() => visibilityManager());
    }, [highlightedSymbol, state, expandNode, activeFilters])

    function onFullyLoaded(callback) {
        setTimeout(function () {
            requestAnimationFrame(callback)
        })
    }
    React.useEffect(() => {
        window.addEventListener('resize', visibilityManager);
        return _ => window.removeEventListener('resize', visibilityManager)
    })

    const classNames2 = `set_value`
    const containerNames = `set_container`
    let renderedSymbols = contentToShow.filter(symbol =>
        symbolShouldBeShown(symbol)).map(s => {
            const [classNames1, style1] = useHighlightedSymbolToCreateClassName(highlightedSymbol, s.uuid);
            return <div className={classNames1} style={style1} onClick={(e) => handleClick(e, s)}>
                <Symbol key={JSON.stringify(s)} symbolId={s} />
            </div>
        })

    return <div className={containerNames} style={{ "color": colorPalette.thirty.bright }}>
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
    const { node } = props;
    const [, toggleShownRecursion,] = useShownRecursion();
    const [, , setHighlightedSymbol] = useHighlightedSymbol();
    const colorPalette = useColorPalette();


    function handleClick(e) {
        e.stopPropagation();
        toggleShownRecursion(node.uuid);
        setHighlightedSymbol([]);
    }

    return <div className={"recursion_button"} onClick={handleClick}>
        {!node.recursive ? null :
            <div className={"recursion_button_text"} style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}>
                <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 64 64"><path fill="#4d5357" d="m39.5 61.1l-6.4-8.7h-.8c-5.6 0-10.2-3.6-10.2-8V25h8l-14-19.2L2 25h8v19.4c0 4.7 2.3 9.1 6.6 12.4c4.2 3.3 9.8 5.2 15.8 5.2c2.4 0 4.8-.3 7.1-.9m-7.8-49.5c5.6 0 10.2 3.6 10.2 8v19.5h-8L48 58.3l14-19.2h-8V19.6c0-4.7-2.3-9.1-6.5-12.4C43.3 3.8 37.7 2 31.7 2c-2.5 0-4.9.3-7.2.9l6.4 8.7h.8" /></svg>
            </div>
        }
    </div>
}

function OverflowButton(props) {
    const { setExpandNode } = props;
    const colorPalette = useColorPalette();

    function handleClick(e) {
        e.stopPropagation();
        setExpandNode(true);
    }

    return <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}
                className={"bauchbinde"} onClick={handleClick}>
        <div className={"bauchbinde_text"}>...</div>
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
    const { node, notifyClick, showMini } = props;
    const [isOverflowV, setIsOverflowV] = React.useState(false);
    const colorPalette = useColorPalette();
    const [, dispatch] = useShownNodes();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const [height, setHeight] = React.useState(0);
    const [expandNode, setExpandNode] = React.useState(false);
    // state updater to force other components to update
    const [, , startAnimationUpdater, stopAnimationUpdater] = useAnimationUpdater();

    React.useEffect(() => {
        dispatch(showNode(node.uuid))
        return () => {
            dispatch(hideNode(node.uuid))
        }
    }, [])
    React.useEffect(() => {

    })

    const divID = `${node.uuid}_animate_height`;

    return <div className={classNames}
        style={{ "backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark }}
        id={node.uuid}
        onClick={(e) => { e.stopPropagation(); notifyClick(node) }}>
        {showMini ?
            <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.ten.dark }}
                className={"mini"} /> :
            <div className={"set_too_high"}  >
                <AnimateHeight
                    id={divID}
                    duration={500}
                    height={height}
                    onHeightAnimationStart={startAnimationUpdater}
                    onHeightAnimationEnd={stopAnimationUpdater}>
                    <NodeContent
                        node={node}
                        setHeight={setHeight}
                        parentID={divID}
                        setIsOverflowV={setIsOverflowV}
                        expandNode={expandNode} />
                    <RecursionButton node={node} />
                </AnimateHeight>
            </div>
        }
        {!showMini && isOverflowV ?
            <OverflowButton setExpandNode={setExpandNode} /> : null}
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


export function RecursiveSuperNode(props) {
    const { node, notifyClick, showMini } = props;
    const colorPalette = useColorPalette();
    const [, dispatch] = useShownNodes();
    const classNames = useHighlightedNodeToCreateClassName(node);
    // state updater to force other components to update

    React.useEffect(() => {
        dispatch(showNode(node.uuid))
        return () => {
            dispatch(hideNode(node.uuid))
        }
    }, [])
    React.useEffect(() => {

    })

    return <div className={classNames}
        style={{ "backgroundColor": colorPalette.fourty.dark, "color": colorPalette.ten.dark }}
        id={node.uuid}
        onClick={(e) => { e.stopPropagation(); notifyClick(node) }} >
        <RecursionButton node={node} />
        {
            node.recursive._graph.nodes.
                map(e => e.id).
                map(subnode => {
                    return <Node key={subnode}
                        node={subnode}
                        notifyClick={notifyClick}
                        showMini={showMini} />
                })
        }
    </div>
}

RecursiveSuperNode.propTypes = {
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

