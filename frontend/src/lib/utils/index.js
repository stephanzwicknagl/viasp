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
    const hash = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(hash_str));
    return Array.from(new Uint8Array(hash)).map(b => b.toString(16).padStart(2, '0')).join('');
}
