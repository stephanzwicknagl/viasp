import PropTypes from "prop-types";

export const SYMBOL = PropTypes.exact({
    _type: PropTypes.oneOf(['Function']),
    arguments: PropTypes.array,
    name: PropTypes.string,
    positive: PropTypes.bool
})

export const SYMBOLIDENTIFIER = PropTypes.exact({
    _type: PropTypes.oneOf(['SymbolIdentifier']),
    symbol: SYMBOL,
    has_reason: PropTypes.bool,
    uuid: PropTypes.string
})

export const SIGNATURE = PropTypes.exact({
    _type: PropTypes.oneOf(['Signature']),
    name: PropTypes.string,
    args: PropTypes.number
})
export const RULECONTAINER = PropTypes.exact({
    _type: PropTypes.oneOf(['RuleContainer']),
    ast: PropTypes.arrayOf(PropTypes.string),
    str_: PropTypes.arrayOf(PropTypes.string)
})
export const TRANSFORMATION = PropTypes.exact({
    _type: PropTypes.oneOf(['Transformation']),
    id: PropTypes.number,
    rules: RULECONTAINER,
    adjacent_sort_indices: PropTypes.exact({
        lower_bound: PropTypes.number,
        upper_bound: PropTypes.number
    }),
    hash: PropTypes.string
})
export const TRANSFORMATIONWRAPPER = PropTypes.exact({
    transformation: TRANSFORMATION,
    shown: PropTypes.bool,
    isExpandableV: PropTypes.bool,
    isCollapsibleV: PropTypes.bool,
    allNodesShowMini: PropTypes.bool,
    hash: PropTypes.string,
})
export const GRAPH = PropTypes.exact({
    _type: PropTypes.oneOf(['Graph']),
    _graph: PropTypes.object
})
export const NODE = PropTypes.exact({
    _type: PropTypes.oneOf(['Node']),
    atoms: PropTypes.array,
    diff: PropTypes.array,
    rule_nr: PropTypes.number,
    reason: PropTypes.object, 
    recursive: PropTypes.oneOfType([PropTypes.bool, PropTypes.array]),
    space_multiplier: PropTypes.number,
    uuid: PropTypes.string,
    loading: PropTypes.bool,
    shownRecursion: PropTypes.bool,
    isExpandableV: PropTypes.bool,
    isCollapsibleV: PropTypes.bool,
    isExpandVAllTheWay: PropTypes.bool,
    showMini: PropTypes.bool,
})
export const CLINGRAPHNODE = PropTypes.exact({
    _type: PropTypes.oneOf(['ClingraphNode']),
    uuid: PropTypes.string,
    loading: PropTypes.bool,
    space_multiplier: PropTypes.number,
    showMini: PropTypes.bool,
});
export const BOX = PropTypes.exact({
    _type: PropTypes.oneOf(['Box']),
    uuid: PropTypes.string
})
export const COLORPALETTE = PropTypes.exact({
    primary: PropTypes.string,
    light: PropTypes.string,
    dark: PropTypes.string,
    warn: PropTypes.string,
    error: PropTypes.string,
    infoBackground: PropTypes.string,
    rowShading: PropTypes.arrayOf(PropTypes.string),
    explanationSuccess: PropTypes.string,
    explanationHighlights: PropTypes.arrayOf(PropTypes.string),
})
export const MAPZOOMSTATE = PropTypes.exact({
    scale: PropTypes.number,
    translation: PropTypes.shape({ x: PropTypes.number, y: PropTypes.number }),
})