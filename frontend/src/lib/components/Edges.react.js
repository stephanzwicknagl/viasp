import React from "react";
import LineTo from "react-lineto";
import PropTypes from "prop-types";
import {useColorPalette} from "../contexts/ColorPalette";
import { useTransformations } from "../contexts/transformations";

export function Edges(props) {
    const colorPalete = useColorPalette();
    const { state: {edges} } = useTransformations();

    return <>
            {edges.map(link => {
                if (link.recursion === "in") {
                    return (
                        <LineTo
                            key={link.src + '-' + link.tgt}
                            from={link.src}
                            fromAnchor={'top center'}
                            toAnchor={'top center'}
                            to={link.tgt}
                            zIndex={1}
                            borderColor={colorPalete.dark}
                            borderStyle={link.style}
                            borderWidth={1}
                            delay={1000}
                            within={`row_container ${link.transformation}`}
                        />
                    );
                }
                if (link.recursion === "out") {
                    return (
                        <LineTo
                            key={link.src + '-' + link.tgt}
                            from={link.src}
                            fromAnchor={'bottom center'}
                            toAnchor={'bottom center'}
                            to={link.tgt}
                            zIndex={1}
                            borderColor={colorPalete.dark}
                            borderStyle={link.style}
                            borderWidth={1}
                            delay={1000}
                            within={`row_container ${link.transformation}`}
                        />
                    );
                }
                return (
                    <LineTo
                        key={link.src + '-' + link.tgt}
                        from={link.src}
                        fromAnchor={'bottom center'}
                        toAnchor={'top center'}
                        to={link.tgt}
                        zIndex={5}
                        borderColor={colorPalete.dark}
                        borderStyle={link.style}
                        borderWidth={1}
                        delay={1000}
                        within={`row_container ${link.transformation}`}
                        />
                );
                }
            )}
        </>
    }

        

Edges.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,
}
