#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: banhao@gmail.com
# Version: 2.0 (Integrated Grok AI)
# Issue Date: DECEMBER 27, 2025
# Release Note: Added AI analysis button and Grok API integration

from waitress import serve
from flask import Flask, request, jsonify, render_template
import ta as ta_lib
import os
import json
import requests
import pandas as pd
import pandas_ta as ta
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
SEC_URL = os.getenv('SEC_URL')
CRYPTO_URL = os.getenv('CRYPTO_URL')
FINANCIAL_API_KEY = os.getenv('FINANCIAL_API_KEY')
XAI_API_KEY = os.getenv('XAI_API_KEY')

# conf.get_default().region = "us"

# Function to fetch tickers from API
def fetch_tickers(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("tickers", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tickers from {url}: {e}")
        return []

# Fetch tickers
SEC_tickers = fetch_tickers(SEC_URL)
CRYPTO_tickers = fetch_tickers(CRYPTO_URL)

# HTML Template with Indicators Dropdown
index_html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEC & CRYPTO Tickers</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            height: 100vh; /* Full viewport height */
            overflow: hidden; /* Prevent body scrollbars */
            font-family: Arial, sans-serif;
        }}
        body {{
            display: flex;
            margin: 0;
            font-family: Arial, sans-serif;
        }}
        .sidebar {{
            width: 250px;
            background-color: #f4f4f4;
            padding: 20px;
            display: flex;
            z-index: 100;
            flex-direction: column;
            gap: 10px;
            box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
            overflow-y: auto; /* Scroll sidebar if content overflows */
        }}
        .content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            height: 100vh; /* Fill viewport height */
            box-sizing: border-box;
        }}
        #result {{
            min-height: 20px; /* Space for messages */
            margin-bottom: 10px;
        }}
        #chart {{
            flex: 1; /* Take remaining height in .content */
            width: 100%;
            min-height: 400px; /* Fallback for small screens */
        }}
        label {{
            font-weight: bold;
        }}
        select[multiple] {{
            height: auto;
            min-height: 120px;
            max-height: 240px;
        }}
        select, button, input {{
            width: 100%;
            padding: 8px;
            margin-top: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
            box-sizing: border-box;
            text-decoration: none;
            color: #007bff;
            cursor: pointer;
        }}
        button {{
            background-color: #007bff;
            color: white;
            cursor: pointer;
            border: none;
        }}
        button:hover:not(:disabled) {{
            background-color: #0056b3;
        }}
        button:disabled {{
            background-color: #cccccc;
            cursor: not-allowed;
        }}
        .label-container {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .info-icon {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 14px;
            height: 14px;
            background-color: #007bff;
            color: white;
            border-radius: 50%;
            font-size: 10px;
            font-weight: bold;
            text-align: center;
            cursor: help;
            position: relative;
        }}
        .tooltip {{
            visibility: hidden;
            width: 180px;
            background-color: #333;
            color: white;
            text-align: left;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            position: absolute;
            left: -100px;
            top: 50%;
            transform: translateX(-50%);
            margin-bottom: 5px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            opacity: 0;
            transition: opacity 0.2s;
        }}
        .info-icon:hover .tooltip,
        .info-icon:focus .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        .content {{
            z-index: 0;
        }}
        .disclaimer {{
            margin-top: 10px;
            padding: 10px;
            background-color: #fff;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 12px;
            line-height: 1.4;
        }}
        .disclaimer h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
        }}
        .disclaimer p {{
            margin: 5px 0;
        }}
        .disclaimer-checkbox {{
            display: flex;
            align-items: center;
            gap: 5px;
            margin-top: 10px;
        }}
        .disclaimer-checkbox input {{
            width: auto;
            margin: 0;
        }}
        .disclaimer-checkbox label {{
            font-size: 12px;
            font-family: Arial, sans-serif;
            font-weight: normal;
            color: #000;
        }}
        .disclaimer-checkbox a {{
            font-size: 12px;
            font-family: Arial, sans-serif;
            font-weight: normal;
            color: #007bff;
            text-decoration: underline;
            cursor: pointer;
        }}
        .disclaimer-checkbox a:hover {{
            color: #0056b3;
        }}
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 200;
            overflow: auto;
        }}
        .modal-content {{
            background-color: #fff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            width: 80%;
            max-width: 500px;
            max-height: 80vh;
            overflow-y: auto;
            font-size: 12px;
            line-height: 1.4;
        }}
        .modal-content h4 {{
            margin: 0 0 10px 0;
            font-size: 14px;
        }}
        .modal-content p {{
            margin: 5px 0;
        }}
        .modal-content button {{
            margin-top: 10px;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .modal-content button:hover {{
            background-color: #0056b3;
        }}
        #toggle-sidebar {{
            display: none;
            position: fixed;
            top: 10px;
            left: 10px;
            padding: 8px 16px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            z-index: 101;
        }}
        #toggle-sidebar:hover {{
            background-color: #0056b3;
        }}
        @media (max-width: 1400px) {{
            .sidebar {{
                position: fixed;
                top: 0;
                left: 0;
                height: 100vh;
                transform: translateX(-100%); /* Hidden by default on mobile */
            }}
            .sidebar.visible {{
                transform: translateX(0); /* Show when toggled */
            }}
            .content {{
                width: 100vw;
                padding: 10px;
            }}
            #chart {{
                height: calc(100vh - 50px); /* Adjust for toggle button and padding */
            }}
            #toggle-sidebar {{
                display: block;
            }}
            .modal-content {{
                width: 90%;
                margin: 10% auto;
            }}
        }}
        .loader {{
            border: 5px solid #f3f3f3;
            border-top: 5px solid #6366f1;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        pre {{
            background: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }}
        #grok-analysis-text {{
            white-space: pre-wrap;       /* Preserves line breaks but wraps long lines */
            word-wrap: break-word;       /* Breaks long words if needed */
            overflow-wrap: break-word;   /* Modern equivalent */
            font-family: inherit;        /* Uses normal font, not monospace */
            line-height: 1.6;
        }}
        .modal-content {{
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}
        #grok-ticker-title {{
            color: #4f46e5; /* indigo-600 */
        }}
    </style>
    <script>
        var tickers = {{
            "SEC": {SEC_tickers},
            "CRYPTO": {CRYPTO_tickers}
        }};
        function updateTickers() {{
            var index = document.getElementById("category").value;
            var companyDropdown = document.getElementById("tickers");
            var resultArea = document.getElementById("result");
            companyDropdown.innerHTML = "<option>Loading...</option>";
            if (index && tickers[index] && Array.isArray(tickers[index]) && tickers[index].length > 0) {{
                tickers[index].forEach(ticker => {{
                    var option = document.createElement("option");
                    option.value = ticker;
                    option.textContent = ticker;
                    companyDropdown.appendChild(option);
                }});
            }} else {{
                companyDropdown.innerHTML = "<option value=''>No tickers available</option>";
                if (!index) {{
                    resultArea.innerHTML = "Please select a category.";
                }} else {{
                    resultArea.innerHTML = "No tickers available for " + index + ". Try another category.";
                }}
            }}
        }}
        
        
        async function askGrok() {{
            const tickerSelect = document.getElementById('tickers');
            const ticker = tickerSelect.value;
            const category = document.getElementById('category').value;
            const aiBtn = document.getElementById('ai-btn');
            const modal = document.getElementById('grok-modal');
            const loading = document.getElementById('grok-loading');
            const result = document.getElementById('grok-result');
            const title = document.getElementById('grok-ticker-title');
            const text = document.getElementById('grok-analysis-text');
            
            // Improved validation: both category and a valid ticker must be selected
            if (!category) {{
                alert("⚠️ Please select a Category first.");
                return;
            }}
            if (!ticker || tickerSelect.selectedIndex === 0 || ticker === '' || ticker.includes('No tickers') || ticker.includes('Select a ticker')) {{
                alert("⚠️ Please select a valid Ticker after choosing a Category.");
                return;
            }}
            
            // Show modal and loading
            modal.style.display = "block";
            loading.classList.remove('hidden');
            result.classList.add('hidden');
            aiBtn.disabled = true;
        
            try {{
                const response = await fetch('/analyze_ai', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        ticker,
                        category
                    }})
                }});
                
                if (!response.ok) {{
                    const errorData = await response.json();
                    throw new Error(errorData.error || `Server error: ${{response.status}}`);
                }}
                
                const data = await response.json();
        
                if (data.error) {{
                    text.textContent = "Error: " + data.error;
                }} else {{
                    title.textContent = `${{data.ticker}} (${{data.category}})`;
                    text.textContent = data.analysis || "No analysis returned.";
                }}
        
                loading.classList.add('hidden');
                result.classList.remove('hidden');
        
            }} catch (e) {{
                console.error("Fetch error:", e);
                text.textContent = "Connection failed. Check your internet or server status.";
                loading.classList.add('hidden');
                result.classList.remove('hidden');
            }} finally {{
                aiBtn.disabled = false;
                aiBtn.innerText = "🚀 Analyze with Grok AI";
            }}
        }}

        function closeGrokModal() {{
            document.getElementById('grok-modal').style.display = "none";
        }}
    
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('grok-modal');
            if (event.target === modal) {{
                closeGrokModal();
            }}
        }};
        
        // Detect if the device is a mobile phone
        function isMobileDevice() {{
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 1400;
        }}

        // Toggle sidebar visibility
        function toggleSidebar() {{
            var sidebar = document.querySelector('.sidebar');
            var content = document.querySelector('.content');
            var toggleButton = document.getElementById('toggle-sidebar');
            if (sidebar.classList.contains('visible')) {{
                sidebar.classList.remove('visible');
                toggleButton.textContent = 'Show Sidebar';
            }} else {{
                sidebar.classList.add('visible');
                toggleButton.textContent = 'Hide Sidebar';
            }}
        }}

        // Initialize tickers dropdown, set default dates, and handle mobile layout
        document.addEventListener("DOMContentLoaded", function() {{
            // Set default dates
            const today = new Date();
            const oneYearAgo = new Date(today);
            oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
        
            // Format dates as YYYY-MM-DD
            const formatDate = (date) => {{
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                return `${{year}}-${{month}}-${{day}}`;
            }};
        
            document.getElementById("start_date").value = formatDate(oneYearAgo);
            document.getElementById("end_date").value = formatDate(today);
        
            // Initialize tickers dropdown
            updateTickers();
            // Disable SUBMIT button by default
            document.getElementById("SubmitButton").disabled = true;
            
            // Hide sidebar and show toggle button on mobile
            if (isMobileDevice()) {{
                document.querySelector('.sidebar').classList.remove('visible');
                document.getElementById('toggle-sidebar').style.display = 'block';
                document.getElementById('toggle-sidebar').textContent = 'Show Sidebar';
            }}
        }});

        function toggleSubmitButton() {{
            const checkbox = document.getElementById("disclaimer-checkbox");
            document.getElementById("SubmitButton").disabled = !checkbox.checked;
        }}
        
        function openDisclaimerModal() {{
            document.getElementById("disclaimer-modal").style.display = "block";
            document.getElementById("disclaimer-modal").focus();
        }}
        function closeDisclaimerModal() {{
            document.getElementById("disclaimer-modal").style.display = "none";
        }}
        // Close modal when clicking outside or pressing Esc
        window.onclick = function(event) {{
            const modal = document.getElementById("disclaimer-modal");
            if (event.target === modal) {{
                modal.style.display = "none";
            }}
        }};
        document.addEventListener("keydown", function(event) {{
            const modal = document.getElementById("disclaimer-modal");
            if (event.key === "Escape" && modal.style.display === "block") {{
                modal.style.display = "none";
            }}
        }});
        function openCryptoHeatmap() {{
            window.open('https://www.tradingview.com/heatmap/crypto/#%7B%22dataSource%22%3A%22Crypto%22%2C%22blockColor%22%3A%2224h_close_change%7C5%22%2C%22blockSize%22%3A%22market_cap_calc%22%2C%22grouping%22%3A%22no_group%22%7D', '_blank', 'width=1024,height=768,toolbar=no,location=no,status=no,menubar=no,resizable=yes');
        }}
        function openStockHeatmap() {{
            window.open('https://www.tradingview.com/heatmap/stock/#%7B%22dataSource%22%3A%22AllUSA%22%2C%22blockColor%22%3A%22change%22%2C%22blockSize%22%3A%22market_cap_basic%22%2C%22grouping%22%3A%22sector%22%7D', '_blank', 'width=1024,height=768,toolbar=no,location=no,status=no,menubar=no,resizable=yes');
        }}
        function OHLCprices() {{
            // Ensure sidebar is hidden and content is full-screen on mobile
            if (isMobileDevice()) {{
                var sidebar = document.querySelector('.sidebar');
                var toggleButton = document.getElementById('toggle-sidebar');
                sidebar.classList.remove('visible');
                toggleButton.textContent = 'Show Sidebar';
                toggleButton.style.display = 'block';
            }}
            var selectedTicker = document.getElementById("tickers").value;
            var selectedCategory = document.getElementById("category").value;
            var interval = document.getElementById("interval").value;
            var intervalMultiplier = document.getElementById("interval_multiplier").value;
            var startDate = document.getElementById("start_date").value;
            var endDate = document.getElementById("end_date").value;
            var bollingerDeltaWindow = document.getElementById("bollinger_delta_window").value;
            var indicatorsSelect = document.getElementById("indicators");
            var selectedIndicators = Array.from(indicatorsSelect.selectedOptions).map(option => option.value);
            var resultArea = document.getElementById("result");
            if (!selectedTicker || !selectedCategory || !interval || !intervalMultiplier || !startDate || !endDate) {{
                alert("⚠️ Please fill all fields before submitting.");
                return;
            }}
            const endpoint = selectedCategory === "CRYPTO" ? "/crypto/prices" : "/prices";
            resultArea.innerHTML = "Loading...";
            document.getElementById('chart').innerHTML = ""; // Clear the chart while loading
            fetch(`${{endpoint}}?ticker=${{selectedTicker}}&category=${{selectedCategory}}&interval=${{interval}}&interval_multiplier=${{intervalMultiplier}}&start_date=${{startDate}}&end_date=${{endDate}}&bollinger_delta_window=${{bollingerDeltaWindow}}&indicators=${{selectedIndicators.join(',')}}`)
                .then(response => {{
                    if (!response.ok) {{
                        return response.json().then(err => {{ throw new Error(err.error || `HTTP error! status: ${{response.status}}`); }});
                    }}
                    return response.json();
                }})
                .then(data => {{
                    resultArea.innerHTML = ""; // Clear the loading message
                    if (!data || data.length === 0) {{
                        document.getElementById('chart').innerHTML = "No data available.";
                        return;
                    }}
                    data.sort((a, b) => new Date(a.time) - new Date(b.time));
                    
                    // Candlestick trace
                    const traceCandles = {{
                        x: data.map(d => d.time),
                        open: data.map(d => d.open),
                        high: data.map(d => d.high),
                        low: data.map(d => d.low),
                        close: data.map(d => d.close),
                        type: 'candlestick',
                        name: 'Price',
                        yaxis: 'y'
                    }};

                    // Volume trace (subplot)
                    const traceVolume = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d.volume || 0),
                        type: 'bar',
                        name: 'Volume',
                        marker: {{ color: 'rgba(128,128,128,0.5)' }},
                        yaxis: 'y2'
                    }};

                    // MACD traces
                    const traceMACD = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d['MACD_12_26_9']),
                        mode: 'lines',
                        name: 'MACD',
                        line: {{ color: 'blue' }},
                        yaxis: 'y3'
                    }};
                    const traceMACDSignal = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d['MACDs_12_26_9']),
                        mode: 'lines',
                        name: 'MACD Signal',
                        line: {{ color: 'orange' }},
                         yaxis: 'y3'
                    }};
                    const traceMACDHist = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d['MACDh_12_26_9']),
                        type: 'bar',
                        name: 'MACD Histogram',
                        marker: {{ color: 'green' }},
                         yaxis: 'y3'
                    }};

                    // Add Bollinger Bands traces
                    const traceUpper = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d['BBU_10_2.0']),
                        mode: 'lines',
                        name: 'Upper Band',
                        line: {{ color: 'rgba(255,0,0,0.5)' }},
                        yaxis: 'y',
                        hoverinfo: 'none' // Disable tooltip
                    }};
                    const traceLower = {{
                        x: data.map(d => d.time),
                        y: data.map(d => d['BBL_10_2.0']),
                        mode: 'lines',
                        name: 'Lower Band',
                        line: {{ color: 'rgba(0,0,255,0.5)' }},
                        yaxis: 'y',
                        hoverinfo: 'none' // Disable tooltip
                    }};

                    // Initialize traces array with guaranteed traces
                    let traces = [
                        traceCandles,
                        traceVolume,
                        traceMACD,
                        traceMACDSignal,
                        traceMACDHist,
                        traceUpper,
                        traceLower
                    ];

                    // Buy Signals
                    const buySignals = data.filter(d => d.Buy_Signal_Price !== null && d.Buy_Signal_Price !== undefined);
                    if (buySignals.length > 0) {{
                        const traceBuy = {{
                            x: buySignals.map(d => d.time),
                            y: buySignals.map(d => d['BBL_10_2.0'] * 0.97),
                            mode: 'markers',
                            marker: {{
                                symbol: 'triangle-up',
                                size: 12,
                                color: 'green'
                            }},
                            hovertext: buySignals.map(d => `BUY AT ${{new Date(d.time).toLocaleString()}}`),
                            hoverinfo: 'text',
                            name: 'Buy Signal',
                            yaxis: 'y'
                        }};
                        traces.push(traceBuy);
                    }}

                    // Sell Signals
                    const sellSignals = data.filter(d => d.Sell_Signal_Price !== null && d.Sell_Signal_Price !== undefined);
                    if (sellSignals.length > 0) {{
                        const traceSell = {{
                            x: sellSignals.map(d => d.time),
                            y: sellSignals.map(d => d['BBU_10_2.0'] * 1.03),
                            mode: 'markers',
                            marker: {{
                                symbol: 'triangle-down',
                                size: 12,
                                color: 'red'
                            }},
                            hovertext: sellSignals.map(d => `SELL AT ${{new Date(d.time).toLocaleString()}}`),
                            hoverinfo: 'text',
                            name: 'Sell Signal',
                            yaxis: 'y'
                        }};
                        traces.push(traceSell);
                    }}

                    // Close Signals
                    const closeSignals = data.filter(d => d.Close_Signal_Price !== null && d.Close_Signal_Price !== undefined);
                    if (closeSignals.length > 0) {{
                        const traceClose = {{
                            x: closeSignals.map(d => d.time),
                            y: closeSignals.map(d => d.Close_Signal_Price),
                            mode: 'markers',
                            marker: {{
                                symbol: 'circle',
                                size: 12,
                                color: 'black'
                            }},
                            hovertext: closeSignals.map(d => `CLOSE AT ${{new Date(d.time).toLocaleString()}}`),
                            hoverinfo: 'text',
                            name: 'Close Signal',
                            yaxis: 'y'
                        }};
                        traces.push(traceClose);
                    }}
                    
                    // Define layout with fixed subplot order: Price → Volume → MACD
                    let layout = {{
                        title: `${{selectedTicker}} Price with Indicators`,
                        xaxis: {{ type: 'date', rangeslider: {{ visible: false }}, domain: [0, 1] }},
                        yaxis: {{ title: 'Price (USD)', domain: [0.4, 1] }},      // Main chart (Price, Bollinger Bands)
                        yaxis2: {{ title: 'Volume', domain: [0.3, 0.4], anchor: 'x' }},  // Volume subplot
                        yaxis3: {{ title: 'MACD', domain: [0.2, 0.3], anchor: 'x' }},    // MACD subplot
                        margin: {{ t: 50, b: 50, l: 50, r: 50 }},
                        showlegend: true,
                        legend: {{ x: 1, y: 1 }}
                    }};
                    
                    // Counter for additional y-axes
                    let yAxisCounter = 4;

                    // Add EMA_10 if selected
                    if (selectedIndicators.includes('EMA_10')) {{
                        const traceEMA_10 = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['EMA_10']),
                            mode: 'lines',
                            name: 'EMA_10',
                            line: {{ color: 'gold' }},
                            yaxis: 'y',
                            hoverinfo: 'none' // Disable tooltip
                        }};
                        traces.push(traceEMA_10);
                    }}
                    
                    // Add EMA_20 if selected
                    if (selectedIndicators.includes('EMA_20')) {{
                        const traceEMA_20 = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['EMA_20']),
                            mode: 'lines',
                            name: 'EMA_20',
                            line: {{ color: 'cyan' }},
                            yaxis: 'y',
                            hoverinfo: 'none' // Disable tooltip
                        }};
                        traces.push(traceEMA_20);
                    }}
                    
                    // Add EMA_50 if selected
                    if (selectedIndicators.includes('EMA_50')) {{
                        const traceEMA_50 = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['EMA_50']),
                            mode: 'lines',
                            name: 'EMA_50',
                            line: {{ color: 'indigo' }},
                            yaxis: 'y',
                            hoverinfo: 'none' // Disable tooltip
                        }};
                        traces.push(traceEMA_50);
                    }}
                    
                    // Add SMA if selected
                    if (selectedIndicators.includes('sma')) {{
                        const traceSMA = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['SMA_20']),
                            mode: 'lines',
                            name: 'SMA',
                            line: {{ color: 'magenta' }},
                            yaxis: 'y',
                            hoverinfo: 'none' // Disable tooltip
                        }};
                        traces.push(traceSMA);
                    }}

                    // Add RSI if selected
                    if (selectedIndicators.includes('rsi')) {{
                        const traceRSI = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['RSI_14']),
                            mode: 'lines',
                            name: 'RSI',
                            line: {{ color: 'purple' }},
                            yaxis: `y${{yAxisCounter}}`
                        }};
                        traces.push(traceRSI);
                        layout[`yaxis${{yAxisCounter}}`] = {{
                            title: 'RSI',
                            domain: [0.1, 0.2],
                            anchor: 'x',
                            range: [0, 100]
                        }};
                        yAxisCounter++;
                    }}

                    // Add STOCH if selected
                    if (selectedIndicators.includes('stoch')) {{
                        const traceStochK = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['STOCHk_14_3_3']),
                            mode: 'lines',
                            name: 'Stochastic %K',
                            line: {{ color: 'blue' }},
                            yaxis: `y${{yAxisCounter}}`
                        }};
                        const traceStochD = {{
                            x: data.map(d => d.time),
                            y: data.map(d => d['STOCHd_14_3_3']),
                            mode: 'lines',
                            name: 'Stochastic %D',
                            line: {{ color: 'red' }},
                            yaxis: `y${{yAxisCounter}}`
                        }};
                        traces.push(traceStochK, traceStochD);
                        layout[`yaxis${{yAxisCounter}}`] = {{
                            title: 'Stochastic',
                            //domain: [yAxisCounter === 4 ? 0.0 : (layout[`yaxis${{yAxisCounter-1}}`].domain[0] - 0.1), yAxisCounter === 4 ? 0.1 : layout[`yaxis${{yAxisCounter-1}}`].domain[0]],
                            domain: [0.0, 0.1],
                            anchor: 'x',
                            range: [0, 100]
                        }};
                        yAxisCounter++;
                    }}

                    // Plot the chart
                    document.getElementById('chart').innerHTML = "";
                    Plotly.newPlot('chart', traces, layout);
                }})
                .catch(error => {{
                    console.error("Error fetching OHLC data:", error);
                    resultArea.innerHTML = "❌ " + error.message;
                    document.getElementById('chart').innerHTML = ""; // Clear the chart on error
                }});
        }}
    </script>
</head>
<body>
<div class="sidebar">
    <label for="category">Category:</label>
    <select id="category" onchange="updateTickers()">
        <option value="">Select...</option>
        <option value="SEC">SEC</option>
        <option value="CRYPTO">CRYPTO</option>
    </select>
    <label for="tickers">Tickers:</label>
    <select id="tickers">
        <option>Select a ticker...</option>
    </select>
    <label for="interval">Interval:</label>
    <select id="interval">
        <option value="second">Second</option>
        <option value="minute">Minute</option>
        <option value="day" selected>Day</option>
        <option value="week">Week</option>
        <option value="month">Month</option>
        <option value="year">Year</option>
    </select>
    <label for="interval_multiplier">Interval Multiplier:</label>
    <input type="number" id="interval_multiplier" min="1" step="1" value="1">
    <label for="start_date">Start Date:</label>
    <input type="date" id="start_date">
    <label for="end_date">End Date:</label>
    <input type="date" id="end_date">
    <label for="indicators">Indicators:</label>
    <select id="indicators" multiple>
        <option value="EMA_10">EMA_10</option>
        <option value="EMA_20">EMA_20</option>
        <option value="EMA_50">EMA_50</option>
        <option value="sma">SMA</option>
        <option value="rsi">RSI</option>
        <option value="stoch">Stochastic</option>
    </select>
    <div class="label-container">
        <label for="bollinger_delta_window">BOLLINGER DELTA WINDOW:</label>
        <span class="info-icon" tabindex="0">i
        <span class="tooltip">Adjust the window value may affect the calculation of the "BUY", "SELL" and "CLOSE" signs.</span>
        </span>
    </div>
    <input type="number" id="bollinger_delta_window" min="1" step="1" value="10">
    <div class="disclaimer-checkbox">
        <input type="checkbox" id="disclaimer-checkbox" onchange="toggleSubmitButton()">
        <label for="disclaimer-checkbox">I agree to the </label>
        <a href="javascript:void(0)" onclick="openDisclaimerModal()">Liability Disclaimer</a>
    </div>
    <button id="SubmitButton" onclick="OHLCprices()">SUBMIT</button>
    <button id="ai-btn" onclick="askGrok()" class="w-full bg-indigo-600 text-white p-3 rounded hover:bg-indigo-700 flex items-center justify-center font-semibold">
    <span>🚀 Analyze with Grok AI</span>
    </button>
    <!-- Grok Analysis Modal -->
    <div id="grok-modal" class="modal">
        <div class="modal-content" style="max-width: 700px; width: 90%;">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-xl font-bold">Grok AI Analysis</h3>
                <button onclick="closeGrokModal()" class="text-2xl text-gray-600 hover:text-gray-900">&times;</button>
            </div>
            <div id="grok-loading" class="text-center py-8">
                <p class="text-lg">Consulting Grok AI...</p>
                <div class="loader mt-4"></div>
            </div>
            <div id="grok-result" class="hidden">
                <h4 id="grok-ticker-title" class="text-lg font-semibold mb-3 text-indigo-700"></h4>
                <div id="grok-analysis-text" class="text-sm leading-relaxed overflow-y-auto bg-gray-50 p-5 rounded-lg border border-gray-200 mb-4" style="white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word;">
                    <!-- Analysis text here -->
                </div>
            
                <div id="grok-suggestions" class="space-y-2">
                    <!-- Suggested question buttons will appear here -->
                </div>
            
                <div class="mt-6 text-right">
                    <button onclick="closeGrokModal()" class="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700">
                        Close
                    </button>
                </div>
            </div>
        </div>
    </div>
    <a class="heatmap-link" href="javascript:void(0)" onclick="openStockHeatmap()">Stock Heatmap</a>
    <a class="heatmap-link" href="javascript:void(0)" onclick="openCryptoHeatmap()">Crypto Heatmap</a>
    <div >
        <label style="font-size: 12px; font-family: Arial, sans-serif;">data source "financialdatasets.ai"</label>
    </div>
</div>
<div class="content">
    <button id="toggle-sidebar" onclick="toggleSidebar()">Show Sidebar</button>                                                                           
    <div id="result"></div>
    <div id="chart"></div>
</div>
<div id="disclaimer-modal" class="modal">
    <div class="modal-content">
        <h4>Liability Disclaimer</h4>
        <p><strong>Important Notice – Please Read Carefully</strong></p>
        <p>The information and signals provided by this application are for informational and educational purposes only and do not constitute financial, investment, or trading advice. The “Buy” and “Sell” indicators are generated based on algorithmic analysis and do not guarantee any specific outcome or return.</p>
        <p>You acknowledge and agree that:</p>
        <ul>
            <li>All investment decisions you make are at your own risk and discretion.</li>
            <li>You are solely responsible for any profits or losses resulting from your use of this application.</li>
            <li>The creator(s), developer(s), or distributor(s) of this application shall not be held liable for any financial loss, damages, or other consequences arising directly or indirectly from the use of, reliance upon, or interpretation of the content, features, or functionality of this application.</li>
        </ul>
        <p>By using this application, you expressly waive any and all claims against the developer(s), owner(s), or affiliates of this application for any loss or damage of any kind.</p>
        <p>If you are unsure about any financial decision, please consult a licensed financial advisor.</p>
        <button onclick="closeDisclaimerModal()">Close</button>
    </div>
</div>
</body>
</html>
"""

# Generate index.html
index_html = index_html_template.format(
    SEC_tickers=json.dumps(SEC_tickers),
    CRYPTO_tickers=json.dumps(CRYPTO_tickers)
)

# Write the file
with open("./templates/index.html", "w", encoding="utf-8") as file:
    file.write(index_html)

print("index.html file has been created successfully.")

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session security

# Helper function to fetch OHLC prices
def OHLC_PRICES(category, ticker, interval, interval_multiplier, start_date, end_date):
    if category == "SEC":
        url = "https://api.financialdatasets.ai/prices"
    elif category == "CRYPTO":
        url = "https://api.financialdatasets.ai/crypto/prices"
    else:
        return {"error": "Invalid category"}
    querystring = {
        "limit": "5000",
        "ticker": ticker,
        "interval": interval,
        "interval_multiplier": interval_multiplier,
        "start_date": start_date,
        "end_date": end_date
    }
    headers = {"X-API-KEY": FINANCIAL_API_KEY}
    print(f"Calling API: {url} with params: {querystring}")
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        print(f"API response status: {response.status_code}")
        data = response.json()
        # print(f"API response: {data}")
        # Check if the API response indicates the ticker is invalid
        if "error" in data and "not found" in data["error"].lower():
            return {"error": f"Ticker {ticker if category == 'CRYPTO' else ticker} data does not exist"}
        return data
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")
        # Check if the error indicates the ticker is invalid (e.g., 404 Not Found)
        if "404" in str(e) or "not found" in str(e).lower():
            return {"error": f"Ticker {ticker if category == 'CRYPTO' else ticker} data does not exist"}
        return {"error": str(e)}

# Helper function to calculate Bollinger Delta
def BOLLINGER_DELTA(window, serial_data):
    BOLLINGER_DELTA = []
    i = 0
    while i < len(serial_data):
        BOLLINGER_DELTA.append(serial_data['BBU_10_2.0'][i] - serial_data['BBL_10_2.0'][i])
        i += 1
    serial_data['BOLLINGER_DELTA'] = BOLLINGER_DELTA
    i = len(serial_data)
    while i >= (len(serial_data) - np.count_nonzero(~np.isnan(serial_data['BOLLINGER_DELTA'])) + window):
        if pd.notna(serial_data['BOLLINGER_DELTA'][i-1]):
            serial_data.iloc[i-window:i, serial_data.columns.get_loc('BOLLINGER_DELTA_SQUARE')] = serial_data['BOLLINGER_DELTA'].iloc[i-window:i] ** 2
            MAX_DELTA_SQUARE = serial_data['BOLLINGER_DELTA_SQUARE'].iloc[i-window:i].max()
            MIN_DELTA_SQUARE = serial_data['BOLLINGER_DELTA_SQUARE'].iloc[i-window:i].min()
            if (MAX_DELTA_SQUARE - MIN_DELTA_SQUARE) != 0:
                K = 100 / (MAX_DELTA_SQUARE - MIN_DELTA_SQUARE)
                serial_data.iloc[i-window:i, serial_data.columns.get_loc('BOLLINGER_DELTA_Indicator')] = (serial_data['BOLLINGER_DELTA_SQUARE'].iloc[i-window:i] - MIN_DELTA_SQUARE) * K
            else:
                serial_data.iloc[i-window:i, serial_data.columns.get_loc('BOLLINGER_DELTA_Indicator')] = (serial_data['BOLLINGER_DELTA_SQUARE'].iloc[i-window:i] - MIN_DELTA_SQUARE) * 0
        i -= 1
    return serial_data

def Signal_Buy_Sell(serial_data):
    sigBuy = []
    sigSell = []
    sigClose = []
    flag = 0
    stop_loss_price = 0
    sigBuy.append(np.nan)
    sigSell.append(np.nan)
    sigClose.append(np.nan)
    serial_data = serial_data.set_index('time')
    for i in list(serial_data.index)[1:] :
        if np.isnan(serial_data['BOLLINGER_DELTA_Indicator'][i]):
            sigBuy.append(np.nan)
            sigSell.append(np.nan)
            sigClose.append(np.nan)
        else:
            if (flag == 0 or flag == -1) and serial_data['BOLLINGER_DELTA_Indicator'][i] == 100 and serial_data['MACD_DIFF'][i] >= 0 and float(serial_data['close'][i]) > float(serial_data['open'][i]) and float(serial_data['open'][i]) > serial_data['EMA_20'][i]:
                sigBuy.append(float(serial_data['low'][i]))
                Buy_Signal_date = i
                cost_price = float((serial_data['open'][i] + serial_data['close'][i])/2)
                stop_loss_price = cost_price * 0.8
                sigSell.append(np.nan)
                sigClose.append(np.nan)
                flag = 1
            elif (flag == 0 or flag == 1) and serial_data['BOLLINGER_DELTA_Indicator'][i] == 100 and serial_data['MACD_DIFF'][i] <= 0 and float(serial_data['close'][i]) < float(serial_data['open'][i]) and float(serial_data['open'][i]) < serial_data['EMA_20'][i]:
                sigSell.append(float(serial_data['high'][i]))
                Sell_Signal_date = i
                cost_price = float((serial_data['open'][i] + serial_data['close'][i])/2)
                stop_loss_price = cost_price * (2 - 0.8)
                sigBuy.append(np.nan)
                sigClose.append(np.nan)
                flag = -1
            else:
                if flag == 1 and float(serial_data['close'][i]) <= float(stop_loss_price):
                    sigBuy.append(np.nan)
                    sigSell.append(np.nan)
                    sigClose.append(float(serial_data['high'][i]))
                    flag = 0
                elif flag == -1 and float(serial_data['close'][i]) >= float(stop_loss_price):
                    sigBuy.append(np.nan)
                    sigSell.append(np.nan)
                    sigClose.append(float(serial_data['low'][i]))
                    flag = 0
                else:
                    sigBuy.append(np.nan)
                    sigSell.append(np.nan)
                    sigClose.append(np.nan)
    return(sigBuy, sigSell, sigClose)

# Helper function to process OHLC data
def process_ohlc_data(data, category, ticker, indicators, bollinger_delta_window):
    if category == "CRYPTO":
#        df = data.get("prices", {}).get("prices", [])
        df = data.get("prices", [])
    else:  # SEC
        df = data.get("prices", [])
    print(f"Extracted prices: {df[:2]}")
    print(f"Number of price rows: {len(df)}")
    if not df:
        return None, {"error": f"Ticker {ticker} data does not exist"}
    if len(df) < 10:
        return None, {"error": f"Not enough data points for indicators (got {len(df)}, need at least 10)"}
    # Convert to DataFrame
    df = pd.DataFrame(df)
    print(f"DataFrame columns: {df.columns.tolist()}")
    print(f"Sample data (first 2 rows):\n{df.head(2)}")
    # Handle different column names for closing price
    possible_close_columns = ['close', 'price', 'last_price', 'close_price', 'value']
    close_column = None
    for col in possible_close_columns:
        if col in df.columns:
            close_column = col
            break
    if close_column:
        if close_column != 'close':
            df.rename(columns={close_column: 'close'}, inplace=True)
            print(f"Renamed '{close_column}' column to 'close'")
    else:
        return None, {"error": f"Missing closing price column. Expected one of {possible_close_columns}"}
    # Ensure 'close' column is numeric
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    if df['close'].isna().all():
        return None, {"error": "All 'close' values are invalid or missing"}
    # Check for sufficient non-NaN values
    if df['close'].dropna().count() < 10:
        return None, {"error": f"Not enough valid 'close' values for indicators (got {df['close'].dropna().count()}, need at least 10)"}
    # Calculate selected indicators
    df.ta.bbands(close='close', length=10, std=2.0, append=True)
    # Calculate Bollinger Delta if Bollinger Bands are selected
    df['BOLLINGER_DELTA_SQUARE'] = np.nan
    df['BOLLINGER_DELTA_Indicator'] = np.nan
    df = BOLLINGER_DELTA(bollinger_delta_window, df)
    df.ta.macd(close='close', fast=12, slow=26, signal=9, append=True)
    df['MACD_DIFF'] = (ta_lib.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9, fillna=False)).macd_diff()
    df.ta.ema(close='close', length=10, append=True)
    df.ta.ema(close='close', length=20, append=True)
    df.ta.ema(close='close', length=50, append=True)
    # print(f"After BOLLINGER_DELTA:\n{df[['BOLLINGER_DELTA', 'BOLLINGER_DELTA_SQUARE', 'BOLLINGER_DELTA_Indicator']].head(2)}")
    if 'rsi' in indicators:
        df.ta.rsi(close='close', length=14, append=True)
        # print(f"After RSI calculation:\n{df[['close', 'RSI_14']].head(2)}")
    if 'sma' in indicators:
        df.ta.sma(close='close', length=20, append=True)
    if 'stoch' in indicators:
        df.ta.stoch(high='high', low='low', close='close', append=True)
    # Keep only rows with valid data
    # df = df.dropna(subset=['BBU_10_2.0', 'BBL_10_2.0'])
    print(f"Rows after dropna: {len(df)}")
    if len(df) == 0:
        return None, {"error": "No valid data after indicator calculations"}
    # Convert to JSON-serializable format
    buy_sell = Signal_Buy_Sell(df)
    df['Buy_Signal_Price'] = buy_sell[0]
    df['Sell_Signal_Price'] = buy_sell[1]
    df['Close_Signal_Price'] = buy_sell[2]
    serial_data = df.replace({np.nan: None}).to_dict(orient="records")
    return serial_data, None

# Serve the HTML page
@app.route("/")
def index():
    return render_template("index.html")


# Grok AI Analysis endpoint
@app.route("/analyze_ai", methods=["POST"])
def analyze_ai():
    if not XAI_API_KEY:
        return jsonify({"error": "Grok API key not configured"}), 500

    data = request.json
    ticker = data.get('ticker')
    category = data.get('category')

    if not ticker or not category:
        return jsonify({"error": "Ticker and category required"}), 400

    category_name = "Stock" if category == "SEC" else "Cryptocurrency"
    
    model = "grok-4-1-fast-reasoning"   # ← This is key for speed
    
    prompt = f"""
    You are Grok, a maximally truth-seeking AI built by xAI.
    Analyze the {category_name.lower()} with ticker '{ticker}' as of late 2025.
    Provide:
    1. A brief overview of what this asset is.
    2. Current market sentiment and key recent trends.
    3. Potential risks.
    4. A clear recommendation: Buy, Hold, or Sell — with concise reasoning.
    Be professional and insightful. Provide as much detail as needed for a complete analysis.
    """

    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 2048
            },
            timeout=60
        )
        # Log for debugging
        print(f"Grok API status: {response.status_code}")
        print(f"Grok API raw response: {response.text[:500]}...")  # First 500 chars for safety
        
        if response.status_code == 403:
            return jsonify({"error": "Invalid or unauthorized API key"}), 500
        if response.status_code == 429:
            return jsonify({"error": "Rate limited. Please wait a moment and try again."}), 429
        if response.status_code == 404:
            return jsonify({"error": f"Model '{model}' not found. Check available models at x.ai/api"}), 500
        
        response.raise_for_status()
        result = response.json()
        
        full_text = result["choices"][0]["message"]["content"].strip()

        return jsonify({
            "ticker": ticker,
            "category": category_name,
            "analysis": full_text
        })

    except requests.exceptions.Timeout:
        return jsonify({"error": "Grok is taking too long to respond. Please try again in a few seconds."}), 504
    except requests.exceptions.RequestException as e:
        print(f"Grok network error: {e}")
        return jsonify({"error": "Cannot reach Grok AI right now: {str(e)}. Please try again."}), 503
    except ValueError:  # Invalid JSON
        print(f"Invalid response from Grok: {response.text}")
        return jsonify({"error": "Grok returned invalid data. Try again."}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Analysis failed. Please try again."}), 500


# API route to get OHLC prices (for both SEC and CRYPTO)
@app.route("/prices", methods=["GET"])
@app.route("/crypto/prices", methods=["GET"])
def get_ohlc_prices():
    ticker = request.args.get("ticker")
    category = request.args.get("category")
    interval = request.args.get("interval")
    interval_multiplier = request.args.get("interval_multiplier")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    bollinger_delta_window = int(request.args.get("bollinger_delta_window"))
    indicators = request.args.get("indicators", "").split(",") if request.args.get("indicators") else []

    # Validate query parameters
    if not all([ticker, category, interval, interval_multiplier, start_date, end_date]):
        return jsonify({"error": "All fields are required"}), 400

    # Validate category
    if category not in ["SEC", "CRYPTO"]:
        return jsonify({"error": "Invalid category. Must be 'SEC' or 'CRYPTO'"}), 400

    # Validate interval
    valid_intervals = ["second", "minute", "day", "week", "month", "year"]
    if interval not in valid_intervals:
        return jsonify({"error": f"Invalid interval. Must be one of {valid_intervals}"}), 400

    # Validate interval multiplier
    try:
        interval_multiplier = int(interval_multiplier)
        if interval_multiplier < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Interval multiplier must be a positive integer"}), 400

    # Validate and adjust dates
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if start_dt >= end_dt:
        return jsonify({"error": "Start date must be before end date"}), 400

    # Adjust end_date to avoid future dates
    current_date = datetime.now().date()
    end_dt_date = end_dt.date()
    if end_dt_date > current_date:
        end_date = current_date.strftime("%Y-%m-%d")
        print(f"Adjusted end_date to current date: {end_date}")

    # Ensure at least 30 days of data to get enough points
    date_range_days = (end_dt - start_dt).days
    if date_range_days < 30:
        start_date = (end_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        print(f"Adjusted start_date to ensure enough data: {start_date}")

    # Fetch data from API
    data = OHLC_PRICES(category, ticker, interval, interval_multiplier, start_date, end_date)
    if "error" in data:
        return jsonify({"error": data["error"]}), 400 if "data does not exist" in data["error"] else 500

    # Process the data with selected indicators
    serial_data, error = process_ohlc_data(data, category, ticker, indicators, bollinger_delta_window)
    if error:
        return jsonify(error), 400

    return jsonify(serial_data)

# Function to start ngrok
#def start_ngrok():
#    global webhook_url
#    try:
#        # Terminate any existing tunnels
#        ngrok.kill()
#        # Start new tunnel
#        tunnel = ngrok.connect(5000, bind_tls=True)  # Ensure HTTPS
#        webhook_url = tunnel.public_url
#        print(f"Ngrok tunnel started: {webhook_url}")
#        return webhook_url
#    except Exception as e:
#        print(f"Failed to start ngrok: {e}")
#        return None

if __name__ == "__main__":
    #serve(app, host="127.0.0.1", port=5000)                   # PROD mode
    app.run(host="0.0.0.0", port=5000, debug=True)           # DEV mode
    # webhook_url = start_ngrok()
    # if webhook_url:
    #     from waitress import serve
    #     serve(app, host="0.0.0.0", port=5000)
    # else:
    #     print("Could not start ngrok. Running locally only.")
    #     serve(app, host="localhost", port=5000)
    #     # app.run(host="localhost", port=5000, debug=False)
