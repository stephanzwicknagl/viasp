import React, {useCallback} from 'react';
import * as Constants from '../constants';
import {Box} from './Box.react';
import './boxrow.css';
import {useTransformations} from '../contexts/transformations';
import debounce from 'lodash/debounce';
import useResizeObserver from '@react-hook/resize-observer';
import {useColorPalette} from '../contexts/ColorPalette';

export function Boxrow() {
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const boxrowRef = React.useRef(null);
    const {
        state: {transformationDropIndices, clingraphGraphics},
    } = useTransformations();
    const [style, setStyle] = React.useState({opacity: 1.0});

    React.useEffect(() => {
        if (transformationDropIndices !== null) {
            setStyle((prevStyle) => ({
                ...prevStyle,
                opacity: 1 - Constants.opacityMultiplier,
            }));
        } else {
            setStyle((prevStyle) => ({...prevStyle, opacity: 1.0}));
        }
    }, [transformationDropIndices]);

    // const checkForOverflow = useCallback(() => {
    //     if (boxrowRef !== null && boxrowRef.current) {
    //         const e = boxrowRef.current;
    //         const wouldOverflowNow = e.offsetWidth < e.scrollWidth;
    //         // We overflowed previously but not anymore
    //         if (overflowBreakingPoint <= e.offsetWidth) {
    //             setIsOverflowH(false);
    //         }
    //         if (!isOverflowH && wouldOverflowNow) {
    //             // We have to react to overflow now but want to remember when we'll not overflow anymore
    //             // on a resize
    //             setOverflowBreakingPoint(e.offsetWidth);
    //             setIsOverflowH(true);
    //         }
    //         // We never overflowed and also don't now
    //         if (overflowBreakingPoint === null && !wouldOverflowNow) {
    //             setIsOverflowH(false);
    //         }
    //     }
    // }, [boxrowRef, isOverflowH, overflowBreakingPoint]);

    // const debouncedCheckForOverflow = React.useMemo(() => {
    //     return debounce(checkForOverflow, Constants.DEBOUNCETIMEOUT);
    // }, [checkForOverflow]);

    // React.useEffect(() => {
    //     checkForOverflow();
    // }, [checkForOverflow, clingraphGraphics]);

    // useResizeObserver(
    //     document.getElementById('content'),
    //     debouncedCheckForOverflow
    // );

    const branchSpaceRefs = React.useRef([]);
    React.useEffect(() => {
        branchSpaceRefs.current = clingraphGraphics.map(
            (_, i) => branchSpaceRefs.current[i] ?? React.createRef()
        );
    }, [clingraphGraphics]);

    return (
        <div className="row_container boxrow_container" style={style}>
            <div ref={boxrowRef} className="boxrow_row">
                {clingraphGraphics.map((child, index) => {
                    const space_multiplier = child.space_multiplier * 100;

                    return (
                        <div
                            className="branch_space"
                            key={child.uuid}
                            style={{flex: `0 0 ${space_multiplier}%`}}
                            ref={branchSpaceRefs.current[index]}
                        >
                            <Box
                                key={child.uuid}
                                node={child}
                                branchSpace={branchSpaceRefs.current[index]}
                            />
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

Boxrow.propTypes = {};
