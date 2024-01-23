import React from "react";
import './box.css'
import PropTypes from 'prop-types';
import {useColorPalette} from "../contexts/ColorPalette";
import {useSettings} from "../contexts/Settings";
import { useHighlightedNode } from "../contexts/HighlightedNode";


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
    const { backendURL } = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node)

    return <div className={classNames}
                style={{"backgroundColor": colorPalette.primary, "color": colorPalette.primary}}
                id={node}>
        <div style={{ "backgroundColor": colorPalette.primary, "color": colorPalette.primary }}>
            <img src={`${backendURL("graph/clingraph")}/${node}`} alt="Clingraph" /> 
        </div> 
    </div>
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: PropTypes.string,
}

