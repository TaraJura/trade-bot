let profitChart = null;
let winLossChart = null;
let currentEditSymbol = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadStatistics();
    loadPositions();
    loadSymbols();
    
    // Update data every 5 seconds
    setInterval(() => {
        loadStatistics();
        loadPositions();
    }, 5000);
    
    // Modal handlers
    document.getElementById('add-position-btn').addEventListener('click', openAddModal);
    document.querySelector('.close').addEventListener('click', closeModal);
    document.getElementById('position-form').addEventListener('submit', handlePositionSubmit);
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        const modal = document.getElementById('position-modal');
        if (event.target === modal) {
            closeModal();
        }
    };
});

function initializeCharts() {
    // Profit/Loss Chart
    const profitCtx = document.getElementById('profitChart').getContext('2d');
    profitChart = new Chart(profitCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative Profit',
                data: [],
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#c9d1d9'
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#8b949e'
                    },
                    grid: {
                        color: '#30363d'
                    }
                },
                y: {
                    ticks: {
                        color: '#8b949e',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    },
                    grid: {
                        color: '#30363d'
                    }
                }
            }
        }
    });
    
    // Win/Loss Chart
    const winLossCtx = document.getElementById('winLossChart').getContext('2d');
    winLossChart = new Chart(winLossCtx, {
        type: 'doughnut',
        data: {
            labels: ['Winning Trades', 'Losing Trades'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#3fb950', '#f85149'],
                borderColor: '#161b22',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#c9d1d9'
                    }
                }
            }
        }
    });
}

async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const stats = await response.json();
        
        // Update statistics
        document.getElementById('total-trades').textContent = stats.total_trades;
        document.getElementById('win-rate').textContent = stats.win_rate.toFixed(1) + '%';
        document.getElementById('total-profit').textContent = '$' + stats.total_profit.toFixed(2);
        document.getElementById('active-positions').textContent = stats.active_positions;
        
        document.getElementById('best-trade').textContent = '$' + stats.best_trade.toFixed(2);
        document.getElementById('worst-trade').textContent = '$' + stats.worst_trade.toFixed(2);
        document.getElementById('avg-profit').textContent = '$' + stats.average_profit.toFixed(2);
        document.getElementById('total-volume').textContent = '$' + stats.total_volume.toFixed(2);
        
        // Update win/loss chart
        winLossChart.data.datasets[0].data = [stats.winning_trades, stats.losing_trades];
        winLossChart.update();
        
        // Update profit chart (would need trade history endpoint for real data)
        updateProfitChart();
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const data = await response.json();
        
        const tbody = document.getElementById('positions-mgmt-body');
        
        if (data.positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="no-data">No open positions</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.positions.map(position => {
            const pnlClass = position.pnl >= 0 ? 'profit-positive' : 'profit-negative';
            return `
                <tr>
                    <td>${position.symbol}</td>
                    <td>${position.quantity.toFixed(6)}</td>
                    <td>$${position.entry_price.toFixed(2)}</td>
                    <td>$${position.current_price.toFixed(2)}</td>
                    <td class="${pnlClass}">$${position.pnl.toFixed(2)} (${position.pnl_percentage.toFixed(2)}%)</td>
                    <td>$${position.stop_loss.toFixed(2)}</td>
                    <td>$${position.take_profit.toFixed(2)}</td>
                    <td>
                        <div class="position-actions">
                            <button class="btn-small btn-edit" onclick="editPosition('${position.symbol}', ${position.stop_loss}, ${position.take_profit})">Edit</button>
                            <button class="btn-small btn-close" onclick="closePosition('${position.symbol}')">Close</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

async function loadSymbols() {
    try {
        const response = await fetch('/api/symbols');
        const data = await response.json();
        
        const select = document.getElementById('position-symbol');
        select.innerHTML = '<option value="">Select Symbol</option>' + 
            data.symbols.map(symbol => 
                `<option value="${symbol}">${symbol.replace('USDT', '/USDT')}</option>`
            ).join('');
    } catch (error) {
        console.error('Error loading symbols:', error);
    }
}

function openAddModal() {
    currentEditSymbol = null;
    document.getElementById('modal-title').textContent = 'Add Position';
    document.getElementById('position-form').reset();
    document.getElementById('position-symbol').disabled = false;
    document.getElementById('stop-loss-group').style.display = 'none';
    document.getElementById('take-profit-group').style.display = 'none';
    document.getElementById('position-modal').style.display = 'block';
}

function editPosition(symbol, stopLoss, takeProfit) {
    currentEditSymbol = symbol;
    document.getElementById('modal-title').textContent = 'Edit Position';
    document.getElementById('position-symbol').value = symbol;
    document.getElementById('position-symbol').disabled = true;
    document.getElementById('position-quantity').style.display = 'none';
    document.getElementById('position-quantity').previousElementSibling.style.display = 'none';
    document.getElementById('position-price').style.display = 'none';
    document.getElementById('position-price').previousElementSibling.style.display = 'none';
    document.getElementById('stop-loss-group').style.display = 'block';
    document.getElementById('take-profit-group').style.display = 'block';
    document.getElementById('position-stop-loss').value = stopLoss;
    document.getElementById('position-take-profit').value = takeProfit;
    document.getElementById('position-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('position-modal').style.display = 'none';
    document.getElementById('position-quantity').style.display = 'block';
    document.getElementById('position-quantity').previousElementSibling.style.display = 'block';
    document.getElementById('position-price').style.display = 'block';
    document.getElementById('position-price').previousElementSibling.style.display = 'block';
}

async function handlePositionSubmit(event) {
    event.preventDefault();
    
    if (currentEditSymbol) {
        // Update existing position
        const data = {
            stop_loss: parseFloat(document.getElementById('position-stop-loss').value),
            take_profit: parseFloat(document.getElementById('position-take-profit').value)
        };
        
        try {
            const response = await fetch(`/api/positions/${currentEditSymbol}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                showNotification('Position updated successfully', 'success');
                closeModal();
                loadPositions();
            } else {
                showNotification(result.message, 'error');
            }
        } catch (error) {
            showNotification('Error updating position', 'error');
        }
    } else {
        // Create new position
        const data = {
            symbol: document.getElementById('position-symbol').value,
            quantity: parseFloat(document.getElementById('position-quantity').value),
            entry_price: parseFloat(document.getElementById('position-price').value)
        };
        
        try {
            const response = await fetch('/api/positions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            if (result.success) {
                showNotification('Position created successfully', 'success');
                closeModal();
                loadPositions();
            } else {
                showNotification(result.message, 'error');
            }
        } catch (error) {
            showNotification('Error creating position', 'error');
        }
    }
}

async function closePosition(symbol) {
    if (!confirm(`Are you sure you want to close the position for ${symbol}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/positions/${symbol}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (result.success) {
            showNotification('Position closed successfully', 'success');
            loadPositions();
            loadStatistics();
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Error closing position', 'error');
    }
}

function updateProfitChart() {
    // This is a placeholder - would need actual trade history data
    // For now, just show sample data
    const labels = [];
    const data = [];
    const now = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(now - i * 24 * 60 * 60 * 1000);
        labels.push(date.toLocaleDateString());
        data.push(Math.random() * 1000 - 200); // Random profit between -200 and 800
    }
    
    // Calculate cumulative profit
    let cumulative = 0;
    const cumulativeData = data.map(profit => {
        cumulative += profit;
        return cumulative;
    });
    
    profitChart.data.labels = labels;
    profitChart.data.datasets[0].data = cumulativeData;
    profitChart.update();
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background-color: ${type === 'success' ? '#238636' : '#da3633'};
        color: white;
        border-radius: 6px;
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}