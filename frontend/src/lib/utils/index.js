export function make_atoms_string(atoms) {
    // console.log(`IN: ${JSON.stringify(atoms)}`)
    if (Array.isArray(atoms)) {
        // console.log(`An array ${atoms}`)
        return atoms.map(make_atoms_string).join(" ")
    }
    switch (atoms._type) {
        case "Number":
            return atoms.number.toString();
        case "Function": {
            const args = atoms.arguments.map(make_atoms_string).join(",")
            return args.length > 0 ? `${atoms.name}(${args})` : `${atoms.name}`
        }
        case "SymbolIdentifier":
            return make_atoms_string(atoms.symbol)
        default:
            throw new TypeError(`Unimplemented type ${atoms._type}`)

    }
}

export function make_rules_string(rule) {
    // TODO: This is pretty bad. Adjust types for this.
    return rule.join(" ")
}

export async function computeSortHash(hashes) {
    const hash_str = hashes.join("");
    const hash_len = 16;
    const hash = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(hash_str));
    return Array.from(new Uint8Array(hash)).map(b => b.toString(hash_len).padStart(2, '0')).join('');
}

export function make_default_nodes(oldNodes = []) {
    if (oldNodes.length > 0) {
        return oldNodes.map((node, i) => {
            return {
                ...node,
                uuid: `${node.uuid}-loading-${i}`,
            }
        });
    }
    
    const nodes = [];
    const count = Math.floor(Math.random() * 2) + 1;
    const symbolCount = Math.floor(Math.random() * 20) + 3; 
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
                uuid: `loading-${i}`,
            };
        });
        nodes.push({
            _type: 'Node',
            recursive: false,
            uuid: `loading-${i}`,
            atoms: diff,
            diff: diff,
            rule_nr: 0,
            reason: {},
            space_multiplier: 0.5,
        });
    }
    return nodes;
}