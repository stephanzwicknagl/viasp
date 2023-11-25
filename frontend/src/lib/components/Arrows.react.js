import React from "react";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import Xarrow from "react-xarrows";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import PropTypes from 'prop-types'

export function Arrows() {
    const { highlightedSymbol } = useHighlightedSymbol();
    const [shownRecursion, , ] = useShownRecursion(); 
    // state to update Arrows after height animation of node
    const [value, , ,] = useAnimationUpdater();

    function calculateArrows() {
        return highlightedSymbol.map(arrow => {
            const suffix1 = `_${document.getElementById(arrow.src+"_main")?"main":"sub"}`;
            const suffix2 = `_${document.getElementById(arrow.tgt+"_main")?"main":"sub"}`;
            return {"src": arrow.src + suffix1, "tgt": arrow.tgt + suffix2, "color": arrow.color};
        }).filter(arrow => {
            // filter false arrows that are not in the DOM
            return document.getElementById(arrow.src) && document.getElementById(arrow.tgt)
        }).map(arrow => {
            return <Xarrow
                key={arrow.src + "-" + arrow.tgt} start={arrow.src} end={arrow.tgt} startAnchor={"top"} endAnchor={"bottom"} color={arrow.color} strokeWidth={2} headSize={5} zIndex={10} />
        })
    }

    let arrows = calculateArrows();


    React.useEffect(() => {
        // arrows = [];
        arrows = calculateArrows();
        onFullyLoaded(() => {arrows = calculateArrows()});
    }, [ highlightedSymbol, shownRecursion ])

    function onFullyLoaded(callback) {
        setTimeout(function () {
            requestAnimationFrame(callback)
        })
    }
    return <div className="arrows_container">
        {arrows.length > 0 ? arrows : null}
    </div>
}

Arrows.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
