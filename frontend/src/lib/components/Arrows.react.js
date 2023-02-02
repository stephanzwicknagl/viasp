import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import Xarrow from "react-xarrows";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";

export function Arrows() {
    const [highlightedSymbol, ,] = useHighlightedSymbol();
    // state to update Arrows after height animation of node
    const [value, , ,] = useAnimationUpdater();

    return <div className="arrows_container">
        {highlightedSymbol.filter(arrow => document.getElementById(arrow.src) && document.getElementById(arrow.tgt)).map(arrow => {
            return <Xarrow
                key={arrow.src + "-" + arrow.tgt} start={arrow.src} end={arrow.tgt} startAnchor={"top"} endAnchor={"bottom"} color={arrow.color} strokeWidth={2} headSize={5} zIndex={10} />
        })}
    </div>
}

Arrows.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
