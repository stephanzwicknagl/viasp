import React from 'react';
import PropTypes from 'prop-types';
import {Row, Boxrow} from "../components/Row.react";
import "../components/main.css";
import {Detail} from "../components/Detail.react";
import {Search} from "../components/Search.react";
import {Facts} from "../components/Facts.react";
import {Edges} from "../components/Edges.react";
import {initialState, nodeReducer, ShownNodesProvider} from "../contexts/ShownNodes";
import {TransformationProvider, useTransformations} from "../contexts/transformations";
import {ColorPaletteProvider} from "../contexts/ColorPalette";
import {HighlightedNodeProvider} from "../contexts/HighlightedNode";
import {showError, useMessages, UserMessagesProvider} from "../contexts/UserMessages";
import {Settings} from "../components/settings";
import {UserMessages} from "../components/messages";
import {DEFAULT_BACKEND_URL, SettingsProvider, useSettings} from "../contexts/Settings";
import {FilterProvider} from "../contexts/Filters";


function loadClingraphUsed(backendURL) {
    return fetch(`${backendURL("control/clingraph")}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

function loadMarkedSymbols(uuid, backendURL) {
    return fetch(`${backendURL("detail/explain")}/${uuid}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

function GraphContainer(props) {
    const {setDetail, notifyDash, usingClingraph, markedSymbols} = props;
    const {state: {transformations}} = useTransformations()
    const lastNodeInGraph = transformations.length - 1;


    return <div className="graph_container">
        <Facts notifyClick={(clickedOn) => {
            console.log("clickedOn: ", clickedOn)
            notifyDash(clickedOn)
            setDetail(clickedOn.uuid)
            }}
            markedSymbols={markedSymbols}
        /><Settings/>
        {transformations.map(({transformation}, i) => {
            if (i === lastNodeInGraph && usingClingraph) {
                return <div>
                        <Row
                            key={transformation.id}
                            transformation={transformation}
                            notifyClick={(clickedOn) => {
                                console.log("clickedOn: ", clickedOn)
                                notifyDash(clickedOn)
                                setDetail(clickedOn.uuid)
                            }}
                            markedSymbols={markedSymbols}
                        />
                        <Boxrow
                            key={transformation.id}
                            transformation={transformation}
                        /></div>
            }
            else {
                return <Row
                    key={transformation.id}
                    transformation={transformation}
                    notifyClick={(clickedOn) => {
                        console.log("clickedOn: ", clickedOn)
                        notifyDash(clickedOn)
                        setDetail(clickedOn.uuid)
                    }}
                    markedSymbols={markedSymbols}
                    />
            }
        })}
        </div>
}

GraphContainer.propTypes = {
    /**
     * Objects passed to this functions will be available to Dash callbacks.
     */
    notifyDash: PropTypes.func,
    /**
     * If the detail component should be opened, set use this function to set the uuid
     */
    setDetail: PropTypes.func,
    /**
     * UsingClingraph is a boolean that is set to true if the backend is using clingraph
     */
    usingClingraph: PropTypes.bool
}

function MainWindow(props) {
    const {notifyDash} = props;
    const [detail, setDetail] = React.useState(null)
    const {backendURL} = useSettings();
    const {state: {transformations}} = useTransformations()
    const [usingClingraph, setUsingClingraph] = React.useState("false")
    const [marked, setMarked] = React.useState(null)

    React.useEffect(() => {
        let mounted = true;
        loadClingraphUsed(backendURL)
            .then(data => {
                if (mounted) {
                    setUsingClingraph(data.using_clingraph)
                }
            });
        return () => mounted = false;
    }, []);

    React.useEffect(() => {
        let mounted = true;
        console.log("detail changed:", detail)
        if (detail) {
            loadMarkedSymbols(detail, backendURL)
                .then(data => {
                    if (mounted) {
                        setMarked(data)
                        console.log("habe marked gesettet:", data)
                    }
                });
            }
    }, [detail]);

    const [, dispatch] = useMessages()
    React.useEffect(() => {
        fetch(backendURL("graph/transformations")).catch(() => {
            dispatch(showError(`Couldn't connect to server at ${backendURL("")}`))
        })
    }, [])

    return <div><Detail shows={detail} clearDetail={() => setDetail(null)}/>
        <div className="content">
            <ShownNodesProvider initialState={initialState} reducer={nodeReducer}>
                <Search setDetail={setDetail}/>
                <GraphContainer setDetail={setDetail} notifyDash={notifyDash} usingClingraph={usingClingraph} markedSymbols={marked}/>
                {
                    transformations.length === 0 ? null : <Edges usingClingraph={usingClingraph}/>
                }
            </ShownNodesProvider>
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
            <HighlightedNodeProvider>
                <FilterProvider>
                    <SettingsProvider backendURL={backendURL}>
                        <UserMessagesProvider>
                            <TransformationProvider>
                                <div>
                                    <UserMessages/>
                                    <MainWindow notifyDash={notifyDash}/>
                                </div>
                            </TransformationProvider>
                        </UserMessagesProvider>
                    </SettingsProvider>
                </FilterProvider>
            </HighlightedNodeProvider>
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
