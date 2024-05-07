import React, {useCallback} from 'react';
import PropTypes from 'prop-types';
import {MAPZOOMSTATE} from '../types/propTypes';
import * as Constants from '../constants';
import {Box} from './Box.react';
import './boxrow.css';
import {useTransformations} from '../contexts/transformations';
import debounce from 'lodash/debounce';
import useResizeObserver from '@react-hook/resize-observer';
import {useColorPalette} from '../contexts/ColorPalette';

export function Boxrow(props) {
    const {transform} = props;
    const [isOverflowH, setIsOverflowH] = React.useState(false);
    const [overflowBreakingPoint, setOverflowBreakingPoint] =
        React.useState(null);
    const boxrowRef = React.useRef(null);
    const {
        state: {transformationDropIndices, clingraphGraphics},
    } = useTransformations();
    const [style, setStyle] = React.useState({
        opacity: 1.0,
        });

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

    const branchSpaceRefs = React.useRef([]);
    React.useEffect(() => {
        branchSpaceRefs.current = clingraphGraphics.map(
            (_, i) => branchSpaceRefs.current[i] ?? React.createRef()
        );
    }, [clingraphGraphics]);

    return (
        <div className="row_container boxrow_container" style={style}>
            <div ref={boxrowRef} className="boxrow_row"
                style={{
                    width: `${clingraphGraphics.length === 1 ? 100 : transform.scale * 100}%`,
                    transform: `translateX(${clingraphGraphics.length === 1 ? 0 : transform.translation.x}px)`,
                }}>
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

Boxrow.propTypes = {
    transform: MAPZOOMSTATE
};
