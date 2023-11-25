import React, { useCallback } from "react";
import { Box } from "./Box.react";
import './boxrow.css';
import { useSettings } from "../contexts/Settings";

function loadClingraphChildren(backendURL) {
    return fetch(`${backendURL("clingraph/children")}`).then(r => r.json());
}

export function Boxrow() {
    const [graphics, setGraphics] = React.useState(null);
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] = React.useState(null);
    const boxrowRef = React.useRef(null);
    const { backendURL } = useSettings();
    const backendURLRef = React.useRef(backendURL);

    React.useEffect(() => {
        let mounted = true;
        loadClingraphChildren(backendURLRef.current)
            .then(items => {
                if (mounted) {
                    setGraphics(items)
                }
            })
        return () => { mounted = false };
    }, []);

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
        checkForOverflow()
    }, [checkForOverflow, graphics])

    React.useEffect(() => {
        window.addEventListener('resize', checkForOverflow)
        return _ => window.removeEventListener('resize', checkForOverflow)
    })

    return <div className="boxrow_container">
        {graphics === null ? <div>Loading Clingraph..</div> : <div ref={boxrowRef} className="boxrow_row">
            {graphics.map((child) => 
                <Box key={child} uuid={child} />)}</div>}
    </div>
}


Boxrow.propTypes = {};
