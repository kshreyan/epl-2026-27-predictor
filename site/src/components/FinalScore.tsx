// Shows the real final score for a completed match alongside the
// model's (frozen, pre-kickoff) predicted score -- distinct styling so
// the two are never confused: predicted_score/predicted_score_model_only
// never changes after kickoff, this is the actual real-world result.
export function FinalScore({
  status,
  actualHomeGoals,
  actualAwayGoals,
}: {
  status: string
  actualHomeGoals: number | null
  actualAwayGoals: number | null
}) {
  if (status !== 'completed' || actualHomeGoals === null || actualAwayGoals === null) return null
  return (
    <span className="tnum block text-[10px] font-normal text-[var(--color-positive)]">
      FT {actualHomeGoals}-{actualAwayGoals}
    </span>
  )
}
