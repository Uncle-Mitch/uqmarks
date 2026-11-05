import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import ts from "typescript";

const source = await readFile(new URL("./courseCardCalculations.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext } });
const { getTargetSummary, getGradeDetailsRows } = await import(
    `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);
const cutoffs = [
    { grade: 1, cutoff: 0 },
    { grade: 5, cutoff: 65 },
    { grade: 7, cutoff: 85 },
];
const item = (score, weight = "100%") => ({
    key: 0,
    assessment: "Exam",
    score,
    weight,
    enabled: true,
    validWeight: true,
});

test("completed course below target is unreachable with no score out of zero", () => {
    const result = getTargetSummary([item("60")], 7, cutoffs);
    assert.equal(result.requiredPercent, null);
    assert.equal(result.requiredScore, "N/A");
    assert.equal(result.remainingWeight, 0);
    assert.equal(result.shortfall, 25);
    assert.equal(result.obtainable, false);
    assert.equal(result.achieved, false);
});

test("completed course at target is achieved, including a zero cutoff", () => {
    assert.equal(getTargetSummary([item("85")], 7, cutoffs).achieved, true);
    assert.equal(getTargetSummary([item("0")], 1, cutoffs).achieved, true);
});

test("rounding is opt-in and the half-point boundary meets the target", () => {
    assert.equal(getTargetSummary([item("84.5")], 7, cutoffs).achieved, false);
    assert.equal(getTargetSummary([item("84.5")], 7, cutoffs, true).achieved, true);
    assert.equal(getTargetSummary([item("84.49")], 7, cutoffs, true).obtainable, false);
});

test("rounding adjusts the score needed on remaining assessments", () => {
    const items = [item("80", "50%"), item("", "50%")];
    assert.equal(getTargetSummary(items, 7, cutoffs).requiredPercent, 90);
    assert.equal(getTargetSummary(items, 7, cutoffs, true).requiredPercent, 89);
});

test("zero scores count as completed; blanks count as remaining", () => {
    assert.equal(getTargetSummary([item("0")], 7, cutoffs).remainingWeight, 0);
    assert.equal(getTargetSummary([item("")], 7, cutoffs).remainingWeight, 100);
});

test("impossible targets with remaining assessments keep their required percentage", () => {
    const result = getTargetSummary([item("0", "50%"), item("", "50%")], 7, cutoffs);
    assert.equal(result.obtainable, false);
    assert.equal(result.requiredPercent, 170);
});

test("grade breakdown uses the same rounding and unreachable states", () => {
    const rows = getGradeDetailsRows([item("84.5")], cutoffs, true);
    assert.equal(rows[2].achieved, true);
    assert.equal(rows[2].cutoff, 84.5);
    assert.equal(rows[0].cutoff, 0);
    assert.equal(getGradeDetailsRows([item("60")], cutoffs)[2].requiredPercent, null);
});
