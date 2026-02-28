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

export function getTargetSummary(
    items: AssessmentItem[],
    targetGrade: number,
    gradeCutoffs: GradeCutoff[],
): TargetSummary {
    const { score, totalWeight } = calculateTotalScore(items);
    const gradeInfo = gradeCutoffs.find((info) => info.grade === targetGrade) ?? gradeCutoffs[0];
    const remainingWeight = Number.isNaN(totalWeight) ? 1 : Math.max(1 - totalWeight, 0);
    const requiredIncrease = Math.max(gradeInfo.cutoff - score, 0);
    const requiredPercent = remainingWeight > 0 ? requiredIncrease / remainingWeight : 0;

    return {
        requiredPercent: Math.max(parseFloat(requiredPercent.toFixed(2)), 0),
        requiredScore: `${requiredIncrease.toFixed(2)}/${Math.round(remainingWeight * 100)}`,
        remainingWeight: Math.round(remainingWeight * 100),
    };
}

export function getGradeDetailsRows(items: AssessmentItem[], gradeCutoffs: GradeCutoff[]): GradeDetailsRow[] {
    const { score, totalWeight } = calculateTotalScore(items);
    const remainingWeight = Number.isNaN(totalWeight) ? 1 : Math.max(1 - totalWeight, 0);

    return gradeCutoffs.map((info) => {
        const requiredIncrease = info.cutoff - score;
        const requiredIncreaseCapped = Math.max(requiredIncrease, 0);
        const requiredPercent = remainingWeight > 0 ? requiredIncreaseCapped / remainingWeight : 0;
        const obtainable = remainingWeight > 0 && requiredIncrease <= remainingWeight * 100;
        const fmt = (value: number) => (value === 0 ? "0" : parseFloat(value.toFixed(2)).toString());

        return {
            key: info.grade,
            grade: info.grade,
            cutoff: info.cutoff,
            requiredPercent: Math.max(parseFloat(requiredPercent.toFixed(2)), 0),
            requiredScore: `${fmt(requiredIncreaseCapped)}/${Math.round(remainingWeight * 100)}`,
            achieved: score >= info.cutoff,
            obtainable,
        };
    });
}
