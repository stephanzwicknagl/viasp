import React from 'react';
import PropTypes from 'prop-types';
import {Row} from "../components/Row.react";
import "../components/main.css"
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


function GraphContainer(props) {
    const {setDetail, notifyDash} = props;
    const {state: {transformations}} = useTransformations()
    const lastIndex = transformations.length - 1;
    return <div className="graph_container">
        <Facts notifyClick={(clickedOn) => {
            notifyDash(clickedOn)
            setDetail(clickedOn.uuid)
        }}/><Settings/>
        {transformations.map(({transformation}, i) => {
            return <Row
                key={transformation.id}
                transformation={transformation}
                notifyClick={(clickedOn) => {
                    notifyDash(clickedOn)
                    setDetail(clickedOn.uuid)
                }}
                isLast={i === lastIndex}        
                />
        })}</div>
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
}

function MainWindow(props) {
    const {notifyDash} = props;
    const [detail, setDetail] = React.useState(null)
    const {backendURL} = useSettings();
    const {state: {transformations}} = useTransformations()

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
                <GraphContainer setDetail={setDetail} notifyDash={notifyDash}/>
                {
                    transformations.length === 0 ? null : <Edges/>
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
