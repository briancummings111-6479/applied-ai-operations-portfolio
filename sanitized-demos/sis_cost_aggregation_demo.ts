/**
 * SANITIZED EDUCATIONAL DEMO: Student Information System (SIS) Cloud Cost Optimizer
 * Author: Brian Cummings | Portfolio: applied-ai-operations-portfolio
 *
 * PLAIN-ENGLISH SUMMARY FOR NON-TECHNICAL REVIEWERS:
 * When our alternative high school expanded from one room to a multi-classroom
 * site with 6 periods, every staff member opening the scheduler originally loaded
 * the entire school's class schedule from the database to check open seats.
 * That caused $50–$100/day in runaway cloud database read charges.
 *
 * This scheduled backend function solves the problem permanently:
 *   1. Every 5 minutes, ONE server job counts seat enrollments per room & period.
 *   2. It writes those totals into ONE tiny summary document.
 *   3. Staff browsers read that single summary instead of thousands of records,
 *      cutting Firestore read operations by 99%+ while preventing room overbooking.
 */

// 1. SYNTHETIC SCHEDULE ASSIGNMENT RECORD (100% fictional IDs)
export interface ScheduleAssignment {
  assignmentId: string;   // e.g., "2026-11-16_STU4092_Mon_P4"
  blockId: string;        // Six 6-week blocks per academic year
  weekStartISO: string;
  dayOfWeek: "Mon" | "Tue" | "Wed" | "Thu" | "Fri";
  periodNumber: 1 | 2 | 3 | 4 | 5 | 6;
  roomCode: string;       // e.g., "SHOP_BAY_1"
  courseId: string;       // e.g., "CL-210"
  studentStatus: "active" | "archived";
}

// 2. PRE-AGGREGATED SUMMARY DOCUMENT (Read by frontend in 1 single database call)
export interface EnrollmentSummarySnapshot {
  generatedAtISO: string;
  activeBlockId: string;
  roomSeatCounts: Record<string, number>; // Key: "week|day|period|room" -> active count
  overbookedSlots: string[];              // Immediate alert flags for counselors
}

// 3. SCHEDULED PRE-AGGREGATION ENGINE (Runs on backend every 5 minutes)
export function buildEnrollmentSummary(
  assignments: ScheduleAssignment[],
  roomCapacities: Record<string, number>,
  activeBlockId: string
): EnrollmentSummarySnapshot {
  const roomSeatCounts: Record<string, number> = {};
  const overbookedSlots: string[] = [];

  for (const row of assignments) {
    // Never count archived students toward live classroom capacity
    if (row.studentStatus === "archived" || row.blockId !== activeBlockId) {
      continue;
    }

    const slotKey = `${row.weekStartISO}|${row.dayOfWeek}|P${row.periodNumber}|${row.roomCode}`;
    roomSeatCounts[slotKey] = (roomSeatCounts[slotKey] || 0) + 1;
  }

  // Flag any room/period exceeding its physical seat limit
  for (const [slotKey, enrolledCount] of Object.entries(roomSeatCounts)) {
    const roomCode = slotKey.split("|")[3];
    const maxSeats = roomCapacities[roomCode] ?? 20;
    if (enrolledCount > maxSeats) {
      overbookedSlots.push(`${slotKey} (${enrolledCount}/${maxSeats})`);
    }
  }

  return {
    generatedAtISO: new Date().toISOString(),
    activeBlockId,
    roomSeatCounts,
    overbookedSlots,
  };
}
