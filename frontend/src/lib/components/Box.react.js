import React from "react";
import './box.css'
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import {useSettings} from "../contexts/Settings";
import {BOX} from "../types/propTypes";
import {useEffect, useState} from "react";
import { useHighlightedNode } from "../contexts/HighlightedNode";


function loadImage(id, backendURL) {
    return fetch(`${backendURL("graph/clingraph")}/${id}`).then(r => {
        if (r.ok) {
            console.log("in load Image:", r.body)
            return r.json()
        }
        throw new Error(r.statusText);
    });
}

function useHighlightedNodeToCreateClassName(node) {
    console.log("in useHighlightedNodeToCreateClassName")
    // const [highlightedBox,] = useHighlightedNode()
    let classNames = `box_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_box" : null}`

    React.useEffect(() => {
        classNames = `box_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_box" : null}`
    }, [node.uuid, node.uuid]
    )
    return classNames
}


export function Box(props) {
    const {node} = props;
    const colorPalette = useColorPalette();
    const [imageToShow, setImageURL] = React.useState(null) 
    const { backendURL } = useSettings();
    // const classNames = useHighlightedNodeToCreateClassName(node)

    React.useEffect(() => {
        let mounted = true;
        loadImage(node.uuid, backendURL)
            .then(data => {
                if (mounted) {
                    setImageURL(data)
                }
            });
        return () => mounted = false;
    }, []);
    console.log(imageToShow);
    if (imageToShow) {
        console.log("Have loaded the image");
    }	
    else {
        console.log("Image could not be loaded");
    }


    return <div className="box_box"
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}>
        <div style={{ "backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark }}>
            <img src={imageToShow} alt="Clingraph visualization could not be loaded" /> 
        </div> 
    </div>
}

Box.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    box: BOX,
}

