import {v4 as uuidv4} from 'uuid';

export function make_atoms_string(atoms) {
    if (Array.isArray(atoms)) {
        return atoms.map(make_atoms_string).join(' ');
    }
    switch (atoms._type) {
        case 'Number':
            return atoms.number.toString();
        case 'Function': {
            const args = atoms.arguments.map(make_atoms_string).join(',');
            return args.length > 0 ? `${atoms.name}(${args})` : `${atoms.name}`;
        }
        case 'SymbolIdentifier':
            return make_atoms_string(atoms.symbol);
        case 'String':
            return `"${atoms.string}"`;
        default:
            throw new TypeError(`Unimplemented type ${atoms._type}`);
    }
}

export function make_rules_string(rule) {
    // TODO: This is pretty bad. Adjust types for this.
    return rule.join(' ');
}


export function make_default_nodes(oldNodes = []) {
    if (oldNodes.length > 0) {
        return oldNodes.map((node, i) => {
            return {
                ...node,
                loading: true,
            };
        });
    }

    const nodeSymbolUpperBound = 20;
    const nodes = [];
    const count = Math.floor(Math.random() * 2) + 1;
    const symbolCount = Math.floor(Math.random() * nodeSymbolUpperBound) + 3;
    for (let i = 0; i < count; i++) {
        const diff = Array.from({length: symbolCount}, (_, i) => {
            return {
                _type: 'SymbolIdentifier',
                symbol: {
                    _type: 'Function',
                    arguments: [],
                    name: `a(${i})`,
                    positive: true,
                },
                has_reason: false,
                uuid: `${uuidv4()}-loading-${i}`,
            };
        });
        nodes.push({
            _type: 'Node',
            recursive: false,
            uuid: `${uuidv4()}-loading-${i}`,
            atoms: diff,
            diff: diff,
            rule_nr: 0,
            reason: {},
            space_multiplier: 0.5,
            loading: true,
        });
    }
    return nodes;
}

export function make_default_clingraph_nodes(oldNodes = []) {
    if (oldNodes.length > 0) {
        return oldNodes.map((node, i) => {
            return {
                ...node,
                uuid: `${node.uuid}`,
                loading: true,
            };
        });
    }

    const nodes = [];
    const count = Math.floor(Math.random() * 2) + 1;
    for (let i = 0; i < count; i++) {
        nodes.push({
            _type: 'ClingraphNode',
            uuid: `${uuidv4()}-loading-${i}`,
            loading: true,
        });
    }
    return nodes;
}

export function findChildByClass(element, className) {
    if (element.classList.contains(className)) {
        return element;
    }

    for (const child of element.children) {
        const found = findChildByClass(child, className);
        if (found) {
            return found;
        }
    }

    return null;
}

export function emToPixel(em) {
    return em * parseFloat(getComputedStyle(document.documentElement).fontSize);
}