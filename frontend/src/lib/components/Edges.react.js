import React from "react";
import LineTo from "react-lineto";
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import { useClingraph } from "../contexts/Clingraph";
import { useEdges } from "../contexts/Edges";

export function Edges() {
    const colorPalete = useColorPalette();
    const {clingraphUsed} = useClingraph();
    const { edges, clingraphEdges } = useEdges();

    const [value, , , ] = useAnimationUpdater();

    return <div className="edge_container" >
            {edges.map(link => 
            <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={5} borderColor={colorPalete.seventy.dark} borderStyle={"solid"} borderWidth={1} />)}
            {!clingraphUsed ? null:
            clingraphEdges.map(link => 
            <LineTo
                key={link.src + "-" + link.tgt} from={link.src} fromAnchor={"bottom center"} toAnchor={"top center"}
                to={link.tgt} zIndex={5} borderColor={colorPalete.seventy.bright} borderStyle={"dashed"} borderWidth={2} />)}
        </div>
}

Edges.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
