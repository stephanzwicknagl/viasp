import React from "react";
import PropTypes from "prop-types";
import { useSettings } from "./Settings";
import { useColorPalette } from "../contexts/ColorPalette";

function fetchReasonOf(backendURL, sourceId, nodeId) {
    return fetch(`${backendURL("graph/reason")}`, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({"sourceid": sourceId, "nodeid": nodeId})
    }).then(r => {
        if (r.ok) {
            return r.json()
        }
        throw new Error(r.statusText);
    });
}
const defaultHighlightedSymbol = [];

const HighlightedSymbolContext = React.createContext(defaultHighlightedSymbol);

export const useHighlightedSymbol = () => React.useContext(HighlightedSymbolContext);
export const HighlightedSymbolProvider = ({ children }) => {
    const [highlightedSymbol, setHighlightedSymbol] = React.useState(defaultHighlightedSymbol);
    const colorPalette = useColorPalette();
    const colorArray = Object.values(colorPalette.highlight);
    const { backendURL } = useSettings();
    const backendUrlRef = React.useRef(backendURL);

    function getNextColor(l, arrowsColors){
        var c = JSON.stringify(colorArray[l % colorArray.length])
        if (arrowsColors.indexOf(c) === -1 || l >= colorArray.length){
            return c
        }
        return getNextColor(l+1, arrowsColors)
    }

    function toggleHighlightedSymbol(arrows) {
        var arrowsSrcTgt = [];
        var arrowsColors = [];
        highlightedSymbol.forEach(item => {
            arrowsSrcTgt.push(JSON.stringify({"src":item.src, "tgt":item.tgt}));
            arrowsColors.push(JSON.stringify(item.color));
        })
        const c = getNextColor(new Set(highlightedSymbol.map(item => item.src)).size, arrowsColors);

        arrows.forEach(a => {
            var value = JSON.stringify(a);
            var index = arrowsSrcTgt.indexOf(value);

            if (index === -1) {
                arrowsSrcTgt.push(JSON.stringify(a));
                arrowsColors.push(c);
            } else {
                arrowsSrcTgt.splice(index, 1);
                arrowsColors.splice(index, 1);
                // call update height
            }
        })
        setHighlightedSymbol(
            arrowsSrcTgt.map((item, i) => {
                var obj = JSON.parse(item);
                obj.color = JSON.parse(arrowsColors[i]);
                return obj;
        }));
    };

    function toggleReasonOf(sourceid, nodeId) {
        fetchReasonOf(backendUrlRef.current, sourceid, nodeId).then(reasons => {
            if (reasons.every(tgt => tgt !== null)) {
                toggleHighlightedSymbol(reasons);
            }
            // TODO: Not sure if we need this
            // else {
            //     const subNode = node.recursive._graph.nodes.filter(node => node.id.atoms.filter(atom => atom.uuid === src.uuid).length > 0);
            //     reasons = subNode[0].id.reason[make_atoms_string(src.symbol)];
            //     toggleShownRecursion(node.uuid);
            //     toggleHighlightedSymbol(reasons.map(tgt => { return { "src": src.uuid, "tgt": tgt.uuid } }), highlightedSymbol);
            // }
            })
    }



    return <HighlightedSymbolContext.Provider
        value={{highlightedSymbol, toggleHighlightedSymbol, setHighlightedSymbol, toggleReasonOf}}>{children}</HighlightedSymbolContext.Provider>
}

HighlightedSymbolProvider.propTypes = {
    /**
     * The subtree that requires access to this context.
     */
    children: PropTypes.element,
}
