export function setWith1DayExpiry(key: string, value: any) {
    const ms = 24 * 60 * 60 * 1000;
    const now = Date.now();
    const item = {
        value,
        expiry: now + ms,
    };
    localStorage.setItem(key, JSON.stringify(item));
}

export function getWith1DayExpiry(key: string) {
    const itemStr = localStorage.getItem(key);
    if (!itemStr) return null;
    try {
        const item = JSON.parse(itemStr);
        if (!item.expiry || Date.now() > item.expiry) {
            localStorage.removeItem(key);
            return null;
        }
        return item.value;
    } catch {
        localStorage.removeItem(key);
        return null;
    }
}
