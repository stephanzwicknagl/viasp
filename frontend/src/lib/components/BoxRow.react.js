import React from 'react';
import {MAPZOOMSTATE} from '../types/propTypes';
import * as Constants from '../constants';
import { useColorPalette } from '../contexts/ColorPalette';
import {Box} from './Box.react';
import './boxrow.css';
import {useTransformations} from '../contexts/transformations';

export function Boxrow(props) {
    const {transform} = props;
    const boxrowRef = React.useRef(null);
    const colorPalette = useColorPalette();
    const {
        state: {transformations, transformationDropIndices, clingraphGraphics},
    } = useTransformations();
    const [style, setStyle] = React.useState({
        opacity: 1.0,
        background: colorPalette.rowShading[(transformations.length + 1) % colorPalette.rowShading.length],
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
