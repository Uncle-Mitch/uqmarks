import type { AssessmentItem, GradeCutoff, GradeDetailsRow, TargetSummary } from "../types/home";

export function parseScore(value: string): number | null {
    if (!value) return null;
    const pct = /^([0-9]+(?:\.[0-9]+)?)%$/.exec(value);
    if (pct) return parseFloat(pct[1]);

    const fraction = /^([0-9]+(?:\.[0-9]+)?)\/([0-9]+(?:\.[0-9]+)?)$/.exec(value);
    if (fraction) {
        const num = parseFloat(fraction[1]);
        const denom = parseFloat(fraction[2]);
        if (denom !== 0) return (num / denom) * 100;
    }

    const numMatch = /^([0-9]+(?:\.[0-9]+)?)$/.exec(value);
    if (numMatch) return parseFloat(numMatch[1]);

    return null;
}

export function parseWeight(value: string) {
    const match = value.match(/^(\d+(\.\d+)?)%$/);
    if (!match) return null;
    return parseFloat(match[1]);
}

export function calculateTotalScore(items: AssessmentItem[]) {
    let weightedSum = 0;
    let totalWeight = 0;
    for (const item of items) {
        if (!item.enabled) continue;

        const score = parseScore(item.score);
        const weight = parseFloat(item.weight) / 100;
        if (score !== null && !Number.isNaN(weight)) {
            const cappedScore = Math.max(Math.min(score, 100), 0);
            weightedSum += cappedScore * weight;
            totalWeight += weight;
        }
    }
    return { score: parseFloat(weightedSum.toFixed(2)), totalWeight };
}

export function getEnabledWeight(items: AssessmentItem[]) {
    return items.filter((item) => item.enabled).reduce((sum, item) => sum + parseFloat(item.weight), 0);
}

export function isWeightValid(items: AssessmentItem[]) {
    return Math.round(getEnabledWeight(items)) === 100;
}

export function clampPercent(value: number) {
    if (Number.isNaN(value)) return 0;
    return Math.max(0, Math.min(100, parseFloat(value.toFixed(2))));
}

export function calculateImpossibleStart(items: AssessmentItem[]) {
    const { score, totalWeight } = calculateTotalScore(items);
    const remainingWeight = Math.max(1 - totalWeight, 0);
    return clampPercent(score + remainingWeight * 100);
}

// Rounding the course total makes each whole-number cutoff reachable half a point earlier.
export function getEffectiveCutoff(cutoff: number, roundFinalGrade = false) {
    return Math.max(0, cutoff - (roundFinalGrade ? 0.5 : 0));
}

export function getTargetSummary(
    items: AssessmentItem[],
    targetGrade: number,
    gradeCutoffs: GradeCutoff[],
    roundFinalGrade = false,
): TargetSummary {
    const { score, totalWeight } = calculateTotalScore(items);
    const gradeInfo = gradeCutoffs.find((info) => info.grade === targetGrade) ?? gradeCutoffs[0];
    const remainingWeight = Number.isNaN(totalWeight) ? 1 : Math.max(1 - totalWeight, 0);
    const requiredIncrease = Math.max(getEffectiveCutoff(gradeInfo.cutoff, roundFinalGrade) - score, 0);
    const achieved = requiredIncrease === 0;
    const obtainable = requiredIncrease <= remainingWeight * 100 + 1e-9;
    const requiredPercent = remainingWeight > 0 ? requiredIncrease / remainingWeight : achieved ? 0 : null;

    return {
        requiredPercent: requiredPercent === null ? null : Math.max(parseFloat(requiredPercent.toFixed(2)), 0),
        requiredScore:
            remainingWeight > 0
                ? `${requiredIncrease.toFixed(2)}/${parseFloat((remainingWeight * 100).toFixed(2))}`
                : "N/A",
        remainingWeight: parseFloat((remainingWeight * 100).toFixed(2)),
        achieved,
        obtainable,
        shortfall: parseFloat(requiredIncrease.toFixed(2)),
    };
}

export function getGradeDetailsRows(
    items: AssessmentItem[],
    gradeCutoffs: GradeCutoff[],
    roundFinalGrade = false,
): GradeDetailsRow[] {
    return gradeCutoffs.map((info) => {
        const summary = getTargetSummary(items, info.grade, gradeCutoffs, roundFinalGrade);
        return {
            key: info.grade,
            grade: info.grade,
            cutoff: getEffectiveCutoff(info.cutoff, roundFinalGrade),
            requiredPercent: summary.requiredPercent,
            requiredScore: summary.requiredScore,
            achieved: summary.achieved,
            obtainable: summary.obtainable,
        };
    });
}
