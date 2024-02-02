import React, { useCallback } from "react";
import { Box } from "./Box.react";
import './boxrow.css';
import { useTransformations } from "../contexts/transformations";

export function Boxrow() {
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const boxrowRef = React.useRef(null);
    const {
        state: {currentDragged, clingraphGraphics},
    } = useTransformations();
    const [clingraphNodes, setClingraphNodes] = React.useState([]);
    const [style, setStyle] = React.useState({opacity: 1.0});
    const opacityMultiplier = 0.8;

    React.useEffect(() => {
        if (currentDragged.length > 0) {
            setStyle((prevStyle) => ({
                ...prevStyle,
                opacity: 1 - opacityMultiplier,
            }));
        } else {
            setStyle((prevStyle) => ({...prevStyle, opacity: 1.0}));
        }
    }, [currentDragged, opacityMultiplier]);


    const checkForOverflow = useCallback(() => {
        if (boxrowRef !== null && boxrowRef.current) {
            const e = boxrowRef.current
            const wouldOverflowNow = e.offsetWidth < e.scrollWidth;
            // We overflowed previously but not anymore
            if (overflowBreakingPoint <= e.offsetWidth) {
                setIsOverflowH(false);
            }
            if (!isOverflowH && wouldOverflowNow) {
                // We have to react to overflow now but want to remember when we'll not overflow anymore
                // on a resize
                setOverflowBreakingPoint(e.offsetWidth)
                setIsOverflowH(true)
            }
            // We never overflowed and also don't now
            if (overflowBreakingPoint === null && !wouldOverflowNow) {
                setIsOverflowH(false);
            }
        }
    }, [boxrowRef, isOverflowH, overflowBreakingPoint]);

    React.useEffect(() => {
        checkForOverflow();
    }, [checkForOverflow, clingraphGraphics]);

    React.useEffect(() => {
        if (clingraphGraphics.length > 0) {
            setClingraphNodes(clingraphGraphics);
        }
    }, [clingraphGraphics]);

    React.useEffect(() => {
        window.addEventListener('resize', checkForOverflow)
        return _ => window.removeEventListener('resize', checkForOverflow)
    })

    return (
        <div className="boxrow_container" style={style}>
            <div ref={boxrowRef} className="boxrow_row">
                {clingraphGraphics.map((child) => (
                    <Box key={child.uuid} node={child} />
                ))}
            </div>
        </div>
    );
}


Boxrow.propTypes = {};
