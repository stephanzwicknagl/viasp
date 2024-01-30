import React from "react";
import LineTo from "react-lineto";
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import { useEdges } from "../contexts/Edges";


export function Edges(props) {
    const colorPalete = useColorPalette();
    const { edges } = useEdges();
    const [value, , ,] = useAnimationUpdater();


    return <div className="edge_container">
            {edges.map(link => {
                if (link.recursion === "in") {
                    return <LineTo
                    key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"top center"} toAnchor={"top center"}
                    to={link.tgt} zIndex={8} borderColor={colorPalete.dark} borderStyle={link.style} borderWidth={1} />
                } else if (link.recursion === "out") {
                    return <LineTo
                    key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"bottom center"}
                    to={link.tgt} zIndex={8} borderColor={colorPalete.dark} borderStyle={link.style} borderWidth={1} />
                }
                return <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={8} borderColor={colorPalete.dark} borderStyle={link.style} borderWidth={1} />
                }
            )}
        </div>
    }

        

Edges.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
