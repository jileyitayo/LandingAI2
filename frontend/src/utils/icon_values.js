import * as LucideReact from 'lucide-react';
import fs from 'fs';

const icons = Object.keys(LucideReact).filter(key => {
    // Filter to only icon components (start with uppercase)
    return key[0] === key[0].toUpperCase() && key[0] !== key[0].toLowerCase();
});

fs.writeFileSync('valid_lucide_icons.json', JSON.stringify(icons, null, 2));
console.log(`Extracted ${icons.length} icons`);
