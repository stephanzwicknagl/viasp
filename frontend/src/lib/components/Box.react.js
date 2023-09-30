import React from "react";
import './box.css'
import {useColorPalette} from "../contexts/ColorPalette";
import {useSettings} from "../contexts/Settings";
import {BOX} from "../types/propTypes";
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
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}
                id={node}>
        <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}>
            <img src={`${backendURL("graph/clingraph")}/${node}`} alt="Clingraph" /> 
        </div> 
    </div>
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    box: BOX,
}

