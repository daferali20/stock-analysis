/**
 * ملف JavaScript الرئيسي لتطبيق تحليل الأسهم
 * يعالج التفاعلات مع الواجهة الأمامية
 */

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة العناصر الأساسية
    initStockAnalysisApp();
});

function initStockAnalysisApp() {
    // عناصر DOM الرئيسية
    const elements = {
        stockForm: document.getElementById('stock-form'),
        symbolSelect: document.getElementById('symbol-select'),
        daysInput: document.getElementById('days-input'),
        deltaTable: document.getElementById('delta-table'),
        maChart: document.getElementById('ma-chart'),
        loadingIndicator: document.getElementById('loading-indicator'),
        errorContainer: document.getElementById('error-container')
    };

    // معالجة إرسال النموذج
    if (elements.stockForm) {
        elements.stockForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const symbol = elements.symbolSelect.value;
            const days = elements.daysInput.value || 365;
            fetchStockAnalysis(symbol, days);
        });
    }

    // معالجة تغيير الرمز
    if (elements.symbolSelect) {
        elements.symbolSelect.addEventListener('change', function() {
            const symbol = this.value;
            if (symbol) {
                fetchQuickStockData(symbol);
            }
        });
    }

    // معالجة الروابط في جدول الدلتا
    if (elements.deltaTable) {
        elements.deltaTable.addEventListener('click', function(e) {
            if (e.target.classList.contains('stock-link')) {
                e.preventDefault();
                const symbol = e.target.dataset.symbol;
                fetchStockAnalysis(symbol, 365);
            }
        });
    }
}

/**
 * جلب بيانات تحليل السهم
 */
async function fetchStockAnalysis(symbol, days) {
    try {
        showLoading(true);
        
        const response = await fetch(`/moving_avg?symbol=${symbol}&days=${days}`);
        
        if (!response.ok) {
            throw new Error('فشل في جلب البيانات');
        }
        
        const data = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(data, 'text/html');
        
        // تحديث قسم التحليل فقط
        const analysisSection = doc.querySelector('.analysis-container');
        if (analysisSection) {
            document.querySelector('.analysis-container').innerHTML = analysisSection.innerHTML;
            initChart(); // إعادة تهيئة الرسم البياني
        }
        
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

/**
 * جلب بيانات سريعة للسهم
 */
async function fetchQuickStockData(symbol) {
    try {
        const response = await fetch(`/get_stock_data?symbol=${symbol}`);
        
        if (!response.ok) {
            throw new Error('فشل في جلب البيانات السريعة');
        }
        
        const data = await response.json();
        
        if (data.status === 'success') {
            updateQuickView(data.data);
        } else {
            throw new Error(data.message || 'خطأ غير معروف');
        }
        
    } catch (error) {
        console.error('Error fetching quick data:', error);
    }
}

/**
 * تحديث العرض السريع للبيانات
 */
function updateQuickView(data) {
    const quickView = document.getElementById('quick-view');
    if (quickView) {
        quickView.innerHTML = `
            <div class="quick-info">
                <h3>${data.symbol}</h3>
                <p>السعر الحالي: $${data.current_price.toFixed(2)}</p>
                <p>MA 50: $${data.ma_50.toFixed(2)}</p>
                <p>MA 200: $${data.ma_200.toFixed(2)}</p>
            </div>
        `;
    }
}

/**
 * تهيئة الرسم البياني
 */
function initChart() {
    const chartDataElement = document.getElementById('chart-data');
    if (chartDataElement) {
        const chartData = JSON.parse(chartDataElement.textContent);
        renderMAChart(chartData);
    }
}

/**
 * عرض الرسم البياني للمتوسطات المتحركة
 */
function renderMAChart(data) {
    const ctx = document.getElementById('ma-chart');
    if (ctx && data) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [
                    {
                        label: 'سعر الإغلاق',
                        data: data.prices,
                        borderColor: '#3498db',
                        tension: 0.1
                    },
                    {
                        label: '50 يوم MA',
                        data: data.ma50,
                        borderColor: '#e74c3c',
                        borderDash: [5, 5],
                        tension: 0.1
                    },
                    {
                        label: '200 يوم MA',
                        data: data.ma200,
                        borderColor: '#2ecc71',
                        borderDash: [10, 5],
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'المتوسطات المتحركة'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'التاريخ'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'السعر'
                        }
                    }
                }
            }
        });
    }
}

/**
 * عرض مؤشر التحميل
 */
function showLoading(show) {
    const loader = document.getElementById('loading-indicator');
    if (loader) {
        loader.style.display = show ? 'block' : 'none';
    }
}

/**
 * عرض رسائل الخطأ
 */
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>خطأ!</strong> ${message}
            </div>
        `;
        errorContainer.style.display = 'block';
        
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
}

/**
 * تنسيق الأرقام
 */
function formatNumber(num) {
    return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}