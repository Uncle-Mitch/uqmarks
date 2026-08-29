import { deleteCookie, getJsonCookie } from "./cookieStorage";
import type { StoredCard } from "../types/home";

const COURSE_CARDS_STORAGE_KEY = "uqm_course_cards";
const LEGACY_COURSE_CARDS_COOKIE = "uqm_course_cards";

export type StoredCourseCards = {
    cards: StoredCard[];
};

function isStoredCourseCards(value: unknown): value is StoredCourseCards {
    return !!value && typeof value === "object" && Array.isArray((value as StoredCourseCards).cards);
}

export function saveCourseCards(cards: StoredCourseCards): boolean {
    try {
        localStorage.setItem(COURSE_CARDS_STORAGE_KEY, JSON.stringify(cards));
        return true;
    } catch {
        return false;
    }
}

export function getStoredCourseCards(): StoredCourseCards | null {
    try {
        const stored = localStorage.getItem(COURSE_CARDS_STORAGE_KEY);
        if (stored) {
            const parsed: unknown = JSON.parse(stored);
            if (isStoredCourseCards(parsed)) return parsed;
            localStorage.removeItem(COURSE_CARDS_STORAGE_KEY);
        }
    } catch {
        try {
            localStorage.removeItem(COURSE_CARDS_STORAGE_KEY);
        } catch {
            // Ignore (localStorage may be unavailable).
        }
        // Continue to the legacy cookie migration when localStorage is unavailable or corrupt.
    }

    const legacyStored = getJsonCookie<StoredCourseCards>(LEGACY_COURSE_CARDS_COOKIE);
    if (!legacyStored || !isStoredCourseCards(legacyStored)) return null;

    if (saveCourseCards(legacyStored)) {
        deleteCookie(LEGACY_COURSE_CARDS_COOKIE);
    }
    return legacyStored;
}
