/**
 * SANITIZED EDUCATIONAL DEMO: Legacy FileMaker to Cloud Case Management Mapper
 * Author: Brian Cummings | Portfolio: applied-ai-operations-portfolio
 *
 * PLAIN-ENGLISH SUMMARY FOR NON-TECHNICAL REVIEWERS:
 * Before our web portal existed, partner organizations tracked cases in legacy
 * FileMaker tables and spreadsheets with cryptic column names (like "Pt_ID_99").
 * This script acts as a strict security checkpoint:
 *   1. It translates cryptic legacy column names into clean, readable fields.
 *   2. It separates private participant identity from state grant metrics.
 *   3. It quarantine-flags incomplete records before they can corrupt reports.
 */

// 1. LEGACY INPUT SHAPE (Cryptic columns exported from older desktop databases)
export interface LegacyFileMakerExportRow {
  FM_Rec_UUID: string;
  Pt_Enroll_Dt_Txt: string;      // Often inconsistently formatted in legacy exports
  Partner_Org_Code: string;      // e.g., "SHASTA_WORK_04"
  Milestone_01_Intake: "Y" | "N" | "";
  Milestone_02_Resume: "Y" | "N" | "";
  Milestone_03_Placed: "Y" | "N" | "";
  Hourly_Wage_Num?: number;
  Raw_Case_Notes_PII?: string;   // Sensitive text that must NOT enter aggregate grant views
}

// 2. CLEAN CLOUD PORTAL RECORD (Standardized, role-restricted, grant-ready)
export interface SanitizedGrantComplianceRecord {
  participantToken: string;      // Anonymized token for state grant auditing
  partnerSiteId: string;
  enrollmentDateISO: string;
  completedMilestones: {
    intakeVerified: boolean;
    resumeCompleted: boolean;
    employmentPlaced: boolean;
  };
  completionPercentage: number;
  verifiedStartingWage: number | null;
  requiresStaffFollowUp: boolean;
  auditStatus: "READY_FOR_STATE_REPORT" | "QUARANTINED_MISSING_DATA";
}

// 3. DETERMINISTIC TRANSFORMATION & PRIVACY REDACTION FUNCTION
export function normalizeLegacyCaseRecord(
  rawRow: LegacyFileMakerExportRow
): SanitizedGrantComplianceRecord {
  // Parse and validate the enrollment date; flag if missing or malformed
  const parsedDate = Date.parse(rawRow.Pt_Enroll_Dt_Txt);
  const isValidDate = !Number.isNaN(parsedDate);

  const intakeVerified = rawRow.Milestone_01_Intake === "Y";
  const resumeCompleted = rawRow.Milestone_02_Resume === "Y";
  const employmentPlaced = rawRow.Milestone_03_Placed === "Y";

  // Calculate 30-day onboarding & placement progress (0%, 33%, 67%, or 100%)
  const completedCount = [intakeVerified, resumeCompleted, employmentPlaced].filter(Boolean).length;
  const completionPercentage = Math.round((completedCount / 3) * 100);

  // Notice: `Raw_Case_Notes_PII` is intentionally excluded from this reporting object
  // so partner coordinators and grant auditors only see de-identified compliance data.
  return {
    participantToken: `PT-${rawRow.FM_Rec_UUID.slice(0, 8).toUpperCase()}`,
    partnerSiteId: rawRow.Partner_Org_Code.trim().toUpperCase(),
    enrollmentDateISO: isValidDate ? new Date(parsedDate).toISOString().split("T")[0] : "INVALID_DATE",
    completedMilestones: {
      intakeVerified,
      resumeCompleted,
      employmentPlaced,
    },
    completionPercentage,
    verifiedStartingWage:
      typeof rawRow.Hourly_Wage_Num === "number" && rawRow.Hourly_Wage_Num > 0
        ? rawRow.Hourly_Wage_Num
        : null,
    requiresStaffFollowUp: !isValidDate || !intakeVerified,
    auditStatus: isValidDate && intakeVerified ? "READY_FOR_STATE_REPORT" : "QUARANTINED_MISSING_DATA",
  };
}
