import React from 'react';
import {make_atoms_string} from "../utils/index";
import './detail.css';
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import { useShownDetail } from "../contexts/ShownDetail";
import {useSettings} from "../contexts/Settings";
import {SIGNATURE, SYMBOL} from "../types/propTypes";
import {IoChevronDown, IoChevronForward, IoCloseSharp} from "react-icons/io5";


function DetailSymbolPill(props) {
    const {symbol} = props;
    const colorPalette = useColorPalette();
    return <span className="detail_atom_view_content"
                 style={{
                     backgroundColor: colorPalette.fifty.dark,
                     color: colorPalette.thirty.bright
                 }}>{make_atoms_string(symbol)}</span>

}

DetailSymbolPill.propTypes = {
    /**
     * The symbol to display.
     */
    symbol: SYMBOL
}


function DetailForSignature(props) {
    const {signature, symbols} = props;
    const [showChildren, setShowChildren] = React.useState(true);
    const openCloseSymbol = showChildren ? <IoChevronDown/> : <IoChevronForward/>
    return <div>
        <hr/>
        <h3 className="detail_atom_view_heading noselect"
            onClick={() => setShowChildren(!showChildren)}>{openCloseSymbol} {signature.name}/{signature.args}</h3>
        <hr/>
        <div className="detail_atom_view_content_container">
            {showChildren ? symbols.map(symbol => <DetailSymbolPill key={JSON.stringify(symbol)}
                                                                    symbol={symbol}/>) : null}</div>
    </div>
}

DetailForSignature.propTypes =
    {
        /**
         * The signature to display in the header
         */
        signature: SIGNATURE,
        /**
         * The atoms that should be shown for this exact signature
         */
        symbols: PropTypes.arrayOf(SYMBOL)
    }

function loadDataForDetail(backendURL, uuid) {
    return fetch(`${backendURL("detail")}/${uuid}`).then(r => r.json())
}

function CloseButton(props) {
    const {onClick} = props;
    return <span style={{'cursor': 'pointer'}} onClick={onClick}><IoCloseSharp size={20}/></span>
}

CloseButton.propTypes =
    {
        /**
         * The function to be called when the button is clicked.
         */
        onClick: PropTypes.func
    }

export function Detail() {
    const [data, setData] = React.useState(null);
    const [type, setType] = React.useState("Model");
    const {backendURL} = useSettings();
    const backendURLRef = React.useRef(backendURL);
    const colorPalette = useColorPalette();
    const { shownDetail: shows, setShownDetail } = useShownDetail();
    const clearDetail = () => setShownDetail(null);

    React.useEffect(() => {
        let mounted = true;
        if (shows !== null) {
            loadDataForDetail(backendURLRef.current, shows)
                .then(items => {
                    if (mounted) {
                        setData(items[1])
                        setType(items[0])

                    }
                })
        }
        return () => { mounted = false };
    }, [shows])

    return <div id="detailSidebar" style={{ backgroundColor: colorPalette.info, color: colorPalette.dark}}
                className={shows === null ? `detail`:`detail detail-open`}>
        <h3><CloseButton onClick={clearDetail}/>{type}</h3>
        {data===null ? 
            <div>Loading..</div> :
            data.map((resp) =>
            <DetailForSignature key={`${resp[0].name}/${resp[0].args}`} signature={resp[0]} symbols={resp[1]}
                                uuid={shows}/>)}
    </div>
}

Detail.propTypes = {}
