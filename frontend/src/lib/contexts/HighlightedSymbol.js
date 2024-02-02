import React from "react";
import PropTypes from "prop-types";
import { useSettings } from "./Settings";
import { useColorPalette } from "../contexts/ColorPalette";
import { useMessages, showError } from "./UserMessages";
import { useFilters } from "../contexts/Filters";
import { useShownRecursion } from "../contexts/ShownRecursion";
import {useTransformations} from '../contexts/transformations';

function fetchReasonOf(backendURL, sourceId, nodeId) {
    return fetch(`${backendURL("graph/reason")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({"sourceid": sourceId, "nodeid": nodeId})
    }).then(r => {
        if (!r.ok) {
            throw new Error(`${r.status} ${r.statusText}`);
        }
        return r.json()
    });
}
const defaultHighlightedSymbol = [];

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);
    const highlightedSymbolRef = React.useRef(highlightedSymbol);
    const colorPalette = useColorPalette();
    const [, message_dispatch] = useMessages()
    const messageDispatchRef = React.useRef(message_dispatch);
    const [shownRecursion, ,] = useShownRecursion();
    const [{activeFilters}] = useFilters();
    const {
        state: {transformations},
    } = useTransformations();


    const {backendURL} = useSettings();
    const backendUrlRef = React.useRef(backendURL);

    const getNextColor = React.useCallback(
        (l, arrowsColors) => {
            const colorArray = Object.values(
                colorPalette.explanationHighlights
            );
            var c = JSON.stringify(colorArray[l % colorArray.length]);
            if (arrowsColors.indexOf(c) === -1 || l >= colorArray.length) {
                return c;
            }
            return getNextColor(l + 1, arrowsColors);
        },
        [colorPalette.explanationHighlights]
    );

    const toggleHighlightedSymbol = React.useCallback(
        (arrows, currentHighlightedSymbol) => {
            var arrowsSrcTgt = [];
            var arrowsColors = [];
            currentHighlightedSymbol.forEach((item) => {
                arrowsSrcTgt.push(
                    JSON.stringify({
                        src: item.src,
                        tgt: item.tgt,
                        srcNode: item.srcNode,
                    })
                );
                arrowsColors.push(JSON.stringify(item.color));
            });
            const c = getNextColor(
                new Set(currentHighlightedSymbol.map((item) => item.src)).size,
                arrowsColors
            );

            arrows.forEach((a) => {
                var value = JSON.stringify(a);
                var index = arrowsSrcTgt.indexOf(value);
                if (index === -1) {
                    arrowsSrcTgt.push(JSON.stringify(a));
                    arrowsColors.push(c);
                } else {
                    arrowsSrcTgt.splice(index, 1);
                    arrowsColors.splice(index, 1);
                }
            });
            setHighlightedSymbol(
                arrowsSrcTgt.map((item, i) => {
                    var obj = JSON.parse(item);
                    obj.color = JSON.parse(arrowsColors[i]);
                    return obj;
                })
            );
        },
        [setHighlightedSymbol, getNextColor]
    );

    const toggleReasonOf = React.useCallback((sourceid, nodeId, currentHighlightedSymbol) => {
        fetchReasonOf(backendUrlRef.current, sourceid, nodeId).then(reasons => {
            if (reasons.every(tgt => tgt !== null)) {
                toggleHighlightedSymbol(reasons, currentHighlightedSymbol);
            }})
            .catch((error) => {
                messageDispatchRef.current(
                    showError(`Failed to get reason: ${error}`)
                )
            });
    }, [messageDispatchRef, toggleHighlightedSymbol]);

    // const reloadHighlightedSymbol = React.useCallback(
    //     (currentHighlightedSymbol) => {
    //         const reasonsOf = [];
    //         highlightedSymbolRef.current.forEach((item) => {
    //             if (reasonsOf.map((r) => r.src).includes(item.src)) {
    //                 reasonsOf.push({src: item.src, srcNode: item.srcNode});
    //             }
    //         });
    //         setHighlightedSymbol([]);

    //         reasonsOf.forEach((item) => {
    //             toggleReasonOf(
    //                 item.src,
    //                 item.srcNode,
    //                 currentHighlightedSymbol
    //             );
    //         });
    //     },
    //     [setHighlightedSymbol, toggleReasonOf]
    // );

    // React.useEffect(
    //     () => {
    //         console.log('reloadHighlightedSymbol dependency changed');

    //         reloadHighlightedSymbol(highlightedSymbolRef.current);
    //     },
    //     [
    //         reloadHighlightedSymbol,
    //         shownRecursion,
    //         activeFilters,
    //         transformations,
    //     ]
    // );



    return <HighlightedSymbolContext.Provider
        value={{highlightedSymbol, toggleHighlightedSymbol, setHighlightedSymbol, toggleReasonOf}}>{children}</HighlightedSymbolContext.Provider>
}

HighlightedSymbolProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
