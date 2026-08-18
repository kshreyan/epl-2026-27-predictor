import { useDashboardJson } from '../lib/useDashboardData'
import type { ModelPerformancePayload } from '../lib/types'
import { num, pct } from '../lib/format'
import { CalibrationChart } from '../components/CalibrationChart'
import { PageState } from '../components/PageState'

export function ModelPerformancePage() {
  const { data, error, loading } = useDashboardJson<ModelPerformancePayload>('epl_model_performance.json')
  if (loading || error || !data) return <PageState loading={loading} error={error} />

  const best = [...data.data].sort((a, b) => a.log_loss - b.log_loss)[0]
  const ensembleSeasonWins = data.ensemble_per_season_comparison.filter((r) => r.ensemble_wins_season).length
  const ensembleSeasons = data.ensemble_per_season_comparison.length

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <section className="border border-[var(--color-border)] p-3 text-[12px] leading-relaxed">
        <h2 className="mb-1 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">Primary model</h2>
        <p>
          <span className="text-[var(--color-accent)]">{best?.model}</span> -- lowest backtest log loss on{' '}
          <span className="tnum">{best?.n_matches}</span> real historical matches (2019/20-2025/26, rolling-origin, no
          random splitting).
        </p>
        {ensembleSeasons > 0 && (
          <p className="mt-2 text-[var(--color-text-faint)]">
            A stacked ensemble of the four real-data models was evaluated with a paired bootstrap significance
            test; it won only <span className="tnum">{ensembleSeasonWins}</span> of{' '}
            <span className="tnum">{ensembleSeasons}</span> backtest seasons and its 95% confidence interval on the
            log-loss difference straddled zero -- not statistically distinguishable from noise, so Dixon-Coles
            alone remains primary.
          </p>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">Backtest model comparison</h2>
        <div className="overflow-x-auto border border-[var(--color-border)]">
          <table>
            <thead>
              <tr className="border-b border-[var(--color-border)] text-left text-[10px] uppercase tracking-wide text-[var(--color-text-faint)]">
                <th className="px-2 py-1.5">Model</th>
                <th className="px-2 py-1.5 text-right">Log loss</th>
                <th className="px-2 py-1.5 text-right">Brier</th>
                <th className="px-2 py-1.5 text-right">RPS</th>
                <th className="px-2 py-1.5 text-right">Accuracy</th>
                <th className="px-2 py-1.5 text-right">Favorite acc.</th>
              </tr>
            </thead>
            <tbody>
              {data.data.map((row) => (
                <tr key={row.model} className={`border-b border-[var(--color-border)] last:border-0 ${row.model === best?.model ? 'bg-[var(--color-panel)]' : ''}`}>
                  <td className="px-2 py-1.5">{row.model}</td>
                  <td className="tnum px-2 py-1.5 text-right">{num(row.log_loss, 4)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{num(row.brier_score, 4)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{num(row.ranked_probability_score, 4)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(row.accuracy)}</td>
                  <td className="tnum px-2 py-1.5 text-right">{pct(row.favorite_accuracy)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <div className="mb-2 flex items-baseline justify-between">
          <h2 className="text-[11px] uppercase tracking-wider text-[var(--color-text-faint)]">Calibration (reliability curve)</h2>
          {data.calibration_summary && (
            <span className="tnum text-[11px] text-[var(--color-text-faint)]">
              {data.calibration_summary.method} · ECE {num(data.calibration_summary.ece, 4)} · {data.calibration_summary.n_matches} matches
            </span>
          )}
        </div>
        <div className="border border-[var(--color-border)] p-2">
          <CalibrationChart bins={data.reliability_table} />
        </div>
      </section>
    </div>
  )
}
