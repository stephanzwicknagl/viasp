import React from "react";
import { useHighlightedSymbol } from "../contexts/HighlightedSymbol";
import Xarrow from "react-xarrows";
import { useAnimationUpdater } from "../contexts/AnimationUpdater";
import PropTypes from 'prop-types'
import { v4 as uuidv4 } from 'uuid';


export function Arrows() {
    const {highlightedSymbol} = useHighlightedSymbol();
    const [arrows, setArrows] = React.useState([]);
    const {animationState} = useAnimationUpdater();

    const calculateArrows = React.useCallback(() => {
        return highlightedSymbol
            .map((arrow) => {
                const suffix1 = `_${
                    document.getElementById(arrow.src + '_main')
                        ? 'main'
                        : 'sub'
                }`;
                const suffix2 = `_${
                    document.getElementById(arrow.tgt + '_main')
                        ? 'main'
                        : 'sub'
                }`;
                return {
                    src: arrow.src + suffix1,
                    tgt: arrow.tgt + suffix2,
                    color: arrow.color,
                };
            })
            .filter((arrow) => {
                // filter false arrows that are not in the DOM
                return (
                    document.getElementById(arrow.src) &&
                    document.getElementById(arrow.tgt)
                );
            })
            .map((arrow) => {
                return (
                    <Xarrow
                        key={uuidv4()}
                        start={arrow.src}
                        end={arrow.tgt}
                        startAnchor={'auto'}
                        endAnchor={'auto'}
                        color={arrow.color}
                        strokeWidth={2}
                        headSize={5}
                        zIndex={10}
                    />
                );
            });
    }, [highlightedSymbol]);

    React.useEffect(() => {
        setArrows(calculateArrows());
    }, [animationState, highlightedSymbol, calculateArrows]);

    return (
        <div className="arrows_container">
            {arrows.length > 0 ? arrows : null}
        </div>
    );
}

Arrows.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
