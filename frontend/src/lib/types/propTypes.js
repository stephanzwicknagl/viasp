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
export const TRANSFORMATION = PropTypes.exact({
    _type: PropTypes.oneOf(['Transformation']),
    id: PropTypes.number,
    rules: PropTypes.array,
    hash: PropTypes.string
})
export const TRANSFORMATIONWRAPPER = PropTypes.exact({
    transformation: TRANSFORMATION,
    shown: PropTypes.bool,
    hash: PropTypes.string
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
    recursive: PropTypes.oneOfType([PropTypes.bool, GRAPH]),
    uuid: PropTypes.string
})
export const BOX = PropTypes.exact({
    _type: PropTypes.oneOf(['Box']),
    uuid: PropTypes.string
})
