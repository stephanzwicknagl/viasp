import React, {Suspense} from 'react';
import PropTypes from 'prop-types';
import {MAPZOOMSTATE} from '../types/propTypes';
import {RowTemplate} from '../components/Row.react';
import {Boxrow} from '../components/BoxRow.react';
import '../components/main.css';
import {Detail} from '../components/Detail.react';
import {Search} from '../components/Search.react';
import {Facts} from '../components/Facts.react';
import {Edges} from '../components/Edges.react';
import {Arrows} from '../components/Arrows.react';
import {ShownNodesProvider} from '../contexts/ShownNodes';
import {
    TransformationProvider,
    useTransformations,
    reorderTransformation,
    setCurrentSort,
    setCurrentDragged,
} from '../contexts/transformations';
import {ColorPaletteProvider} from '../contexts/ColorPalette';
import {HighlightedNodeProvider} from '../contexts/HighlightedNode';
import {
    showError,
    useMessages,
    UserMessagesProvider,
} from '../contexts/UserMessages';
import {EdgeProvider} from '../contexts/Edges';
import {useShownDetail, ShownDetailProvider} from '../contexts/ShownDetail';
import {Settings} from '../LazyLoader';
import {UserMessages} from '../components/messages';
import {
    DEFAULT_BACKEND_URL,
    SettingsProvider,
    useSettings,
} from '../contexts/Settings';
import {FilterProvider} from '../contexts/Filters';
import {
    HighlightedSymbolProvider,
    useHighlightedSymbol,
} from '../contexts/HighlightedSymbol';
import {
    ShownRecursionProvider,
    useShownRecursion,
} from '../contexts/ShownRecursion';
import {
    useAnimationUpdater,
    AnimationUpdaterProvider,
} from '../contexts/AnimationUpdater';
import DraggableList from 'react-draggable-list';
import {MapInteraction} from 'react-map-interaction';
import useResizeObserver from '@react-hook/resize-observer';
import * as Constants from '../constants';
import debounce from 'lodash.debounce';
import { useDebouncedAnimateResize } from '../hooks/useDebouncedAnimateResize';

function postCurrentSort(backendURL, hash) {
    return fetch(`${backendURL('graph/sorts')}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({hash: hash}),
    }).then((r) => {
        if (r.ok) {
            return r;
        }
        throw new Error(r.statusText);
    });
}

function GraphContainer(props) {
    const {notifyDash, scrollContainer, transform} = props;
    const {
        state: {transformations, canDrop, clingraphGraphics},
        dispatch: dispatchTransformation,
    } = useTransformations();
    const {highlightedSymbol} = useHighlightedSymbol();
    const [, message_dispatch] = useMessages();
    const {backendURL} = useSettings();
    const [, , setShownRecursion] = useShownRecursion();
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);
    const draggableListRef = React.useRef(null);
    const {setHighlightedSymbol} = useHighlightedSymbol();
    const clingraphUsed = clingraphGraphics.length > 0;

    function onMoveEnd(newList, movedItem, oldIndex, newIndex) {
        dispatchTransformation(setCurrentDragged(''));
        const indexOfOldItemAtNewIndex =
            oldIndex < newIndex ? newIndex - 1 : newIndex + 1;
        const newHash = canDrop[newList[indexOfOldItemAtNewIndex].hash] || '';

        if (newHash.length > 0) {
            setShownRecursion([]);
            setHighlightedSymbol([]);
            dispatchTransformation(reorderTransformation(oldIndex, newIndex));
            postCurrentSort(backendUrlRef.current, newHash)
                .catch((error) => {
                    messageDispatchRef.current(
                        showError(`Failed to set new current graph: ${error}`)
                    );
                })
                .then((r) => {
                    dispatchTransformation(setCurrentSort(newHash));
                });
            return;
        }
    }

    const graphContainerRef = React.useRef(null);
    return (
        <div className="graph_container" ref={graphContainerRef}>
            <Facts />
            <Suspense fallback={<div>Loading...</div>}>
                <Settings />
            </Suspense>
            <DraggableList
                ref={draggableListRef}
                itemKey="hash"
                template={RowTemplate}
                list={transformations}
                onMoveEnd={onMoveEnd}
                container={() => scrollContainer.current}
                autoScrollRegionSize={200}
                padding={0}
                unsetZIndex={true}
                commonProps={{transform}}
            />
            {clingraphUsed ? <Boxrow /> : null}
            {highlightedSymbol.length === 0 ? null : <Arrows />}
            {transformations.length === 0 ? null : <Edges />}
        </div>
    );
}

GraphContainer.propTypes = {
    /**
     * Objects passed to this functions will be available to Dash callbacks.
     */
    notifyDash: PropTypes.func,
    /**
     * Reference to the scrollable div containing the list of rows
     * This is used to calculate the scroll region for the draggable list
     */
    scrollContainer: PropTypes.object,
    /**
     * The current zoom transformation of the graph
     */
    transform: MAPZOOMSTATE,
};

function MainWindow(props) {
    const {notifyDash} = props;
    const {backendURL} = useSettings();
    const [, dispatch] = useMessages();
    const backendURLRef = React.useRef(backendURL);
    const dispatchRef = React.useRef(dispatch);
    const {setAnimationState} = useAnimationUpdater();
    const setAnimationStateRef = React.useRef(setAnimationState);
    const [ctrlPressed, setCtrlPressed] = React.useState(false);
    const [translationBounds, setTranslationBounds] = React.useState({
        scale: 1,
        translation: {xMin: 0, xMax: 0},
    });
    const [mapShiftValue, setMapShiftValue] = React.useState({
        translation: {x: 0, y: 0},
        scale: 1,
    });
    const contentDivRef = React.useRef(null);
    const translationRef = React.useRef('translation')

    useDebouncedAnimateResize(contentDivRef, translationRef);


    React.useEffect(() => {
        fetch(backendURLRef.current('graph/sorts')).catch(() => {
            dispatchRef.current(
                showError(
                    `Couldn't connect to server at ${backendURLRef.current('')}`
                )
            );
        });
    }, []);

    React.useEffect(() => {
        const setAnimationState = setAnimationStateRef.current;
        setAnimationState((oldValue) => ({
            ...oldValue,
            graph_zoom: {
                translation: {x: 0, y: 0},
                scale: 1,
            },
        }));
        return () => {
            setAnimationState((v) => {
                const {graph_zoom: _, ...rest} = v;
                return rest;
            });
        };
    }, []);

    React.useEffect(() => {
        const handleKeyDown = (event) => {
            if (event.key === 'Control') {
                setCtrlPressed(true);
            }
        };

        const handleKeyUp = (event) => {
            if (event.key === 'Control') {
                setCtrlPressed(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, []);

    // Manage Graph Zoom
    const {shownDetail} = useShownDetail();
    const prevShownDetail = React.useRef(null);

    const handleMapChange = ({translation, scale}) => {
        if (ctrlPressed) {
            const newTranslation = {...translation};
            let newScale = scale;

            const contentWidth = contentDivRef.current.clientWidth;
            const rowWidth = contentWidth * newScale;
            const detailOpenWidth =
                shownDetail === null 
                ? 0
                : Constants.detailOpenWidthRatio * contentWidth;
            setTranslationBounds({
                scale: shownDetail === null 
                        ? 1
                        : 1 - Constants.detailOpenWidthRatio,
                translation: {
                    xMax: 0,
                    xMin: 
                        contentWidth -
                        rowWidth -
                        detailOpenWidth,
                },
            });

            setMapShiftValue(() => {
                if (newTranslation.x < translationBounds.translation.xMin) {
                    newTranslation.x = translationBounds.translation.xMin;
                }
                if (newTranslation.x > translationBounds.translation.xMax) {
                    newTranslation.x = translationBounds.translation.xMax;
                }
                if (newScale < translationBounds.scale) {
                    newScale = translationBounds.scale;
                }
                return {
                    translation: newTranslation,
                    scale: newScale,
                };
            });
        }
    };

    const handleMapChangeOnDetailChange = React.useCallback(() => {
        if (shownDetail === null && prevShownDetail.current !== null) {
            // close a potential gap between the right border of the graph
            // and the right border of the content div
            setMapShiftValue((oldShiftValue) => {
                const rowWidth =
                    contentDivRef.current.clientWidth * oldShiftValue.scale;
                const distanceOfRightSideOfGraphFromRightBorderUnderDetailSidebar =
                    contentDivRef.current.clientWidth -
                    oldShiftValue.translation.x -
                    rowWidth;
                if (
                    distanceOfRightSideOfGraphFromRightBorderUnderDetailSidebar <=
                    0
                ) {
                    return {...oldShiftValue};
                }
                if (oldShiftValue.scale < 1) {
                    return {
                        scale: 1,
                        translation: {
                            ...oldShiftValue,
                            x: 0,
                        },
                    };
                }
                return {
                    ...oldShiftValue,
                    translation: {
                        ...oldShiftValue.translation,
                        x:
                            oldShiftValue.translation.x +
                            distanceOfRightSideOfGraphFromRightBorderUnderDetailSidebar,
                    },
                };
            });
        }
        if (shownDetail !== null && prevShownDetail.current === null) {
            // if the graph is shifted all the way to the left
            // and the zoom scale is > 1, shift the graph to the left
            setMapShiftValue((oldShiftValue) => {
                const rowWidth =
                    contentDivRef.current.clientWidth * oldShiftValue.scale;
                const distanceOfRightSideOfGraphFromRightBorder =
                    rowWidth -
                    contentDivRef.current.clientWidth +
                    oldShiftValue.translation.x;
                if (
                    oldShiftValue.scale === 1 ||
                    distanceOfRightSideOfGraphFromRightBorder >=
                        Constants.detailOpenShiftThreshold *
                            contentDivRef.current.clientWidth
                ) {
                    return {...oldShiftValue};
                }
                return {
                    ...oldShiftValue,
                    translation: {
                        ...oldShiftValue.translation,
                        x:
                            oldShiftValue.translation.x -
                            Constants.detailOpenWidthRatio *
                                contentDivRef.current.clientWidth -
                            distanceOfRightSideOfGraphFromRightBorder,
                    },
                };
            });
        }
        prevShownDetail.current = shownDetail;
    }, [setMapShiftValue, shownDetail]);

    React.useEffect(() => {
        handleMapChangeOnDetailChange();
    }, [shownDetail, handleMapChangeOnDetailChange]);

    const animateResize = React.useCallback(() => {
        setMapShiftValue((oldShiftValue) => {
            const contentWidth = contentDivRef.current.clientWidth;
            const detailWidth = shownDetail === null
                ? 0
                : Constants.detailOpenWidthRatio * contentWidth;
            const rowWidth = contentWidth * oldShiftValue.scale;
            if (
                translationBounds.translation.xMin + oldShiftValue.translation.x >=
                Constants.detailOpenShiftThreshold * contentWidth
            ) {
                return {...oldShiftValue};
            }
            return {
                ...oldShiftValue,
                translation: {
                    ...oldShiftValue.translation,
                    x: 
                        contentWidth -
                        rowWidth -
                        detailWidth,
                },
            };
        });
    }, [shownDetail, translationBounds]);

    // const debouncedAnimateResize = React.useMemo(
    //     () => debounce(animateResize, Constants.DEBOUNCETIMEOUT),
    //     [animateResize]
    // );
    // useResizeObserver(contentDivRef, debouncedAnimateResize);

    // observe scroll position
    // Add a state for the scroll position
    const [scrollPosition, setScrollPosition] = React.useState(0);

    // Add an effect to update the scroll position state when the contentDiv scrolls
    React.useEffect(() => {
        const contentDiv = contentDivRef.current;
        const handleScroll = (event) => {
            setScrollPosition(event.target.scrollTop)
        };


        if (contentDiv) {
            contentDiv.addEventListener('scroll', handleScroll);
        }

        return () => {
            if (contentDiv) {
                contentDiv.removeEventListener('scroll', handleScroll);
            }
        };
    }, [contentDivRef]);

    React.useEffect(() => {
        setAnimationState((oldValue) => ({
            ...oldValue,
            graph_zoom: {
                ...oldValue.graph_zoom,
                translation: {
                    x: mapShiftValue.translation.x,
                    y: scrollPosition,
                },
            },
        }));
    }, [mapShiftValue, scrollPosition, setAnimationState]);

    return (
        <>
            <div className="content" id="content" ref={contentDivRef}>
                <Search />
                <div
                    style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                    }}
                >
                    <MapInteraction
                        minScale={translationBounds.scale}
                        value={mapShiftValue}
                        onChange={({translation, scale}) =>
                            handleMapChange({translation, scale})
                        }
                    >
                        {() => {
                            return ctrlPressed ? (
                                <div
                                    className="scroll_overlay"
                                    style={{
                                        position: 'absolute',
                                        top: 0,
                                        left: 0,
                                        width: '100%',
                                        height: '100%',
                                        backgroundColor: 'transparent',
                                        zIndex: 1,
                                    }}
                                ></div>
                            ) : null;
                        }}
                    </MapInteraction>
                </div>
                <GraphContainer
                    notifyDash={notifyDash}
                    scrollContainer={contentDivRef}
                    transform={mapShiftValue}
                />
            </div>
            <Detail />
        </>
    );
}

MainWindow.propTypes = {
    /**
     * Objects passed to this functions will be available to Dash callbacks.
     */
    notifyDash: PropTypes.func,
};

/**
 * ViaspDash is the main dash component
 */
export default function ViaspDash(props) {
    const {id, backendURL, setProps, colorPalette} = props;

    function notifyDash(clickedOn) {
        setProps({clickedOn: clickedOn});
    }

    return (
        <div id={id}>
            <ColorPaletteProvider colorPalette={colorPalette}>
                <SettingsProvider backendURL={backendURL}>
                    <HighlightedNodeProvider>
                        <ShownRecursionProvider>
                            <ShownDetailProvider>
                                <FilterProvider>
                                    <AnimationUpdaterProvider>
                                        <UserMessagesProvider>
                                            <ShownNodesProvider>
                                                <TransformationProvider>
                                                    <HighlightedSymbolProvider>
                                                        <EdgeProvider>
                                                            <div>
                                                                <UserMessages />
                                                                <MainWindow
                                                                    notifyDash={
                                                                        notifyDash
                                                                    }
                                                                />
                                                            </div>
                                                        </EdgeProvider>
                                                    </HighlightedSymbolProvider>
                                                </TransformationProvider>
                                            </ShownNodesProvider>
                                        </UserMessagesProvider>
                                    </AnimationUpdaterProvider>
                                </FilterProvider>
                            </ShownDetailProvider>
                        </ShownRecursionProvider>
                    </HighlightedNodeProvider>
                </SettingsProvider>
            </ColorPaletteProvider>
        </div>
    );
}

ViaspDash.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * Dash-assigned callback that should be called to report property changes
     * to Dash, to make them available for callbacks.
     */
    setProps: PropTypes.func,
    /**
     * Colors to be used in the application.
     */
    colorPalette: PropTypes.object,
    /**
     * Object to set by the notifyDash callback
     */
    clickedOn: PropTypes.object,

    /**
     * The url to the viasp backend server
     */
    backendURL: PropTypes.string,
};

ViaspDash.defaultProps = {
    colorPalette: {},
    clickedOn: {},
    backendURL: DEFAULT_BACKEND_URL,
};
