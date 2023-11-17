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

export async function computeSortHash(transformations) {
    if (transformations.length === 0) {
        return ""
    }
    const encoder = new TextEncoder();

    // Create an array of promises
    const hashPromises = transformations.map(transformation => {
        // Convert transformation.rules to a string
        const transformationStr = JSON.stringify(transformation.transformation).replace(/\s+/g, '');
        // Return a promise that resolves to the hash of the transformation
        return window.crypto.subtle.digest('SHA-256', encoder.encode(transformationStr));
    });
    
    // Wait for all promises to resolve
    const hashes = await Promise.all(hashPromises);

    // Concatenate all hashes
    const concatenated = new Uint8Array(hashes.reduce((acc, hash) => acc + hash.byteLength, 0));
    let offset = 0;
    for (const hash of hashes) {
        concatenated.set(new Uint8Array(hash), offset);
        offset += hash.byteLength;
    }

    // Compute the final hash
    const finalHash = await window.crypto.subtle.digest('SHA-256', concatenated);

    // Convert the final hash to a hexadecimal string
    const hashHex = Array.from(new Uint8Array(finalHash)).map(b => b.toString(16).padStart(2, '0')).join('');
    console.log("Calculated Hash:", hashHex);
    return hashHex;
}