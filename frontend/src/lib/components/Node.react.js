import React, {Suspense} from "react";
import './node.css';
import PropTypes from "prop-types";
import { Symbol } from "./Symbol.react";
import { hideNode, showNode, useShownNodes } from "../contexts/ShownNodes";
import { useColorPalette } from "../contexts/ColorPalette";
import { useHighlightedNode } from "../contexts/HighlightedNode";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import { useSettings } from "../contexts/Settings";
import { useShownDetail } from "../contexts/ShownDetail";
import { NODE } from "../types/propTypes";
import { useFilters } from "../contexts/Filters";
import AnimateHeight from 'react-animate-height';
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import clockwiseVerticalArrows from '@iconify/icons-emojione-monotone/clockwise-vertical-arrows';
import arrowDownDoubleFill from '@iconify/icons-ri/arrow-down-double-fill';
import { IconWrapper } from '../LazyLoader';

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
    const { highlightedSymbol, toggleReasonOf } = useHighlightedSymbol();
    const standardNodeHeight = 80;
    const minimumNodeHeight = 34;

    let contentToShow;
    if (state.show_all) {
        contentToShow = node.atoms;
    } else {
        contentToShow = node.diff;
    }

    const symbolShouldBeShown = React.useCallback((symbolId) => {
        return activeFilters.length === 0 || any(activeFilters.filter(filter => filter._type === "Signature")
            .map(filter => filter.name === symbolId.symbol.name && filter.args === symbolId.symbol.arguments.length));
    }, [activeFilters])

    function handleClick(e, src) {
        e.stopPropagation();
        if (src.has_reason) {
            toggleReasonOf(src.uuid, node.uuid)
        }
    }



    const visibilityManager = React.useCallback(() => {
        function symbolVisibilityManager(compareHighlightedSymbol, symbol) {
            const i = compareHighlightedSymbol.map(item => item.tgt).indexOf(symbol.uuid);
            const j = compareHighlightedSymbol.map(item => item.src).indexOf(symbol.uuid);
            const childElement = document.getElementById(symbol.uuid + `_${isSubnode ? "sub" : "main"}`);
            const parentElement = document.getElementById(parentID);

            if (!childElement || !parentElement) {
                return { "fittingHeight": 0, "isMarked": i !== -1 || j !== -1 };
            }
            const childRect = childElement.getBoundingClientRect();
            const parentRect = parentElement.getBoundingClientRect();
            return { "fittingHeight": childRect.bottom - parentRect.top, "isMarked": i !== -1 || j !== -1 };
        }

        var allHeights = contentToShow
            .filter(symbol => symbolShouldBeShown(symbol))
            .map(s => symbolVisibilityManager(highlightedSymbol, s));
        var markedItems = allHeights.filter(item => item.isMarked);
        var maxSymbolHeight = Math.max(minimumNodeHeight, ...allHeights.map(item => item.fittingHeight))

        if (expandNode) {
            setHeight(maxSymbolHeight);
            setIsOverflowV(false)
        }
        else { 
            // marked node is under the fold
            if (markedItems.length && any(markedItems.map(item => item.fittingHeight > standardNodeHeight))) {
                setHeight(height => {
                    Math.max(height, Math.max(...markedItems.map(item => item.fittingHeight)));
                    setIsOverflowV(maxSymbolHeight > height)
                });
            }
            else { 
                // marked node is not under the fold
                setHeight(height => Math.max(height, Math.min(standardNodeHeight, maxSymbolHeight)));
                setIsOverflowV(maxSymbolHeight > standardNodeHeight)
            }
        };
    }, [contentToShow, highlightedSymbol, setHeight, setIsOverflowV, standardNodeHeight, minimumNodeHeight, expandNode, symbolShouldBeShown, isSubnode, parentID])


    React.useEffect(() => {
        visibilityManager();
        onFullyLoaded(() => visibilityManager());
    }, [visibilityManager, highlightedSymbol, state, expandNode, activeFilters])


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
    const renderedSymbols = contentToShow.filter(symbol =>
        symbolShouldBeShown(symbol)).map(s => {
            return <Symbol key={JSON.stringify(s)} symbolIdentifier={s} isSubnode={isSubnode} handleClick={handleClick}/>
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
    setIsOverflowV: PropTypes.func,
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
                    <IconWrapper icon={clockwiseVerticalArrows} width="9" height="9" />
                </Suspense>
            </div>
        }
    </div>
}

RecursionButton.propTypes = {
    /**
     * object containing the node data to be displayed
     * */
    node: NODE,
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
                <IconWrapper icon={arrowDownDoubleFill} width="12" height="12" />
            </Suspense>
        </div>
    </div>
}

OverflowButton.propTypes = {
    /**
     * The function to be called to set the node height
     *  */
    setExpandNode: PropTypes.func,
}


function useHighlightedNodeToCreateClassName(node) {
    const [highlightedNode,] = useHighlightedNode()
    const [classNames, setClassNames] = React.useState(`node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`);

    React.useEffect(() => {
        setClassNames(`node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`);
    }, [node.uuid, highlightedNode]);

    return classNames;
}

export function Node(props) {
    const { node, showMini, isSubnode } = props;
    const [isOverflowV, setIsOverflowV] = React.useState(false);
    const colorPalette = useColorPalette();
    const { dispatch: dispatchShownNodes } = useShownNodes();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const [height, setHeight] = React.useState(0);
    const [expandNode, setExpandNode] = React.useState(false);
    // state updater to force other components to update
    const [, , startAnimationUpdater, stopAnimationUpdater] = useAnimationUpdater();
    const { setShownDetail } = useShownDetail();
    
    const dispatchShownNodesRef = React.useRef(dispatchShownNodes);
    const nodeuuidRef = React.useRef(node.uuid);

    const notifyClick = (node) => {
        setShownDetail(node.uuid);
    }
    React.useEffect(() => {
        const dispatch = dispatchShownNodesRef.current;
        const nodeuuid = nodeuuidRef.current
        dispatch(showNode(nodeuuid))
        return () => {
            dispatch(hideNode(nodeuuid))
        }
    }, [])

    const divID = `${node.uuid}_animate_height`;

    return <div className={classNames}
        style={{ "backgroundColor": colorPalette.light, "color": colorPalette.primary }}
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
                    onHeightAnimationEnd={stopAnimationUpdater}
                    >
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
     * If true, shows the minified node without displaying its symbols
     */
    showMini: PropTypes.bool,
    /**
     * If the node is a subnode of a recursive node
     */
    isSubnode: PropTypes.bool
}


export function RecursiveSuperNode(props) {
    const { node, showMini } = props;
    const colorPalette = useColorPalette();
    const { dispatch: dispatchShownNodes } = useShownNodes();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const { setShownDetail } = useShownDetail();

    const dispatchShownNodesRef = React.useRef(dispatchShownNodes);
    const nodeuuidRef = React.useRef(node.uuid);

    const notifyClick = (node) => {
        setShownDetail(node.uuid);
    }

    React.useEffect(() => {
        const dispatch = dispatchShownNodesRef.current;
        const nodeuuid = nodeuuidRef.current
        dispatch(showNode(nodeuuid))
        return () => {
            dispatch(hideNode(nodeuuid))
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
     * If true, shows the minified node without displaying its symbols
     */
    showMini: PropTypes.bool,
}

