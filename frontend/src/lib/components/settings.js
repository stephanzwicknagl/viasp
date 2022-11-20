import React from "react";
import {useColorPalette} from "../contexts/ColorPalette";
import {setBackendURL, toggleShowAll, useSettings} from "../contexts/Settings";
import {useHighlightedSymbol} from "../contexts/HighlightedSymbol";
import {GoCheck, GoStop, IoCloseSharp, IoInformationCircleOutline, IoOptionsSharp} from "react-icons/all";
import {IconContext} from "react-icons";
import './settings.css'
import PropTypes from "prop-types";

const FORM_ID = 'settings_form'

function ClearMarked() {
    const [,, setHighlightedSymbol] = useHighlightedSymbol()
    const colorPalette = useColorPalette();
    return <tr>
        <td align="right">Reasoning:</td>
        <td align="center">
            <span style={{ backgroundColor: colorPalette.sixty.bright }}
                className="display_all_toggle_span noselect"
                onClick={() => setHighlightedSymbol([])}> 
                <span className="toggle_part unselected" style={{"padding-right": "16px","padding-left":"16px"}}>clear marked symbols</span>
            </span>
        </td>
    </tr>
}

function useToggleState(toggle_state) {
    let classNameNew = `toggle_part ${toggle_state.show_all ? "unselected" : "selected"}`;
    let label = toggle_state.show_all ? "Added symbols" : "All symbols";
    React.useEffect(() => {
        classNameNew = `toggle_part ${toggle_state.show_all ? "unselected" : "selected"}`;

    }, [toggle_state.show_all])
    return [classNameNew, label]

}

function ShowAllToggle() {
    const {state, dispatch} = useSettings()
    const [classNameNew, label] = useToggleState(state);
    const colorPalette = useColorPalette();
    const [, , setHighlightedSymbol] = useHighlightedSymbol()

    return <tr>
        <td align="right">Nodes show:</td>
        <td align="center">
        <span style={{backgroundColor: colorPalette.sixty.bright}}
              className="display_all_toggle_span noselect"
                onClick={() => {dispatch(toggleShowAll()); setHighlightedSymbol([])}}>
                <span className={classNameNew} style={state.show_all ? null : {
                backgroundColor: colorPalette.ten.bright,
                "color": colorPalette.sixty.bright
            }}>{label}</span>
        </span>
        </td>
    </tr>
}

function BackendHealthCheck() {
    const {state, backendURL} = useSettings()
    const [backendReachable, setBackendReachable] = React.useState(true)
    React.useEffect(() => {
        fetch(backendURL("healthcheck")).then(() => {
            setBackendReachable(true)
        }).catch(() => {
            setBackendReachable(false)
        })
    }, [backendURL])
    return <tr>
        <td align="right">Health:</td>
        <td>{backendReachable ?
            <span style={{"fontSize": "12px"}}><IconContext.Provider
                value={{color: "green"}}><GoCheck/></IconContext.Provider> Backend reachable</span> :
            <span style={{"fontSize": "12px"}}><IconContext.Provider
                value={{color: "red"}}><GoStop/></IconContext.Provider> Backend unreachable</span>}</td>
    </tr>
}

function BackendURLSetting(props) {
    const {input} = props;

    return <tr>
        <td align="right">URL:</td>
        <td>
            <input id="form_backendURL" type="text" form={FORM_ID} defaultValue={input}/>
            <input type="submit" form={FORM_ID} value="Save"/>
        </td>
    </tr>
}

BackendURLSetting.propTypes = {
    /**
     * The default value to be displayed
     */
    input: PropTypes.string
}

function Header(props) {
    const {text} = props;
    return <tr>
        <td className="settings_header" align="center" colSpan="3">{text}</td>
    </tr>
}

Header.propTypes = {
    /**
     * The text to be displayed in the header
     */
    text: PropTypes.string
}


function SettingsTable() {

    const {state, dispatch} = useSettings()

    function onSubmit(e) {
        dispatch(setBackendURL(e.target.elements.form_backendURL.value))
        e.preventDefault()
    }

    return <React.Fragment>
        <form method="GET" id={FORM_ID} onSubmit={onSubmit}/>
        <table>
            <tbody>
            <Header text="Display"/>
            <ShowAllToggle/>
            <ClearMarked/>
            <Header text="Backend"/>
            <BackendURLSetting input={state.backend_url}/>
            <BackendHealthCheck/>
            </tbody>
        </table>
    </React.Fragment>
}

export function Settings() {
    const colorPalette = useColorPalette();
    const [drawnOut, setDrawnOut] = React.useState(false);
    return <div className="settings noselect">
                <span className="drawer_toggle"
                      style={{backgroundColor: colorPalette.ten.dark, color: colorPalette.sixty.bright}}
                      onClick={() => setDrawnOut(!drawnOut)}>{drawnOut ? <IoCloseSharp size={28}/> :
                    <IoOptionsSharp size={28}/>}</span>
        <div className="drawer" style={{backgroundColor: colorPalette.sixty.dark}}>
            <div className="drawer_content"
                 style={drawnOut ? {
                     maxWidth: "500px",
                     backgroundColor: colorPalette.sixty.dark
                 } : {maxWidth: "0px", backgroundColor: colorPalette.sixty.dark}}>
                <SettingsTable/>
            </div>
        </div>
    </div>
}
