import type { Attraction, DayPlan, TripPlan } from "../types/trip";

export type MoveDirection = "up" | "down";
export type DeleteAttractionResult =
  | { status: "deleted"; attraction: Attraction }
  | { status: "last_attraction" }
  | { status: "not_found" };

export function cloneTripPlan(plan: TripPlan): TripPlan {
  if (typeof structuredClone === "function") {
    return structuredClone(plan);
  }
  return JSON.parse(JSON.stringify(plan)) as TripPlan;
}

export function getTripEditError(plan: TripPlan): string | null {
  for (const day of plan.days) {
    for (const attraction of day.attractions) {
      if (!attraction.address.trim()) {
        return `${attraction.name}的地址不能为空`;
      }
      if (!attraction.description.trim()) {
        return `${attraction.name}的描述不能为空`;
      }
      if (
        !Number.isInteger(attraction.visit_duration) ||
        attraction.visit_duration < 10 ||
        attraction.visit_duration > 480
      ) {
        return `${attraction.name}的游览时长应为 10–480 分钟`;
      }
    }
  }
  return null;
}

function findDay(plan: TripPlan, dayIndex: number): DayPlan | undefined {
  return plan.days.find((day) => day.day_index === dayIndex);
}

export function moveAttraction(
  plan: TripPlan,
  dayIndex: number,
  attractionIndex: number,
  direction: MoveDirection,
): boolean {
  const attractions = findDay(plan, dayIndex)?.attractions;
  if (!attractions) {
    return false;
  }

  const targetIndex =
    direction === "up" ? attractionIndex - 1 : attractionIndex + 1;
  if (
    attractionIndex < 0 ||
    attractionIndex >= attractions.length ||
    targetIndex < 0 ||
    targetIndex >= attractions.length
  ) {
    return false;
  }

  [attractions[attractionIndex], attractions[targetIndex]] = [
    attractions[targetIndex],
    attractions[attractionIndex],
  ];
  return true;
}

export function deleteAttraction(
  plan: TripPlan,
  dayIndex: number,
  attractionIndex: number,
): DeleteAttractionResult {
  const attractions = findDay(plan, dayIndex)?.attractions;
  if (
    !attractions ||
    attractionIndex < 0 ||
    attractionIndex >= attractions.length
  ) {
    return { status: "not_found" };
  }
  if (attractions.length <= 1) {
    return { status: "last_attraction" };
  }

  const [attraction] = attractions.splice(attractionIndex, 1);
  if (plan.budget) {
    plan.budget.total_attractions = Math.max(
      0,
      plan.budget.total_attractions - attraction.ticket_price,
    );
    plan.budget.total =
      plan.budget.total_attractions +
      plan.budget.total_hotels +
      plan.budget.total_meals +
      plan.budget.total_transportation;
  }
  return { status: "deleted", attraction };
}
