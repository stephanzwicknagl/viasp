import React from "react";
import './box.css'
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import {useSettings} from "../contexts/Settings";
import {BOX} from "../types/propTypes";
import { useHighlightedNode } from "../contexts/HighlightedNode";


function loadImage(id, backendURL) {
    return fetch(`${backendURL("graph/clingraph")}/${id}`).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

function useHighlightedNodeToCreateClassName(node) {
    const [highlightedBox,] = useHighlightedNode()
    let classNames = `box_border mouse_over_shadow ${node} ${highlightedBox === node ? "highlighted_box" : null}`

    React.useEffect(() => {
        classNames = `box_border mouse_over_shadow ${node} ${highlightedBox === node ? "highlighted_box" : null}`
    }, [node, node]
    )
    return classNames
}


export function Box(props) {
    const {node} = props;
    const colorPalette = useColorPalette();
    const [imageToShow, setImageURL] = React.useState(null) 
    const { backendURL } = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node)

    React.useEffect(() => {
        let mounted = true;
        loadImage(node, backendURL)
            .then(data => {
                if (mounted) {
                    setImageURL(data)
                }
            });
        return () => mounted = false;
    }, []);

    return <div className={classNames}
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}
                id={node}>
        <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}>
            <img src={imageToShow} alt="Clingraph" /> 
        </div> 
    </div>
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    box: BOX,
}

