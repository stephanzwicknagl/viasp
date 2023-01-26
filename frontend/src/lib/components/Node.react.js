import React from "react";
import {make_atoms_string} from "../utils/index";
import './node.css'
import PropTypes, { symbol } from "prop-types";
import {hideNode, showNode, useShownNodes} from "../contexts/ShownNodes";
import {useColorPalette} from "../contexts/ColorPalette";
import {useHighlightedNode} from "../contexts/HighlightedNode";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import {useSettings} from "../contexts/Settings";
import {NODE, SYMBOLIDENTIFIER} from "../types/propTypes";
import {useFilters} from "../contexts/Filters";
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
        style = {"backgroundColor": compareHighlightedSymbol[i].color};
    }
    else if (j !== -1) {
        classNames = `mouse_over_symbol mark_symbol`;
    }
    return [classNames, style]
}

function NodeContent(props) {

    const {state} = useSettings();
    const {node,setHeight, parentID} = props;
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
        if (reasons.every(tgt => tgt !== null)){
            toggleHighlightedSymbol(reasons.map(tgt => { return { "src": src.uuid, "tgt": tgt.uuid } }), highlightedSymbol);
        }
    }

    const visibilityManager = (compareHighlightedSymbol, symbol) => {
        const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol.uuid);
        if (i !== -1) {
            const childRect = document.getElementById(symbol.uuid).getBoundingClientRect();
            const parentRect = document.getElementById(parentID).getBoundingClientRect();
            return childRect.bottom - parentRect.top;
        };
        return 0;
    }

    React.useEffect(() => {
        var newDiffs = contentToShow.filter(symbol => symbolShouldBeShown(symbol)).map(s => visibilityManager(highlightedSymbol, s)).filter(s => s > 0);
        setHeight(Math.max(...newDiffs, 80));
    }, [highlightedSymbol])

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
    const [, toggleShownRecursion,] = useShownRecursion();
    const [, , setHighlightedSymbol] = useHighlightedSymbol();

    function handleClick(e) {
        e.stopPropagation();
        toggleShownRecursion(node.uuid);
        setHighlightedSymbol([]);
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
    const [height, setHeight] = React.useState(80);
    // state updater to force other components to update
    const [, , startAnimationUpdater, stopAnimationUpdater] = useAnimationUpdater();

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

    let divID = `${node.uuid}_animate_height`;

    return <div className={classNames}
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}
                id={node.uuid} onClick={() => notifyClick(node)}>
        {showMini ? <div style={{"backgroundColor": colorPalette.ten.dark, "color": colorPalette.ten.dark}}
                         className={"mini"}/> :
            <div className={"set_too_high"} ref={ref}>
                <AnimateHeight
                    id={divID}
                    duration={500}
                    height={height} 
                    onHeightAnimationStart={startAnimationUpdater} 
                    onHeightAnimationEnd={stopAnimationUpdater}>
                    <NodeContent node={node} setHeight={setHeight} parentID={divID}/>
                    <RecursionButton node={node} /></AnimateHeight>
                    </div>}
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


export function RecursiveNode(props) {
    const { node, notifyClick, showMini } = props;
    const [isOverflowV, setIsOverflowV] = React.useState(false);
    const colorPalette = useColorPalette();
    const [, dispatch] = useShownNodes();
    const { state } = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node);
    // state updater to force other components to update
    const [, , startAnimationUpdater, stopAnimationUpdater] = useAnimationUpdater();

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
    style={{ "backgroundColor": colorPalette.fourty.dark, "color": colorPalette.ten.dark }}
        id={node.uuid} onClick={(e) => { e.stopPropagation(); notifyClick(node) }} >
        {node.recursive._graph.nodes.map((subnode) => {
            const [height, setHeight] = React.useState(80);
            let divID = `${node.uuid}_animate_height`;
            const classNames2 = useHighlightedNodeToCreateClassName(subnode.id);
            return <div className={classNames2}
                style={{ "backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark }}
                id={subnode.id.uuid} onClick={(e) => {e.stopPropagation(); notifyClick(subnode.id)}}>
                {showMini ? <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.ten.dark }}
                    className={"mini"} /> :
                    <div className={"set_too_high"} ref={ref} >
                        <AnimateHeight
                            id={divID}
                            duration={500}
                            height={height} 
                            onHeightAnimationStart={startAnimationUpdater}
                            onHeightAnimationEnd={stopAnimationUpdater}>
                        <NodeContent node={subnode.id} setHeight={setHeight} parentID={divID} />
                        <RecursionButton node={subnode.id} /></AnimateHeight></div>}
                {!showMini && isOverflowV ?
                    <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}
                        className={"noselect bauchbinde"}>...</div> : null}
            </div>
        })}
            <RecursionButton node={node} />
    </div>
}

RecursiveNode.propTypes = {
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
