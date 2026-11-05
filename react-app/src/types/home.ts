export type AssessmentItem = {
    key: number;
    assessment: string;
    weight: string;
    score: string;
    enabled: boolean;
    validWeight: boolean;
};

export type CourseCard = {
    id: string;
    courseCode: string;
    semesterId: string;
    semesterLabel: string;
    courseProfileUrl?: string;
    loading: boolean;
    showURLRequest: boolean;
    searchError: string;
    validInput: boolean;
    editingWeights: boolean;
    collapsed: boolean;
    dataSource: AssessmentItem[];
    totalScore: number;
    weightValid: boolean;
    targetGrade: number;
    roundFinalGrade: boolean;
};

export type StoredCard = {
    courseCode: string;
    semesterId: string;
    semesterLabel: string;
    dataSource: AssessmentItem[];
    targetGrade: number;
    roundFinalGrade?: boolean;
    collapsed?: boolean;
};

export type GradeDetailsRow = {
    key: number;
    grade: number;
    cutoff: number;
    requiredPercent: number | null;
    requiredScore: string;
    achieved: boolean;
    obtainable: boolean;
};

export type GradeCutoff = {
    grade: number;
    cutoff: number;
};

export type TargetSummary = {
    requiredPercent: number | null;
    requiredScore: string;
    remainingWeight: number;
    achieved: boolean;
    obtainable: boolean;
    shortfall: number;
};

export type SemesterOption = {
    value: string;
    label: string;
};
