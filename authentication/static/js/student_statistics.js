document.addEventListener("DOMContentLoaded", function () {
    /*statistics*/   
    // Get the chart container element
    const BarChart = document.getElementById('Chart');

    // Get the chart type buttons
    const barChartBtn = document.querySelector('.BarChart');
    const lineChartBtn = document.querySelector('.LineChart');
    const pieChartBtn = document.querySelector('.PieChart');
    
    // Define the chart data
    const chartData = {
    labels: ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'],
    datasets: [{
        label: 'Attendance',
        data: [12, 19, 28, 25, 12, 23, 19, 13, 25, 22, 13, 19],
        backgroundColor: [
        'rgba(255, 99, 132, 0.2)', // JAN
        'rgba(54, 162, 235, 0.2)', // FEB
        'rgba(255, 206, 86, 0.2)', // MAR
        'rgba(75, 192, 192, 0.2)', // APR
        'rgba(153, 102, 255, 0.2)', // MAY
        'rgba(255, 159, 64, 0.2)', // JUN
        'rgba(255, 99, 132, 0.2)', // JUL
        'rgba(54, 162, 235, 0.2)', // AUG
        'rgba(255, 206, 86, 0.2)', // SEP
        'rgba(75, 192, 192, 0.2)', // OCT
        'rgba(153, 102, 255, 0.2)', // NOV
        'rgba(255, 159, 64, 0.2)', // DEC
        ],
        borderColor: [
        'rgba(255, 99, 132, 1)', // JAN
        'rgba(54, 162, 235, 1)', // FEB
        'rgba(255, 206, 86, 1)', // MAR
        'rgba(75, 192, 192, 1)', // APR
        'rgba(153, 102, 255, 1)', // MAY
        'rgba(255, 159, 64, 1)', // JUN
        'rgba(255, 99, 132, 1)', // JUL
        'rgba(54, 162, 235, 1)', // AUG
        'rgba(255, 206, 86, 1)', // SEP
        'rgba(75, 192, 192, 1)', // OCT
        'rgba(153, 102, 255, 1)', // NOV
        'rgba(255, 159, 64, 1)', // DEC
        ],
        borderWidth: 1,
        borderRadius: 5
    }]
    };
    
    // Function to initialize the chart
    function initializeChart(type = 'bar') {
    if (chart) {
        chart.destroy(); // Destroy the existing chart
    }
    chart = new Chart(BarChart, {
        type: type,
        data: chartData,
        options: {
        scales: {
            y: {
            beginAtZero: true,
            max: 30,
            }
        }
        }
    });
    }
    
    // Initialize the chart for the first time
    let chart;
    initializeChart();
    
    // Add event listeners to the chart type buttons
    barChartBtn.addEventListener('click', () => {
    initializeChart('bar');
    });
    
    lineChartBtn.addEventListener('click', () => {
    initializeChart('line');
    });
    
    pieChartBtn.addEventListener('click', () => {
    initializeChart('doughnut');
    });
    
});