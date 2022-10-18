import PropTypes from "prop-types";

export const SYMBOL = PropTypes.exact({
    _type: PropTypes.oneOf(['Function']),
    arguments: PropTypes.array,
    name: PropTypes.string,
    positive: PropTypes.bool
})

export const SIGNATURE = PropTypes.exact({
    _type: PropTypes.oneOf(['Signature']),
    name: PropTypes.string,
    args: PropTypes.number
})
export const TRANSFORMATION = PropTypes.exact({
    _type: PropTypes.oneOf(['Transformation']),
    id: PropTypes.number,
    rules: PropTypes.array
})
export const NODE = PropTypes.exact({
    _type: PropTypes.oneOf(['Node']),
    atoms: PropTypes.array,
    diff: PropTypes.array,
    rule_nr: PropTypes.number,
    uuid: PropTypes.string
})
export const BOX = PropTypes.exact({
    _type: PropTypes.oneOf(['Box']),
    uuid: PropTypes.string
})
