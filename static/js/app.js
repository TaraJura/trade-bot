let updateInterval = null;

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const saveConfigBtn = document.getElementById('save-config');
    
    startBtn.addEventListener('click', startBot);
    stopBtn.addEventListener('click', stopBot);
    saveConfigBtn.addEventListener('click', saveConfig);
    
    loadSymbols();
    updateStatus();
    setInterval(updateStatus, 5000);
});

async function startBot() {
    const strategy = document.getElementById('strategy').value;
    const symbol = document.getElementById('symbol').value;
    const interval = document.getElementById('interval').value;
    const testMode = document.getElementById('test-mode').checked;
    
    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                strategy: strategy,
                symbol: symbol,
                interval: interval,
                test_mode: testMode
            }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
            showNotification('Bot started successfully', 'success');
            updateStatus();
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error starting bot: ' + error.message, 'error');
    }
}

async function stopBot() {
    try {
        const response = await fetch('/api/stop', {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
            showNotification('Bot stopped successfully', 'success');
            updateStatus();
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error stopping bot: ' + error.message, 'error');
    }
}

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        const statusText = document.getElementById('status-text');
        const statusDot = document.getElementById('status-dot');
        
        if (data.is_running) {
            statusText.textContent = data.test_mode ? 'Running (Test Mode)' : 'Running (Live)';
            statusDot.className = 'online';
            document.getElementById('start-btn').disabled = true;
            document.getElementById('stop-btn').disabled = false;
        } else {
            statusText.textContent = 'Offline';
            statusDot.className = 'offline';
            document.getElementById('start-btn').disabled = false;
            document.getElementById('stop-btn').disabled = true;
        }
        
        if (data.usdt_balance !== undefined) {
            document.getElementById('usdt-balance').textContent = data.usdt_balance.toFixed(2);
            document.getElementById('total-value').textContent = data.total_value.toFixed(2);
        }
        
        updatePositions(data.positions || []);
        updateTrades(data.recent_trades || []);
        
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

function updatePositions(positions) {
    const tbody = document.getElementById('positions-body');
    
    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No open positions</td></tr>';
        return;
    }
    
    tbody.innerHTML = positions.map(position => {
        const pnlClass = position.pnl >= 0 ? 'profit-positive' : 'profit-negative';
        return `
            <tr>
                <td>${position.symbol}</td>
                <td>${position.quantity.toFixed(6)}</td>
                <td>$${position.entry_price.toFixed(2)}</td>
                <td>$${position.current_price.toFixed(2)}</td>
                <td class="${pnlClass}">$${position.pnl.toFixed(2)}</td>
                <td class="${pnlClass}">${position.pnl_percentage.toFixed(2)}%</td>
            </tr>
        `;
    }).join('');
}

function updateTrades(trades) {
    const tbody = document.getElementById('trades-body');
    
    if (trades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No trades yet</td></tr>';
        return;
    }
    
    tbody.innerHTML = trades.map(trade => {
        const time = new Date(trade.timestamp).toLocaleString();
        const profitClass = trade.profit >= 0 ? 'profit-positive' : 'profit-negative';
        const profitText = trade.profit !== null ? `$${trade.profit.toFixed(2)}` : '-';
        
        return `
            <tr>
                <td>${time}</td>
                <td>${trade.symbol}</td>
                <td>${trade.action}</td>
                <td>$${trade.price.toFixed(2)}</td>
                <td>${trade.quantity.toFixed(6)}</td>
                <td class="${profitClass}">${profitText}</td>
            </tr>
        `;
    }).join('');
}

async function loadSymbols() {
    try {
        const response = await fetch('/api/symbols');
        const data = await response.json();
        
        const symbolSelect = document.getElementById('symbol');
        symbolSelect.innerHTML = data.symbols.map(symbol => 
            `<option value="${symbol}">${symbol.replace('USDT', '/USDT')}</option>`
        ).join('');
    } catch (error) {
        console.error('Error loading symbols:', error);
    }
}

async function saveConfig() {
    const config = {
        max_position_size: parseFloat(document.getElementById('max-position').value),
        stop_loss_percentage: parseFloat(document.getElementById('stop-loss').value) / 100,
        take_profit_percentage: parseFloat(document.getElementById('take-profit').value) / 100,
    };
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Configuration saved successfully', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error saving configuration: ' + error.message, 'error');
    }
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