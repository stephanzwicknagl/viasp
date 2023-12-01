import React, {Suspense} from 'react';
import PropTypes from 'prop-types';
import { RowTemplate } from "../components/Row.react";
import { Boxrow } from "../components/BoxRow.react";
import "../components/main.css";
import {Detail} from "../components/Detail.react";
import {Search} from "../components/Search.react";
import {Facts} from "../components/Facts.react";
import { Edges } from "../components/Edges.react";
import { Arrows } from "../components/Arrows.react";
import { ShownNodesProvider } from "../contexts/ShownNodes";
import { TransformationProvider, useTransformations, reorderTransformation } from "../contexts/transformations";
import { ClingraphProvider, useClingraph } from '../contexts/Clingraph';
import { ColorPaletteProvider } from "../contexts/ColorPalette"; 
import {HighlightedNodeProvider} from "../contexts/HighlightedNode";
import {showError, useMessages, UserMessagesProvider} from "../contexts/UserMessages";
import { EdgeProvider, useEdges } from '../contexts/Edges';
import { ShownDetailProvider } from '../contexts/ShownDetail';
import { Settings } from '../LazyLoader';
import {UserMessages} from "../components/messages";
import {DEFAULT_BACKEND_URL, SettingsProvider, useSettings} from "../contexts/Settings";
import {FilterProvider} from "../contexts/Filters";
import { HighlightedSymbolProvider, useHighlightedSymbol } from '../contexts/HighlightedSymbol';
import { ShownRecursionProvider } from '../contexts/ShownRecursion';
import { AnimationUpdaterProvider } from '../contexts/AnimationUpdater';
import DraggableList from 'react-draggable-list';
import { computeSortHash } from '../utils';


function postCurrentSort(backendURL, hash) {
    return fetch(`${backendURL("graph/sorts")}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ hash: hash })
    }).then(r => {
        if (r.ok) {
            return r
        }
        throw new Error(r.statusText);
    });
}


function GraphContainer(props) {
    const {notifyDash} = props;
    const {state: {transformations, possibleSorts}, dispatch: dispatchTransformation} = useTransformations()
    const { clingraphUsed } = useClingraph();
    const [, message_dispatch] = useMessages()
    const { backendURL } = useSettings();
    const backendUrlRef = React.useRef(backendURL);
    const messageDispatchRef = React.useRef(message_dispatch);
    const graphContainerRef = React.useRef(null);


    function onMoveEnd(newList, movedItem, oldIndex, newIndex) {
        computeSortHash(newList.map(t => t.transformation.hash)).then((newHash) => {
            if (possibleSorts.includes(newHash)) {
                postCurrentSort(backendUrlRef.current, newHash).catch(error => {
                    messageDispatchRef.current(showError(`Failed to set new current graph: ${error}`))
                })
                dispatchTransformation(reorderTransformation(oldIndex, newIndex));
                return;
            }
        });
    }

    return <div className="graph_container" ref={graphContainerRef}>
        <Facts /><Suspense fallback={<div>Loading...</div>}><Settings /></Suspense>
        <DraggableList
            itemKey="hash"
            template={RowTemplate}
            list={transformations}
            onMoveEnd={onMoveEnd}
            container={() => graphContainerRef.current}
            padding = {0}
            // unsetZIndex = {true} 
          />
        { clingraphUsed ? <Boxrow /> : null}
        </div>
}

GraphContainer.propTypes = {
    /**
     * Objects passed to this functions will be available to Dash callbacks.
     */
    notifyDash: PropTypes.func,
}

function MainWindow(props) {
    const {notifyDash} = props;
    const {backendURL} = useSettings();
    const {state: {transformations}} = useTransformations()
    const { highlightedSymbol } = useHighlightedSymbol();
    const [, dispatch] = useMessages()
    const backendURLRef = React.useRef(backendURL)
    const dispatchRef = React.useRef(dispatch)


    React.useEffect(() => {
        fetch(backendURLRef.current("graph/sorts")).catch(() => {
            dispatchRef.current(showError(`Couldn't connect to server at ${backendURLRef.current("")}`))
        })
    }, [])

    return <div><Detail />
        <div className="content">
        <Search />
        <GraphContainer notifyDash={notifyDash} />
        {
            transformations.length === 0 ? null : <Edges />
        }
        {
            highlightedSymbol.length === 0 ? null : <Arrows />
        }
        </div>
    </div>
}

MainWindow.propTypes = {
    /**
     * Objects passed to this functions will be available to Dash callbacks.
     */
    notifyDash: PropTypes.func,
}

/**
 * ViaspDash is the main dash component
 */
export default function ViaspDash(props) {
    const {id, setProps, backendURL, colors} = props;

    function notifyDash(clickedOn) {
        setProps({clickedOn: clickedOn})
    }

    return <div id={id}>
        <ColorPaletteProvider colorPalette={colors}>
            <SettingsProvider backendURL={backendURL}>
                <HighlightedNodeProvider>
                    <HighlightedSymbolProvider>
                        <ShownRecursionProvider>
                            <ShownDetailProvider>
                                <FilterProvider>
                                    <AnimationUpdaterProvider>
                                            <UserMessagesProvider>
                                                <ShownNodesProvider>
                                                        <TransformationProvider>
                                                            <EdgeProvider>
                                                                <ClingraphProvider>
                                                                    <div>
                                                                        <UserMessages/>
                                                                        <MainWindow notifyDash={notifyDash}/>
                                                                    </div>
                                                                </ClingraphProvider>
                                                            </EdgeProvider>
                                                        </TransformationProvider>
                                                </ShownNodesProvider>
                                            </UserMessagesProvider>
                                    </AnimationUpdaterProvider>
                                </FilterProvider>
                            </ShownDetailProvider>
                        </ShownRecursionProvider>
                    </HighlightedSymbolProvider>
                </HighlightedNodeProvider>
            </SettingsProvider>
        </ColorPaletteProvider>
    </div>
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
    colors: PropTypes.object,
    /**
     * Object to set by the notifyDash callback
     */
    clickedOn: PropTypes.object,

    /**
     * The url to the viasp backend server
     */
    backendURL: PropTypes.string
};

ViaspDash.defaultProps = {
    colors: {},
    clickedOn: {},
    backendURL: DEFAULT_BACKEND_URL
}
