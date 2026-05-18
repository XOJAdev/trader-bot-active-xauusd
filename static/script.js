async function updateDashboard() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'online') {
            document.getElementById('status-text').textContent = 'Live Trading';
            document.getElementById('status-badge').style.background = 'rgba(16, 185, 129, 0.1)';
            document.getElementById('status-badge').style.borderColor = 'rgba(16, 185, 129, 0.2)';
            document.getElementById('status-text').style.color = 'var(--green)';
            document.getElementById('status-dot').style.backgroundColor = 'var(--green)';
            document.getElementById('status-dot').style.boxShadow = '0 0 10px var(--green)';
            
            document.getElementById('val-balance').textContent = '$' + data.balance.toFixed(2);
            document.getElementById('val-equity').textContent = '$' + data.equity.toFixed(2);
            document.getElementById('val-margin').textContent = '$' + data.margin_free.toFixed(2);
            
            const profitEl = document.getElementById('val-profit');
            profitEl.textContent = (data.profit >= 0 ? '+$' : '-$') + Math.abs(data.profit).toFixed(2);
            profitEl.className = 'card-value ' + (data.profit >= 0 ? 'profit' : 'loss');

            // Bozor tahlilini yuklash
            const marketBox = document.getElementById('market-status-box');
            if (data.market) {
                const m = data.market;
                const trendColor = m.trend.includes("O'sish") ? "var(--green)" : (m.trend.includes("Tushish") ? "var(--red)" : "var(--gold)");
                const liqColor = (m.liquidity && m.liquidity.includes("Yuqori")) ? "var(--green)" : ((m.liquidity && m.liquidity.includes("Past")) ? "var(--red)" : "var(--gold)");
                
                marketBox.innerHTML = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.8rem;">
                        <div style="background: rgba(255,255,255,0.02); padding: 0.8rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.3rem; text-transform: uppercase;">Joriy Narx</div>
                            <div style="font-size: 1.5rem; font-weight: 800;">${m.price}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.02); padding: 0.8rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.3rem; text-transform: uppercase;">Trend & Likvidlik</div>
                            <div style="font-size: 1.1rem; font-weight: 800; color: ${trendColor}; margin-bottom: 0.2rem;">${m.trend}</div>
                            <div style="font-size: 0.85rem; font-weight: 600; color: ${liqColor};">${m.liquidity || 'N/A'}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.02); padding: 0.8rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.3rem; text-transform: uppercase;">AI Signal Bahosi (10 ball)</div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                                <span style="font-size: 0.9rem; font-weight: 600; color: var(--green);">BUY Score:</span>
                                <span style="font-size: 1.1rem; font-weight: 800; color: var(--green);">${m.buy_score !== undefined ? m.buy_score : '-'}/10</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 0.9rem; font-weight: 600; color: var(--red);">SELL Score:</span>
                                <span style="font-size: 1.1rem; font-weight: 800; color: var(--red);">${m.sell_score !== undefined ? m.sell_score : '-'}/10</span>
                            </div>
                        </div>
                        <div style="background: rgba(255,255,255,0.02); padding: 0.8rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.3rem; text-transform: uppercase;">Ko'rsatkichlar</div>
                            <div style="font-size: 0.85rem; font-weight: 600; display:flex; justify-content: space-between;"><span>EMA 50:</span> <span style="color:var(--text-main)">${m.ema50}</span></div>
                            <div style="font-size: 0.85rem; font-weight: 600; display:flex; justify-content: space-between;"><span>EMA 200:</span> <span style="color:var(--text-main)">${m.ema200}</span></div>
                            <div style="font-size: 0.85rem; font-weight: 600; display:flex; justify-content: space-between;"><span>Stoch %K:</span> <span style="color:${m.stoch_k > 80 ? 'var(--red)' : (m.stoch_k < 20 ? 'var(--green)' : 'var(--text-main)')}">${m.stoch_k}</span></div>
                            <div style="font-size: 0.85rem; font-weight: 600; display:flex; justify-content: space-between;"><span>ATR:</span> <span style="color:var(--text-main)">${m.atr}</span></div>
                        </div>
                    </div>
                    <div style="margin-top: 0.5rem; font-size: 0.75rem; color: var(--text-muted); text-align: right;">
                        ⏳ So'nggi tahlil vaqti: ${m.time}
                    </div>
                `;
            }

            const tbody = document.getElementById('positions-body');
            if (data.open_positions.length > 0) {
                tbody.innerHTML = '';
                data.open_positions.forEach(pos => {
                    const row = document.createElement('tr');
                    const typeClass = pos.type === 'BUY' ? 'type-buy' : 'type-sell';
                    const profitClass = pos.profit >= 0 ? 'profit' : 'loss';
                    
                    row.innerHTML = `
                        <td>#${pos.ticket}</td>
                        <td style="font-weight: 600;">XAUUSD</td>
                        <td><span class="${typeClass}">${pos.type}</span></td>
                        <td>${pos.volume}</td>
                        <td>${pos.price_open}</td>
                        <td>${pos.sl}</td>
                        <td>${pos.tp}</td>
                        <td class="profit-text ${profitClass}">${pos.profit > 0 ? '+' : ''}${pos.profit.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            } else {
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Hozirda ochiq pozitsiyalar yo\'q</td></tr>';
            }

            // Tarixni yuklash
            const hbody = document.getElementById('history-body');
            if (data.history && data.history.length > 0) {
                hbody.innerHTML = '';
                data.history.forEach(deal => {
                    const row = document.createElement('tr');
                    const typeClass = deal.type === 'BUY' ? 'type-buy' : 'type-sell';
                    const profitClass = deal.profit > 0 ? 'profit' : (deal.profit < 0 ? 'loss' : '');
                    const profitText = deal.profit > 0 ? `+${deal.profit.toFixed(2)}` : deal.profit.toFixed(2);
                    
                    row.innerHTML = `
                        <td>${deal.time}</td>
                        <td>#${deal.ticket}</td>
                        <td style="font-weight: 600;">${deal.entry}</td>
                        <td><span class="${typeClass}">${deal.type}</span></td>
                        <td>${deal.volume}</td>
                        <td>${deal.price}</td>
                        <td class="profit-text ${profitClass}">${profitText}</td>
                    `;
                    hbody.appendChild(row);
                });
            } else {
                hbody.innerHTML = '<tr><td colspan="7" class="empty-state">Hozircha tarixiy bitimlar mavjud emas</td></tr>';
            }
            
        } else {
            // Offline
            document.getElementById('status-text').textContent = 'Disconnected';
            document.getElementById('status-badge').style.background = 'rgba(239, 68, 68, 0.1)';
            document.getElementById('status-badge').style.borderColor = 'rgba(239, 68, 68, 0.2)';
            document.getElementById('status-text').style.color = 'var(--red)';
            document.getElementById('status-dot').style.backgroundColor = 'var(--red)';
            document.getElementById('status-dot').style.boxShadow = '0 0 10px var(--red)';
        }
    } catch (e) {
        console.error("Dashboard xatosi:", e);
    }
}

// Fetch every 2 seconds
setInterval(updateDashboard, 2000);
updateDashboard();

// Sozlamalarni yuklash
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        if (config) {
            document.getElementById('inp-lot').value = config.LOT || 0.01;
            document.getElementById('inp-sl-atr').value = config.SL_ATR_MULTIPLIER || 1.5;
            document.getElementById('inp-tp-atr').value = config.TP_ATR_MULTIPLIER || 2.5;
            document.getElementById('inp-active').checked = config.BOT_ACTIVE !== false;
            
            const autoRiskCheckbox = document.getElementById('inp-auto-risk');
            autoRiskCheckbox.checked = config.AI_AUTO_RISK === true;
            toggleInputs(config.AI_AUTO_RISK === true);
        }
    } catch (e) {
        console.error("Konfiguratsiyani yuklashda xatolik:", e);
    }
}

function toggleInputs(isAuto) {
    document.getElementById('inp-lot').disabled = isAuto;
    document.getElementById('inp-sl-atr').disabled = isAuto;
    document.getElementById('inp-tp-atr').disabled = isAuto;
    
    const opacity = isAuto ? '0.5' : '1';
    document.getElementById('inp-lot').style.opacity = opacity;
    document.getElementById('inp-sl-atr').style.opacity = opacity;
    document.getElementById('inp-tp-atr').style.opacity = opacity;
}

// Boshqaruv tugmalari
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();

    document.getElementById('btn-close-all').addEventListener('click', async () => {
        if (!confirm('Haqiqatan ham barcha ochiq pozitsiyalarni yopmoqchimisiz?')) return;
        
        try {
            const res = await fetch('/api/close_all', { method: 'POST' });
            const data = await res.json();
            alert(data.message || (data.error ? 'Xatolik: ' + data.error : 'Bajarildi'));
            updateDashboard();
        } catch (e) {
            alert('Xatolik yuz berdi: ' + e.message);
        }
    });

    document.getElementById('btn-close-profitable').addEventListener('click', async () => {
        if (!confirm('Faqat foydada bo\'lgan pozitsiyalarni yopmoqchimisiz?')) return;
        
        try {
            const res = await fetch('/api/close_profitable', { method: 'POST' });
            const data = await res.json();
            alert(data.message || (data.error ? 'Xatolik: ' + data.error : 'Bajarildi'));
            updateDashboard();
        } catch (e) {
            alert('Xatolik yuz berdi: ' + e.message);
        }
    });
    
    const sendManualTrade = async (type) => {
        if (!confirm(`Haqiqatan ham ${type.toUpperCase()} pozitsiyasini ochmoqchimisiz?`)) return;
        const lot = document.getElementById('inp-lot').value || 0.01;
        
        try {
            const res = await fetch('/api/trade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type: type, lot: lot })
            });
            const data = await res.json();
            alert(data.message || (data.error ? 'Xatolik: ' + data.error : 'Bajarildi'));
            updateDashboard();
        } catch (e) {
            alert('Xatolik yuz berdi: ' + e.message);
        }
    };

    document.getElementById('btn-buy-manual').addEventListener('click', () => sendManualTrade('buy'));
    document.getElementById('btn-sell-manual').addEventListener('click', () => sendManualTrade('sell'));

    document.getElementById('inp-auto-risk').addEventListener('change', (e) => {
        toggleInputs(e.target.checked);
    });

    document.getElementById('btn-save-config').addEventListener('click', async () => {
        const newConfig = {
            BOT_ACTIVE: document.getElementById('inp-active').checked,
            AI_AUTO_RISK: document.getElementById('inp-auto-risk').checked,
            LOT: parseFloat(document.getElementById('inp-lot').value),
            SL_ATR_MULTIPLIER: parseFloat(document.getElementById('inp-sl-atr').value),
            TP_ATR_MULTIPLIER: parseFloat(document.getElementById('inp-tp-atr').value)
        };

        try {
            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newConfig)
            });
            const data = await res.json();
            if (data.success) {
                const statusEl = document.getElementById('config-status');
                statusEl.style.display = 'block';
                setTimeout(() => statusEl.style.display = 'none', 3000);
            } else {
                alert('Xatolik: ' + data.error);
            }
        } catch (e) {
            alert('Xatolik yuz berdi: ' + e.message);
        }
    });
});
