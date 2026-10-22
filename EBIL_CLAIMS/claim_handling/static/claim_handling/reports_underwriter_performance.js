document.addEventListener('DOMContentLoaded', function () {

    // ---------- Colours (match the table's CSS bands) ----------
    const GOOD = '#12b76a5c';
    const FAIR = '#d977065d';
    const POOR = '#d92c205a';
    const BAR_BORDER = '#f5f2f2';

    // ---------- Helpers ----------
    // Read JSON written by Django's json_script; fall back to [] if missing/invalid
    function readJson(id) {
        const el = document.getElementById(id);
        if (!el) return [];
        try {
            return JSON.parse(el.textContent);
        } catch (e) {
            console.error('Could not parse JSON for #' + id, e);
            return [];
        }
    }

    // Decimals arrive as strings from Django, so convert; keep null for missing values
    function toNum(value) {
        if (value === null || value === undefined || value === '') return null;
        const n = Number(value);
        return Number.isNaN(n) ? null : n;
    }

    // Pick a colour from two thresholds. lowIsGood = true means smaller values are better.
    function colorByThreshold(value, fairLimit, poorLimit, lowIsGood) {
        if (lowIsGood) {
            if (value < fairLimit) return GOOD;
            if (value < poorLimit) return FAIR;
            return POOR;
        }
        if (value < fairLimit) return POOR;
        if (value < poorLimit) return FAIR;
        return GOOD;
    }

    // Custom legend made of three colour keys
    function legendLabels(items) {
        return function () {
            return items.map(item => ({
                text: item.text,
                fillStyle: item.color,
                strokeStyle: BAR_BORDER,
                lineWidth: 1,
                hidden: false
            }));
        };
    }

    // Shared chart options
    function baseOptions({ title, xTitle, yTitle, legend, tooltipSuffix = '', yTickSuffix = '', yMax }) {
        const yScale = {
            beginAtZero: true,
            title: { display: true, text: yTitle }
        };
        if (yMax !== undefined) yScale.max = yMax;
        if (yTickSuffix) {
            yScale.ticks = { callback: value => value + yTickSuffix };
        }

        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: legend ? { generateLabels: legend } : {}
                },
                title: { display: true, text: title, font: { size: 16 } }
            },
            scales: {
                x: { title: { display: true, text: xTitle } },
                y: yScale
            }
        };

        if (tooltipSuffix) {
            options.plugins.tooltip = {
                callbacks: {
                    label: ctx => (ctx.parsed.y === null ? '' : ctx.parsed.y + tooltipSuffix)
                }
            };
        }
        return options;
    }

    // Standard bar dataset styling
    function barStyle(extra) {
        return Object.assign({
            borderColor: BAR_BORDER,
            borderWidth: 1,
            borderRadius: 2,
            maxBarThickness: 100
        }, extra);
    }

    // ---------- Data ----------
    const underwriters = readJson('underwriter-data');

    const underwriterNames = underwriters.map(u => u.underwriter_name);
    const settlementRatios = underwriters.map(u => toNum(u.settlement_ratio));
    const averageTats = underwriters.map(u => toNum(u.average_tat_dv));
    const closedClaims = underwriters.map(u => toNum(u.closed_claims));
    const pendingClaims = underwriters.map(u => toNum(u.pending_claims));
    const rejectionRates = underwriters.map(u => toNum(u.rejection_rate));

    // Higher settlement ratio is better: <40 poor, 40-59 fair, >=60 good
    const settlementColors = settlementRatios.map(v => colorByThreshold(v, 40, 60, false));
    // Lower rejection rate is better: <40 good, 40-59 fair, >=60 poor
    const rejectionColors = rejectionRates.map(v => colorByThreshold(v, 40, 60, true));
    // Lower turnaround is better: <5 good, 5-10 fair, >=11 poor
    const tatColors = averageTats.map(v => colorByThreshold(v, 5, 11, true));

    // ---------- Chart 1: Settlement ratio ----------
    new Chart(document.getElementById('settlement-ratio-graph'), {
        type: 'bar',
        data: {
            labels: underwriterNames,
            datasets: [barStyle({
                label: 'Settlement Ratio (%)',
                data: settlementRatios,
                backgroundColor: settlementColors
            })]
        },
        options: baseOptions({
            title: 'Settlement Ratio by Underwriter - 2026',
            xTitle: 'Underwriter',
            yTitle: 'Settlement Ratio (%)',
            tooltipSuffix: '%',
            yTickSuffix: '%',
            yMax: 100,
            legend: legendLabels([
                { text: 'Excellent (≥ 60%)', color: GOOD },
                { text: 'Fairly Good (40% - 59%)', color: FAIR },
                { text: 'Below Threshold (< 40%)', color: POOR }
            ])
        })
    });

    // ---------- Chart 2: Closed vs pending claims ----------
    new Chart(document.getElementById('pending_and_closed_each_underwriter_graph'), {
        type: 'bar',
        data: {
            labels: underwriterNames,
            datasets: [
                barStyle({ label: 'Closed Claims', data: closedClaims, backgroundColor: 'lightblue' }),
                barStyle({ label: 'Pending Claims', data: pendingClaims, backgroundColor: '#fce2b1' })
            ]
        },
        options: baseOptions({
            title: 'Pending and Closed Claims for Each Underwriter - 2026',
            xTitle: 'Underwriters',
            yTitle: 'Number of Claims'
        })
    });

    // ---------- Chart 3: Average turnaround time ----------
    new Chart(document.getElementById('average_tat_dv_graph'), {
        type: 'bar',
        data: {
            labels: underwriterNames,
            datasets: [barStyle({
                label: 'Average Turnaround Time',
                data: averageTats,
                backgroundColor: tatColors
            })]
        },
        options: baseOptions({
            title: 'Average Turnaround Time for Each Underwriter - 2026',
            xTitle: 'Underwriters',
            yTitle: 'Average Turnaround Time (days)',
            tooltipSuffix: ' days',
            legend: legendLabels([
                { text: 'Excellent (< 5 days)', color: GOOD },
                { text: 'Fairly Good (5 - 10 days)', color: FAIR },
                { text: 'Below Threshold (≥ 11 days)', color: POOR }
            ])
        })
    });

    // ---------- Chart 4: Rejection rate ----------
    new Chart(document.getElementById('rejection_rate_graph'), {
        type: 'bar',
        data: {
            labels: underwriterNames,
            datasets: [barStyle({
                label: 'Rejection Rate (%)',
                data: rejectionRates,
                backgroundColor: rejectionColors
            })]
        },
        options: baseOptions({
            title: 'Rejection Rates by Underwriters - 2026',
            xTitle: 'Underwriter',
            yTitle: 'Rejection Rate (%)',
            tooltipSuffix: '%',
            yTickSuffix: '%',
            yMax: 100,
            legend: legendLabels([
                { text: 'Low (< 40%)', color: GOOD },
                { text: 'Average (40% - 59%)', color: FAIR },
                { text: 'High (≥ 60%)', color: POOR }
            ])
        })
    });
});