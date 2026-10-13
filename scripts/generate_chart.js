const fs = require('fs');

const data = fs.readFileSync('simple_data.csv', 'utf-8').trim().split('\n').map(line => {
    const [gameCode, gameName, balance, bet] = line.split(',');
    return {
        gameCode,
        gameName: gameName || gameCode,
        balance: parseFloat(balance),
        bet: parseFloat(bet)
    };
}).filter(d => d.balance > 0 && d.bet > 0);

// Group by gameCode
const groups = {};
data.forEach(d => {
    if (!groups[d.gameCode]) {
        groups[d.gameCode] = { label: d.gameName || d.gameCode, balances: [], bets: [] };
    }
    groups[d.gameCode].balances.push(d.balance);
    groups[d.gameCode].bets.push(d.bet);
});

// Create chart.js config
const colors = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E9', '#F8B500', '#00CED1', '#FF69B4', '#32CD32',
    '#FFD700', '#FF4500', '#8A2BE2', '#00FA9A', '#FF1493', '#00BFFF'
];

const datasets = Object.entries(groups).map(([code, g], i) => ({
    label: g.label,
    data: g.balances.map((b, idx) => ({ x: Math.log10(b), y: Math.log10(g.bets[idx]) })),
    backgroundColor: colors[i % colors.length],
    borderColor: colors[i % colors.length],
    pointRadius: 4,
    pointHoverRadius: 6,
    showLine: false
}));

const config = {
    type: 'scatter',
    data: { datasets },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: true,
                text: 'Balance vs. Bet Size Correlation (Log-Log Scatter)',
                font: { size: 16 }
            },
            legend: {
                display: true,
                position: 'right'
            },
            tooltip: {
                callbacks: {
                    label: (ctx) => {
                        const x = Math.pow(10, ctx.parsed.x).toLocaleString();
                        const y = Math.pow(10, ctx.parsed.y).toLocaleString();
                        return `${ctx.dataset.label}: Balance=${x}, Bet=${y}`;
                    }
                }
            }
        },
        scales: {
            x: {
                type: 'linear',
                position: 'bottom',
                title: { display: true, text: 'Log10(Player Balance)' },
                grid: { color: 'rgba(0,0,0,0.1)' }
            },
            y: {
                title: { display: true, text: 'Log10(Wager Size)' },
                grid: { color: 'rgba(0,0,0,0.1)' }
            }
        }
    }
};

console.log(JSON.stringify(config, null, 2));