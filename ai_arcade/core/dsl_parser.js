function parseDSL(dslText) {
    const lines = dslText.split('\n');
    const config = {};
    for (let line of lines) {
        line = line.trim();
        if (!line || line.startsWith('#')) continue;
        const parts = line.split(':');
        if (parts.length < 2) continue;
        const key = parts[0].trim();
        const value = parts.slice(1).join(':').trim();
        config[key] = value;
    }
    return config;
}

window.parseDSL = parseDSL;
