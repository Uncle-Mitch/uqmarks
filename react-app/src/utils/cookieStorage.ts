type CookieOptions = {
    days?: number;
    path?: string;
    sameSite?: "Lax" | "Strict" | "None";
    secure?: boolean;
};

const defaultOptions: CookieOptions = {
    days: 30,
    path: "/",
    sameSite: "Lax",
};

export function setCookie(name: string, value: string, options: CookieOptions = {}) {
    const resolved = { ...defaultOptions, ...options };
    const expires = resolved.days ? new Date(Date.now() + resolved.days * 864e5).toUTCString() : "";
    const parts = [`${name}=${encodeURIComponent(value)}`];
    if (expires) parts.push(`Expires=${expires}`);
    if (resolved.path) parts.push(`Path=${resolved.path}`);
    if (resolved.sameSite) parts.push(`SameSite=${resolved.sameSite}`);
    if (resolved.secure) parts.push("Secure");
    document.cookie = parts.join("; ");
}

export function getCookie(name: string) {
    const match = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
    if (!match) return null;
    return decodeURIComponent(match.split("=").slice(1).join("="));
}

export function deleteCookie(name: string) {
    document.cookie = `${name}=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/; SameSite=Lax`;
}

export function setJsonCookie<T>(name: string, value: T, options: CookieOptions = {}) {
    setCookie(name, JSON.stringify(value), options);
}

export function getJsonCookie<T>(name: string) {
    const raw = getCookie(name);
    if (!raw) return null;
    try {
        return JSON.parse(raw) as T;
    } catch {
        return null;
    }
}
