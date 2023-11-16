import React, {lazy, Suspense} from "react";
import { make_atoms_string } from "../utils/index";
import './node.css';
import PropTypes from "prop-types";
import { Symbol } from "./Symbol.react";
import { hideNode, showNode, useShownNodes } from "../contexts/ShownNodes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useHighlightedNode } from "../contexts/HighlightedNode";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useSettings } from "../contexts/Settings";
import { NODE } from "../types/propTypes";
import { useFilters } from "../contexts/Filters";
import AnimateHeight from 'react-animate-height';
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import clockwiseVerticalArrows from '@iconify/icons-emojione-monotone/clockwise-vertical-arrows';
import arrowDownDoubleFill from '@iconify/icons-ri/arrow-down-double-fill';
import { IconWrapper as RealComponent } from '../LazyLoader';

function any(iterable) {
    for (let index = 0; index < iterable.length; index++) {
        if (iterable[index]) {
            return true;
        }
    }
    return false;
}

function NodeContent(props) {

    const { state } = useSettings();
    const { node, setHeight, parentID, setIsOverflowV, expandNode, isSubnode } = props;
    const colorPalette = useColorPalette();
    const [{ activeFilters },] = useFilters();
    const [highlightedSymbol, toggleHighlightedSymbol, setHighlightedSymbol] = useHighlightedSymbol();
    const [, toggleShownRecursion,] = useShownRecursion();
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

        if (!node.reason[make_atoms_string(src.symbol)]) {
            return;
        }
        let reasons = node.reason[make_atoms_string(src.symbol)];
        if (reasons.every(tgt => tgt !== null)) {
            toggleHighlightedSymbol(reasons.map(tgt => { return { "src": src.uuid, "tgt": tgt.uuid } }), highlightedSymbol);
        }
        else {
            let subNode = node.recursive._graph.nodes.filter(node => node.id.atoms.filter(atom => atom.uuid == src.uuid).length > 0);
            reasons = subNode[0].id.reason[make_atoms_string(src.symbol)];
            toggleShownRecursion(node.uuid);
            toggleHighlightedSymbol(reasons.map(tgt => { return { "src": src.uuid, "tgt": tgt.uuid } }), highlightedSymbol);
        }
    }

    function symbolVisibilityManager(compareHighlightedSymbol, symbol) {
        const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol.uuid);
        const j = compareHighlightedSymbol.map(item => item.src).indexOf(symbol.uuid);
        const childElement = document.getElementById(symbol.uuid + `_${isSubnode ? "sub" : "main"}`);
        const parentElement = document.getElementById(parentID);

        if (!childElement || !parentElement) {
            return { "fittingHeight": 0, "isMarked": i !== -1 || j !== -1 };
        }
        else {
            const childRect = childElement.getBoundingClientRect();
            const parentRect = parentElement.getBoundingClientRect();
            return { "fittingHeight": childRect.bottom - parentRect.top, "isMarked": i !== -1 || j !== -1 };
        }
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
            // const [classNames1, style1] = useHighlightedSymbolAndReasonToCreateClassName(highlightedSymbol, s.uuid, node.reason[make_atoms_string(s)]);
            return <Symbol key={JSON.stringify(s)} symbolIdentifier={s} isSubnode={isSubnode} reasons={node.reason[make_atoms_string(s)]} handleClick={handleClick}/>
        })

    return <div className={containerNames} style={{ "color": colorPalette.dark }}>
        <span className={classNames2}>{renderedSymbols.length > 0 ? renderedSymbols : ""}</span>
    </div>
}

NodeContent.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * The function to be called to set the node height
     */
    setHeight: PropTypes.func,
    /**
     * The id of the parent node
     */
    parentID: PropTypes.string,
    /**
     * Set the vertical overflow state of the Node
     */
    setIsdOverflowV: PropTypes.func,
    /**
     * If the node is expanded
     */
    expandNode: PropTypes.bool,
    /**
     * If the node is a subnode
     */
    isSubnode: PropTypes.bool
}

function RecursionButton(props) {
    const { node } = props;
    const [, toggleShownRecursion,] = useShownRecursion();
    const colorPalette = useColorPalette();


    function handleClick(e) {
        e.stopPropagation();
        toggleShownRecursion(node.uuid);
    }

    return <div className={"recursion_button"} onClick={handleClick}>
        {!node.recursive ? null :
            <div className={"recursion_button_text"} style={{ "backgroundColor": colorPalette.primary, "color": colorPalette.sixty.dark }}>
                <Suspense fallback={<div>R</div>}>
                    <RealComponent icon={clockwiseVerticalArrows} width="9" height="9" />
                </Suspense>
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

    return <div style={{ "backgroundColor": colorPalette.primary, "color": colorPalette.sixty.dark }}
                className={"bauchbinde"} onClick={handleClick}>
        <div className={"bauchbinde_text"}>
            <Suspense fallback={<div>...</div>}>
                <RealComponent icon={arrowDownDoubleFill} width="12" height="12" />
            </Suspense>
        </div>
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
    const { node, notifyClick, showMini, isSubnode } = props;
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
        style={{ "backgroundColor": colorPalette.light, "color": colorPalette.secondary }}
        id={node.uuid}
        onClick={(e) => { e.stopPropagation(); notifyClick(node) }}>
        {showMini ?
            <div style={{ "backgroundColor": colorPalette.primary, "color": colorPalette.primary }}
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
                        expandNode={expandNode}
                        isSubnode={isSubnode} />
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
        style={{ "backgroundColor": colorPalette.fourty.dark, "color": colorPalette.fourty.bright }}
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
                        showMini={showMini}
                        isSubnode = {true} />
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

