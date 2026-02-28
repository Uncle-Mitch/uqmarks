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
};

export type StoredCard = {
    courseCode: string;
    semesterId: string;
    semesterLabel: string;
    dataSource: AssessmentItem[];
    targetGrade: number;
    collapsed?: boolean;
};

export type GradeDetailsRow = {
    key: number;
    grade: number;
    cutoff: number;
    requiredPercent: number;
    requiredScore: string;
    achieved: boolean;
    obtainable: boolean;
};

export type GradeCutoff = {
    grade: number;
    cutoff: number;
};

export type TargetSummary = {
    requiredPercent: number;
    requiredScore: string;
    remainingWeight: number;
};

export type SemesterOption = {
    value: string;
    label: string;
};
