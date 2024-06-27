import React, {Suspense} from 'react';
import './node.css';
import PropTypes from 'prop-types';
import {Symbol} from './Symbol.react';
import {hideNode, showNode, useShownNodes} from '../contexts/ShownNodes';
import {useColorPalette} from '../contexts/ColorPalette';
import {useHighlightedNode} from '../contexts/HighlightedNode';
import {useHighlightedSymbol} from '../contexts/HighlightedSymbol';
import {toggleShownRecursion, useTransformations, setNodeIsCollapsibleV, setNodeShowMini, setNodeIsExpandableV, checkTransformationExpandableCollapsible} from '../contexts/transformations';
import {useSettings} from '../contexts/Settings';
import {useShownDetail} from '../contexts/ShownDetail';
import {NODE} from '../types/propTypes';
import {useFilters} from '../contexts/Filters';
import AnimateHeight from 'react-animate-height';
import {useAnimationUpdater} from '../contexts/AnimationUpdater';
import {IconWrapper} from '../LazyLoader';
import useResizeObserver from '@react-hook/resize-observer';
import {findChildByClass} from '../utils';
import debounce from 'lodash.debounce';
import * as Constants from '../constants';
import {useDebouncedAnimateResize} from '../hooks/useDebouncedAnimateResize';

function any(iterable) {
    for (let index = 0; index < iterable.length; index++) {
        if (iterable[index]) {
            return true;
        }
    }
    return false;
}

function NodeContent(props) {
    const {state} = useSettings();
    const {node, setHeight, parentID, isSubnode, transformationId} =
        props;
    const colorPalette = useColorPalette();
    const [{activeFilters}] = useFilters();
    const {highlightedSymbol, toggleReasonOf} = useHighlightedSymbol();
    const {dispatch: dispatchTransformation} = useTransformations();

    let contentToShow;
    if (state.show_all) {
        contentToShow = node.atoms;
    } else {
        contentToShow = node.diff;
    }

    const isMounted = React.useRef(true);
    const setContainerRef = React.useRef(null);

    React.useEffect(() => {
        return () => {
            isMounted.current = false;
        };
    }, []);

    const symbolShouldBeShown = React.useCallback(
        (symbolId) => {
            return (
                activeFilters.length === 0 ||
                any(
                    activeFilters
                        .filter((filter) => filter._type === 'Signature')
                        .map(
                            (filter) =>
                                filter.name === symbolId.symbol.name &&
                                filter.args === symbolId.symbol.arguments.length
                        )
                )
            );
        },
        [activeFilters]
    );

    function handleClick(e, src) {
        e.stopPropagation();
        if (src.has_reason) {
            toggleReasonOf(src.uuid, node.uuid, highlightedSymbol);
        }
    }

    const symbolVisibilityManager = React.useCallback((
        compareHighlightedSymbol,
        symbol,
    ) => {
        const i = compareHighlightedSymbol
            .map((item) => item.tgt)
            .indexOf(symbol.uuid);
        const j = compareHighlightedSymbol
            .map((item) => item.src)
            .indexOf(symbol.uuid);
        const childElement = document.getElementById(
            symbol.uuid + `_${isSubnode ? 'sub' : 'main'}`
        );
        const parentElement = document.getElementById(parentID);

        if (!childElement || !parentElement) {
            return {fittingHeight: 0, isMarked: i !== -1 || j !== -1};
        }
        const childRect = childElement.getBoundingClientRect();
        const parentRect = parentElement.getBoundingClientRect();
        const belowLineMargin = 5;
        return {
            fittingHeight:
                childRect.bottom - parentRect.top + belowLineMargin,
            isMarked: i !== -1 || j !== -1,
        };
    }, [isSubnode, parentID]);
    
    const visibilityManager = React.useCallback(() => {
        var allHeights = contentToShow
            .filter((symbol) => symbolShouldBeShown(symbol))
            .map((s) =>
                symbolVisibilityManager(
                    highlightedSymbol,
                    s,
                    contentToShow.length === 1
                )
            );
        var markedItems = allHeights.filter((item) => item.isMarked);
        var maxSymbolHeight = Math.max(
            Constants.minimumNodeHeight,
            ...allHeights.map((item) => item.fittingHeight)
        );

        if (node.loading === true) {
            setHeight(Math.min(Constants.standardNodeHeight, maxSymbolHeight));
            dispatchTransformation(setNodeIsExpandableV(transformationId, node.uuid, false));
            return;
        }
        if (node.isExpandVAllTheWay) {
            setHeight(maxSymbolHeight);
            dispatchTransformation(setNodeIsExpandableV(transformationId, node.uuid, false));
        } else {
            // marked node is under the standard height fold
            if (
                markedItems.length &&
                any(
                    markedItems.map(
                        (item) => item.fittingHeight > Constants.standardNodeHeight
                    )
                )
            ) {
                const newHeight = Math.max(
                    ...markedItems.map((item) => item.fittingHeight)
                );
                setHeight(newHeight);
                dispatchTransformation(setNodeIsExpandableV(transformationId, node.uuid, maxSymbolHeight > newHeight));
            } else {
                // marked node is not under the standard height fold
                setHeight(Math.min(Constants.standardNodeHeight, maxSymbolHeight));
                dispatchTransformation(setNodeIsExpandableV(transformationId, node.uuid, maxSymbolHeight > Constants.standardNodeHeight));
            }
        }
        dispatchTransformation(checkTransformationExpandableCollapsible(transformationId));
    }, [
        contentToShow,
        highlightedSymbol,
        setHeight,
        symbolShouldBeShown,
        symbolVisibilityManager,
        node.loading,
        dispatchTransformation,
        node.uuid,
        node.isExpandVAllTheWay,
        transformationId
    ]);

    React.useEffect(() => {
        visibilityManager();
        onFullyLoaded(() => {
            if (isMounted.current) {
                visibilityManager();
            }
        });
    }, [
        visibilityManager,
        highlightedSymbol,
        state,
        node.isExpandVAllTheWay,
        activeFilters,
    ]);

    function onFullyLoaded(callback) {
        setTimeout(function () {
            requestAnimationFrame(callback);
        });
    }
    useResizeObserver(setContainerRef, visibilityManager);

    // const nodeUuidRef = React.useRef(node.uuid);
    // const {setAnimationState} = useAnimationUpdater();
    // const setAnimationStateRef = React.useRef(setAnimationState);
    // const animateResize = React.useCallback((entry) => {
    //     const nodeUuid = nodeUuidRef.current;
    //     const setAnimationState = setAnimationStateRef.current;
    //     setAnimationState((oldValue) => ({
    //         [nodeUuid]: {
    //             ...oldValue[nodeUuid],
    //             width: entry.contentRect.width,
    //             height: entry.contentRect.height,
    //             top: entry.contentRect.top,
    //             left: entry.contentRect.left,
    //         },
    //     }));
    // }, []);

    // const debouncedAnimateResize = React.useCallback(
    //     (entry) => {
    //         return debounce(
    //             () => animateResize(entry),
    //             Constants.DEBOUNCETIMEOUT
    //         );
    //     },
    //     [animateResize]
    // );
    // useResizeObserver(setContainerRef, debouncedAnimateResize);


    const classNames2 = `set_value`;
    const renderedSymbols = contentToShow
        .filter((symbol) => symbolShouldBeShown(symbol))
        .map((s) => {
            return (
                <Symbol
                    key={JSON.stringify(s)}
                    symbolIdentifier={s}
                    isSubnode={isSubnode}
                    handleClick={handleClick}
                />
            );
        });

    return (
        <div
            className={`set_container ${
                node.loading === true ? 'hidden' : ''
            }`}
            style={{color: colorPalette.dark}}
            ref={setContainerRef}
        >
            <span className={classNames2}>
                {renderedSymbols.length > 0 ? renderedSymbols : ''}
            </span>
        </div>
    );
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
     * If the node is a subnode
     */
    isSubnode: PropTypes.bool,
    /**
     * The id of the transformation the node belongs to
     */
    transformationId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

function RecursionButton(props) {
    const {node} = props;
    const {state, dispatch, reloadEdges} = useTransformations();
    const colorPalette = useColorPalette();

    function handleClick(e) {
        e.stopPropagation();
        dispatch(toggleShownRecursion(node.uuid));
        const shownRecursionNodes = Object.values(state.transformationNodesMap)
            .flat()
            .filter(n => n.shownRecursion)
            .map(n => n.uuid);
        if (node.shownRecursion) {
            shownRecursionNodes.splice(shownRecursionNodes.indexOf(node.uuid), 1)
        } else { 
            shownRecursionNodes.push(node.uuid)
        }
        reloadEdges(shownRecursionNodes, state.clingraphGraphics.length > 0);
    }

    return (
        <div className={'recursion_button'} onClick={handleClick}>
            {node.recursive.length === 0 ? null : (
                <div
                    className={'recursion_button_text'}
                    style={{
                        backgroundColor: colorPalette.primary,
                        color: colorPalette.light,
                    }}
                >
                    <Suspense fallback={<div>R</div>}>
                        <IconWrapper
                            icon={"clockwiseVerticalArrows"}
                            width="9"
                            height="9"
                        />
                    </Suspense>
                </div>
            )}
        </div>
    );
}

RecursionButton.propTypes = {
    /**
     * object containing the node data to be displayed
     * */
    node: NODE,
};

function useHighlightedNodeToCreateClassName(node) {
    const [highlightedNode] = useHighlightedNode();
    const [classNames, setClassNames] = React.useState(
        `txt-elem node_border mouse_over_shadow ${node.uuid} ${
            highlightedNode === node.uuid ? 'highlighted_node' : null
        }`
    );

    React.useEffect(() => {
        if(highlightedNode === node.uuid) {
            console.log('highlighted node', node.uuid)
        }
        setClassNames(
            `txt-elem node_border mouse_over_shadow ${node.uuid} ${
                highlightedNode === node.uuid ? 'highlighted_node' : null
            }`
        );
    }, [node.uuid, highlightedNode]);

    return classNames;
}

function checkForOverflowE(
    branchSpace,
    showMini,
    overflowBreakingPoint,
    setOverflowBreakingPoint,
    setShowMini
) {
    if (
        typeof branchSpace !== 'undefined' &&
        branchSpace !== null &&
        branchSpace.current
    ) {
        const e = branchSpace.current;
        const setContainer = findChildByClass(e, 'set_too_high');
        const nodeBorder = findChildByClass(e, 'node_border');
        const wouldOverflowNow = setContainer
            ? setContainer.scrollWidth >
              nodeBorder.offsetWidth
               - Constants.overflowThreshold
            : false;
        // We overflowed previously but not anymore
        if (
            overflowBreakingPoint <=
            e.offsetWidth - Constants.overflowThreshold
        ) {
            setShowMini(false);
        }
        if (!showMini && wouldOverflowNow) {
            // We have to react to overflow now but want to remember when we'll not overflow anymore
            // on a resize
            setOverflowBreakingPoint(e.offsetWidth);
            setShowMini(true);
        }
        // We never overflowed and also don't now
        if (overflowBreakingPoint === null && !wouldOverflowNow) {
            setShowMini(false);
        }
    }
}

export function Node(props) {
    const {node, isSubnode, branchSpace, transformationId} = props;
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const colorPalette = useColorPalette();
    const {dispatch: dispatchShownNodes} = useShownNodes();
    const {dispatch: dispatchTransformation} = useTransformations();
    const classNames = useHighlightedNodeToCreateClassName(node);
    const [height, setHeight] = React.useState(Constants.minimumNodeHeight);
    const {animationState} = useAnimationUpdater();
    const {setShownDetail} = useShownDetail();
    const dispatchShownNodesRef = React.useRef(dispatchShownNodes);
    const nodeuuidRef = React.useRef(node.uuid);
    const animateHeightRef = React.useRef(null);

    useDebouncedAnimateResize(
        animateHeightRef, nodeuuidRef
    );

    const notifyClick = (node) => {
        // setShownDetail(node.uuid);
    };
    React.useEffect(() => {
        const dispatch = dispatchShownNodesRef.current;
        const nodeuuid = nodeuuidRef.current;
        dispatch(showNode(nodeuuid));
        return () => {
            dispatch(hideNode(nodeuuid));
        };
    }, []);


    React.useEffect(() => {
        dispatchTransformation(setNodeIsCollapsibleV(transformationId, node.uuid, height > Constants.standardNodeHeight));
    }, [height, dispatchTransformation, node.uuid, transformationId])

    const checkForOverflow = React.useCallback(() => {
        checkForOverflowE(
            branchSpace,
            node.showMini,
            overflowBreakingPoint,
            setOverflowBreakingPoint,
            (showMini) => {
                dispatchTransformation(setNodeShowMini(transformationId, node.uuid, showMini))
                dispatchTransformation(checkTransformationExpandableCollapsible(transformationId));
            }
        );
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [branchSpace, overflowBreakingPoint, animationState.graph_zoom, node.showMini]);
    
    const debouncedCheckForOverflow = React.useMemo(() => {
        return debounce(checkForOverflow, Constants.DEBOUNCETIMEOUT);
    }, [checkForOverflow]);

    React.useEffect(() => {
        checkForOverflow();
    }, [checkForOverflow, node.showMini]);   
    
    useResizeObserver(
        document.getElementById('content'),
        debouncedCheckForOverflow
    );

    const divID = `${node.uuid}_animate_height`;

    return (
        <div
            className={classNames}
            style={{
                backgroundColor: colorPalette.light,
                color: colorPalette.primary,
            }}
            id={node.uuid}
            onClick={(e) => {
                e.stopPropagation();
                notifyClick(node);
            }}
        >
            {node.showMini ? (
                <div
                    style={{
                        backgroundColor: colorPalette.primary,
                        color: colorPalette.primary,
                    }}
                    className={'mini'}
                />
            ) : (
                <AnimateHeight
                    id={divID}
                    duration={500}
                    height={height}
                    ref={animateHeightRef}
                    contentClassName={`set_too_high ${
                        node.loading === true ? 'loading' : null
                    }`}
                >
                    <NodeContent
                        node={node}
                        setHeight={setHeight}
                        parentID={divID}
                        isSubnode={isSubnode}
                        transformationId={transformationId}
                    />
                    <RecursionButton node={node} />
                </AnimateHeight>
            )}
        </div>
    );
}

Node.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * If the node is a subnode of a recursive node
     */
    isSubnode: PropTypes.bool,
    /**
     * The ref to the branch space the node sits in 
     */
    branchSpace: PropTypes.object,
    /**
     * The id of the transformation the node belongs to
     */
    transformationId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

export function RecursiveSuperNode(props) {
    const {node, branchSpace, transformationId} = props;
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState();
    const colorPalette = useColorPalette();
    const {dispatch: dispatchShownNodes} = useShownNodes();
    const classNames = `node_border ${node.uuid}`;
    const {setShownDetail} = useShownDetail();
    const {dispatch: dispatchTransformation} = useTransformations();
    const {animationState} = useAnimationUpdater();

    const dispatchShownNodesRef = React.useRef(dispatchShownNodes);
    const nodeuuidRef = React.useRef(node.uuid);

    const notifyClick = (node) => {
        setShownDetail(node.uuid);
    };

    React.useEffect(() => {
        const dispatch = dispatchShownNodesRef.current;
        const nodeuuid = nodeuuidRef.current;
        dispatch(showNode(nodeuuid));
        return () => {
            dispatch(hideNode(nodeuuid));
        };
    }, []);

    const checkForOverflow = React.useCallback(() => {
        checkForOverflowE(
            branchSpace,
            node.showMini,
            overflowBreakingPoint,
            setOverflowBreakingPoint,
            (showMini) => dispatchTransformation(setNodeShowMini(transformationId, node.uuid, showMini))
        );
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [branchSpace, node.showMini, overflowBreakingPoint, animationState.graph_zoom]);

    const debouncedCheckForOverflow = React.useMemo(() => {
        return debounce(checkForOverflow, Constants.DEBOUNCETIMEOUT);
    }, [checkForOverflow]);

    React.useEffect(() => {
        checkForOverflow();
    }, [checkForOverflow, node]);

    useResizeObserver(
        document.getElementById('content'),
        debouncedCheckForOverflow
    );
    
    return (
        <div
            className={classNames}
            style={{color: colorPalette.primary}}
            id={node.uuid}
            onClick={(e) => {
                e.stopPropagation();
                notifyClick(node);
            }}
        >
            {node.showMini ? (
                <div
                    style={{
                        backgroundColor: colorPalette.primary,
                        color: colorPalette.primary,
                    }}
                    className={'mini'}
                />
            ) : (
                <>
                    <RecursionButton node={node} />
                    {node.recursive
                        .map((subnode) => {
                            return (
                                <Node
                                key={subnode.uuid}
                                node={subnode}
                                notifyClick={notifyClick}
                                isSubnode={true}
                                transformationId={transformationId}
                                />
                                );
                        })}
                </>
            )}
        </div>
    );
}

RecursiveSuperNode.propTypes = {
    /**
     * object containing the node data to be displayed
    */
   node: NODE,
    /**
    * The ref to the branch space
    */
    branchSpace: PropTypes.object,
    /**
     * The id of the transformation the node belongs to
     */
    transformationId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};
