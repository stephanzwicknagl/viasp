import React from "react";
import {make_atoms_string} from "../utils/index";
import './node.css'
import PropTypes from "prop-types";
import {hideNode, showNode, useShownNodes} from "../contexts/ShownNodes";
import {useColorPalette} from "../contexts/ColorPalette";
import {useHighlightedNode} from "../contexts/HighlightedNode";
import {useSettings} from "../contexts/Settings";
import {NODE, SYMBOL} from "../types/propTypes";
import {useFilters} from "../contexts/Filters";


function any(iterable) {
    for (let index = 0; index < iterable.length; index++) {
        if (iterable[index]) {
            return true;
        }
    }
    return false;
}

function Symbol(props) {
    const { symbol } = props;
    let atomString = make_atoms_string(symbol)
    atomString = atomString.length === 0 ? "" : atomString;
    return <div className={"symbol"}>{atomString}</div>
}

Symbol.propTypes = {
    /**
     * The symbol to display
     */
    symbol: SYMBOL
}

function NodeContent(props) {

    const {state} = useSettings();
    const {node, notifyClick, markedSymbols} = props;
    // no notify click in sub-node scope, because whole node is clickable atm
    const colorPalette = useColorPalette();
    const [{activeFilters},] = useFilters();
    const [markSymbol, setMarkSymbol] = React.useState(false);
    let contentToShow;
    if (state.show_all) {
        contentToShow = node.atoms;
    } else {
        contentToShow = node.diff;
    }

    function symbolShouldBeShown(symbol) {
        return activeFilters.length === 0 || any(activeFilters.filter(filter => filter._type === "Signature")
            .map(filter => filter.name === symbol.name && filter.args === symbol.arguments.length));
    }

    const classNames2 = `set_value`
    const containerNames = `set_container`
    
    const [marked, setMarked] = React.useState(null);
    React.useEffect(() => {
            // console.log("markedSymbols: ", markedSymbols)
            if (markedSymbols) {
                console.log("als string", markedSymbols.map(s => make_atoms_string(s)))
                setMarked(markedSymbols.map(s => make_atoms_string(s)))
            };
    }, [markedSymbols, node, state.show_all])
    const [renderedSymbols, setRenderedSymbols] = React.useState([])
    React.useEffect( () => {
        setRenderedSymbols(contentToShow.filter(symbol => 
                symbolShouldBeShown(symbol)).map(s => {
                    let atomString = make_atoms_string(s)
                    // console.log(atomString);
                    // console.log((atomString === "p(1)"));
                    // console.log("in check if marked of", marked)
                    if (marked) {
                        setMarkSymbol(marked.includes(atomString));
                    }
                    const classNames1 = `${(markSymbol) ? "mark mouse_over_shadow" : "mouse_over_shadow"}`;
                    const colorNames = (markSymbol) ?  {"background-color": colorPalette.warn.ten} : null;
                    return <div className={classNames1} style={colorNames}><Symbol key={JSON.stringify(s)} symbol={s} /></div>
        }))
    }, [marked, markSymbol, contentToShow, activeFilters, colorPalette, markedSymbols])
    return <div className={containerNames} style={{"color": colorPalette.thirty.bright}}>
        <span className={classNames2}>{renderedSymbols.length > 0 ? renderedSymbols : ""}</span>
    </div>
}

NodeContent.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * If the Node will overflow vertically
     */
    overflowV: PropTypes.bool
}

function useHighlightedNodeToCreateClassName(node) {
    const [highlightedNode,] = useHighlightedNode()
    let classNames = `node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`

    React.useEffect(() => {
            classNames = `node_border mouse_over_shadow ${node.uuid} ${highlightedNode === node.uuid ? "highlighted_node" : null}`
        }, [node.uuid, highlightedNode]
    )
    return classNames
}

export function Node(props) {
    const {node, notifyClick, showMini, markedSymbols} = props;
    const [isOverflowV, setIsOverflowV] = React.useState(false);
    const colorPalette = useColorPalette();
    const [, dispatch] = useShownNodes()
    const {state} = useSettings();
    const classNames = useHighlightedNodeToCreateClassName(node)


    const ref = React.useCallback(x => {
        if (x !== null) {
            setIsOverflowV(x.scrollHeight > x.offsetHeight + 2);
        }
    }, [state]);
    React.useEffect(() => {
        dispatch(showNode(node.uuid))
        return () => {
            dispatch(hideNode(node.uuid))
        }
    }, [])
    React.useEffect(() => {

    })

    // const imageToShow = node.clingraph ? node.clingraph : "https://www.w3schools.com/html/img_girl.jpg";

    return <div className={classNames}
                style={{"backgroundColor": colorPalette.sixty.dark, "color": colorPalette.ten.dark}}
                id={node.uuid} onClick={() => notifyClick(node)}>
        {showMini ? <div style={{"backgroundColor": colorPalette.ten.dark, "color": colorPalette.ten.dark}}
                         className={"mini"}/> :
            <div className={"set_too_high"} ref={ref}><NodeContent node={node} notifyClick={notifyClick} markedSymbols={markedSymbols}/></div>}
        {!showMini && isOverflowV ?
            <div style={{"backgroundColor": colorPalette.ten.dark, "color": colorPalette.sixty.dark}}
                 className={"noselect bauchbinde"}>...</div> : null}
    </div>
}

Node.propTypes = {
    /**
     * object containing the node data to be displayed
     */
    node: NODE,
    /**
     * The function to be called if the facts are clicked on
     */
    notifyClick: PropTypes.func,
    /**
     * If true, shows the minified node without displaying its symbols
     */
    showMini: PropTypes.bool,
}

