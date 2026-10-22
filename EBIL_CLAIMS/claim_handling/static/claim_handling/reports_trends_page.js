document.addEventListener('DOMContentLoaded', function () {
    const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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

    // Distinct colour per underwriter using evenly spaced hues
    function colorForIndex(i, total) {
        const hue = Math.round((360 / total) * i);
        return `hsl(${hue}, 70%, 45%)`;
    }

    // Shared options so every chart is configured the same way
    function baseOptions({ title, yTitle, tooltipSuffix = '', yTickSuffix = '', yMax }) {
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
                    labels: { usePointStyle: true }
                },
                title: { display: true, text: title, font: { size: 16 } }
            },
            scales: {
                x: { title: { display: true, text: 'Month(s)' } },
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

    // ---------- Data ----------
    const lodgedClosed = readJson('lodged-closed-data');
    const lodgedTrends = lodgedClosed.map(i => toNum(i.lodged));
    const closedTrends = lodgedClosed.map(i => toNum(i.closed));

    const avgTatValues = readJson('avg-tat-data').map(i => toNum(i.avg_tat));
    const avgSettlementRatioValues = readJson('avg-settlement-data').map(i => toNum(i.settlement_ratio));

    const settlementData = {};
    readJson('settlement-data').forEach(item => {
        const data = item.data || {};
        settlementData[item.underwriter] = MONTHS.map(m => toNum(data[m]));
    });
    const underwritersList = Object.keys(settlementData);

    // ---------- Chart 1: Lodged vs Closed ----------
    new Chart(document.getElementById('lodged-closed-trend-graph'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [
                {
                    label: 'Lodged Claims',
                    data: lodgedTrends,
                    fill: '+1',
                    backgroundColor: 'rgba(45, 104, 235, 0.1)',
                    borderColor: '#2563EB',
                    pointRadius: 4,
                    pointBackgroundColor: '#2563EB',
                    tension: 0.3
                },
                {
                    label: 'Closed Claims',
                    data: closedTrends,
                    borderColor: 'orange',
                    pointRadius: 4,
                    pointBackgroundColor: 'orange',
                    tension: 0.3
                }
            ]
        },
        options: baseOptions({
            title: 'Lodged vs Closed Claims Trend - 2026',
            yTitle: "Claims' Number"
        })
    });

    // ---------- Chart 2: Average turnaround time ----------
    new Chart(document.getElementById('avg-tat-per-month-trend'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [{
                label: 'Average Turnaround Time',
                data: avgTatValues,
                fill: true,
                backgroundColor: 'rgba(135, 206, 235, 0.3)',
                borderColor: '#2563EB',
                pointRadius: 4,
                pointBackgroundColor: '#2563EB',
                tension: 0.3
            }]
        },
        options: baseOptions({
            title: 'Average Turnaround Time Trend - 2026',
            yTitle: 'Average Turnaround Time (days)',
            tooltipSuffix: ' days'
        })
    });

    // ---------- Chart 3: Average settlement ratio ----------
    new Chart(document.getElementById('avg-settlement-ratio-per-month-trend-graph'), {
        type: 'line',
        data: {
            labels: MONTHS,
            datasets: [{
                label: 'Average Settlement Ratio',
                data: avgSettlementRatioValues,
                fill: true,
                backgroundColor: 'rgba(53, 122, 84, 0.15)',
                borderColor: '#357A54',
                pointRadius: 4,
                pointBackgroundColor: '#357A54',
                tension: 0.3
            }]
        },
        options: baseOptions({
            title: 'Average Settlement Ratio Trend - 2026',
            yTitle: 'Average Settlement Ratio (%)',
            tooltipSuffix: ' %',
            yTickSuffix: '%',
            yMax: 100
        })
    });

    // ---------- Chart 4: Settlement ratio per underwriter ----------
    const settlementRatioChart = new Chart(
        document.getElementById('settlement-ratio-trend-for-each-underwriter'),
        {
            type: 'line',
            data: { labels: MONTHS, datasets: [] },
            options: baseOptions({
                title: 'Settlement Ratio Trend by Underwriter - 2026',
                yTitle: 'Settlement Ratio (%)',
                tooltipSuffix: '%',
                yTickSuffix: '%'
            })
        }
    );

    const underwriterDatasets = underwritersList.map((underwriter, i) => {
        const color = colorForIndex(i, underwritersList.length);
        return {
            label: underwriter,
            data: settlementData[underwriter],
            backgroundColor: 'rgba(45, 104, 235, 0.1)',
            borderColor: color,
            pointRadius: 4,
            pointBackgroundColor: color,
            tension: 0.3,
            fill: true,
            borderWidth: 2,
            spanGaps: true // skip missing months instead of dropping the line to zero
        };
    });

    const underwriterSelect = document.getElementById('underwriter-select');

    underwritersList.forEach(function (underwriter) {
        const option = document.createElement('option');
        option.value = underwriter;
        option.textContent = underwriter;
        underwriterSelect.appendChild(option);
    });

    underwriterSelect.addEventListener('change', function () {
        const selected = underwriterDatasets.find(ds => ds.label === underwriterSelect.value);
        settlementRatioChart.data.datasets = selected ? [selected] : [];
        settlementRatioChart.update();
    });

    // Select the first underwriter by default so the chart isn't empty on load
    if (underwritersList.length > 0) {
        underwriterSelect.value = underwritersList[0];
        underwriterSelect.dispatchEvent(new Event('change'));
    }
});