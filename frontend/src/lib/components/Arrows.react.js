import React from "react";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import { useShownRecursion } from "../contexts/ShownRecursion";
import Xarrow from "react-xarrows";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";

export function Arrows() {
    const [highlightedSymbol, ,] = useHighlightedSymbol();
    const [shownRecursion, , ] = useShownRecursion(); 
    // state to update Arrows after height animation of node
    const [value, , ,] = useAnimationUpdater();

    function calculateArrows() {
        return highlightedSymbol.map(arrow => {
            const suffix1 = `_${document.getElementById(arrow.src+"_main")?"main":"sub"}`;
            const suffix2 = `_${document.getElementById(arrow.tgt+"_main")?"main":"sub"}`;
            return <Xarrow
                key={arrow.src + suffix1 + "-" + arrow.tgt + suffix2} start={arrow.src+suffix1} end={arrow.tgt+suffix2} startAnchor={"top"} endAnchor={"bottom"} color={arrow.color} strokeWidth={2} headSize={5} zIndex={10} />
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
